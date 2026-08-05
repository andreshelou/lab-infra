#!/usr/bin/env python3
"""Reset one target index by deleting and recreating it from a clean payload."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROTECTED_SOURCE_CLUSTER_NAMES = {"elasticsearch-nonprod"}
PROTECTED_SOURCE_CLUSTER_UUIDS = {"0WP9AgGdTmKIpRPJRryFOw"}


class RestClient:
    def __init__(self, base_url: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {url} failed: {exc.code} {error_body}") from exc
        return json.loads(response_body) if response_body.strip() else {}

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def put(self, path: str, payload: dict[str, Any]) -> Any:
        return self.request("PUT", path, payload)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, payload)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)


def encoded_index(index: str) -> str:
    return urllib.parse.quote(index, safe="")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_not_protected_source_target(client: RestClient) -> dict[str, Any]:
    info = client.get("/")
    cluster_name = info.get("cluster_name")
    cluster_uuid = info.get("cluster_uuid")
    if cluster_name in PROTECTED_SOURCE_CLUSTER_NAMES or cluster_uuid in PROTECTED_SOURCE_CLUSTER_UUIDS:
        raise RuntimeError(
            "Refusing to write to protected source cluster: "
            f"cluster_name={cluster_name!r}, cluster_uuid={cluster_uuid!r}. "
            "Use the OpenSearch endpoint as --target."
        )
    return info


def index_exists(client: RestClient, index: str) -> bool:
    try:
        client.get(f"/{encoded_index(index)}")
        return True
    except RuntimeError as exc:
        if " 404 " in str(exc) or "index_not_found_exception" in str(exc):
            return False
        raise


def count_docs(client: RestClient, index: str) -> int | None:
    if not index_exists(client, index):
        return None
    result = client.get(f"/{encoded_index(index)}/_count")
    return int(result.get("count", 0))


def get_aliases(client: RestClient, index: str) -> dict[str, Any]:
    if not index_exists(client, index):
        return {}
    try:
        result = client.get(f"/{encoded_index(index)}/_alias")
    except RuntimeError as exc:
        if " 404 " in str(exc):
            return {}
        raise
    return result.get(index, {}).get("aliases", {})


def mappings_equal(client: RestClient, index: str, payload: dict[str, Any]) -> bool:
    actual = client.get(f"/{encoded_index(index)}/_mapping").get(index, {}).get("mappings", {})
    return actual == payload.get("mappings", {})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset one target index from a clean create payload")
    parser.add_argument("--target", required=True, help="Target OpenSearch URL")
    parser.add_argument("--index", required=True, help="Index to reset")
    parser.add_argument("--payloads", required=True, help="Directory containing <index>.create.json")
    parser.add_argument("--output", default="./out-reset-index", help="Directory for reset reports")
    parser.add_argument("--preserve-aliases", action="store_true", help="Reapply aliases that existed before deleting the index")
    parser.add_argument("--force", action="store_true", help="Required when resetting an index that currently has aliases")
    parser.add_argument("--refresh", action="store_true", help="Refresh index after recreation")
    parser.add_argument("--execute", action="store_true", help="Actually delete and recreate the index")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = RestClient(args.target)
    cluster = assert_not_protected_source_target(target)
    payload_path = Path(args.payloads) / f"{args.index}.create.json"
    if not payload_path.exists():
        raise RuntimeError(f"Payload not found: {payload_path}")
    payload = read_json(payload_path)

    exists_before = index_exists(target, args.index)
    count_before = count_docs(target, args.index)
    aliases_before = get_aliases(target, args.index)
    has_aliases = bool(aliases_before)

    plan = {
        "target": args.target,
        "cluster": cluster,
        "index": args.index,
        "payload": str(payload_path),
        "exists_before": exists_before,
        "count_before": count_before,
        "aliases_before": aliases_before,
        "preserve_aliases": args.preserve_aliases,
        "force": args.force,
        "actions": ["delete index if exists", "create index from payload"],
    }
    if args.preserve_aliases:
        plan["actions"].append("reapply aliases captured before delete")

    if has_aliases and (not args.force or not args.preserve_aliases):
        print(json.dumps({**plan, "blocked": True, "reason": "index has aliases; use --force --preserve-aliases to reset safely"}, indent=2, sort_keys=True))
        sys.exit(1)

    if not args.execute:
        print(json.dumps({**plan, "dry_run": True}, indent=2, sort_keys=True))
        return

    started = time.monotonic()
    if exists_before:
        target.delete(f"/{encoded_index(args.index)}")
    target.put(f"/{encoded_index(args.index)}", payload)
    if args.preserve_aliases and aliases_before:
        actions = [{"add": {"index": args.index, "alias": alias, **alias_body}} for alias, alias_body in aliases_before.items()]
        target.post("/_aliases", {"actions": actions})
    if args.refresh:
        target.post(f"/{encoded_index(args.index)}/_refresh")

    count_after = count_docs(target, args.index)
    aliases_after = get_aliases(target, args.index)
    mapping_matches_payload = mappings_equal(target, args.index, payload)
    elapsed = time.monotonic() - started
    report = {
        **plan,
        "executed": True,
        "elapsed_seconds": round(elapsed, 3),
        "count_after": count_after,
        "aliases_after": aliases_after,
        "mapping_matches_payload": mapping_matches_payload,
    }
    report_path = Path(args.output) / "reports" / f"reset-{args.index}-{int(time.time())}.json"
    write_json(report_path, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Report: {report_path}")
    if count_after != 0 or not mapping_matches_payload:
        sys.exit(1)


if __name__ == "__main__":
    main()
