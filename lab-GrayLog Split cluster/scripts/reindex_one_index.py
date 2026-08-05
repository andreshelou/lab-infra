#!/usr/bin/env python3
"""Remote reindex a single index and report elapsed time."""

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

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, payload)


def assert_not_protected_source_target(client: RestClient) -> None:
    info = client.get("/")
    cluster_name = info.get("cluster_name")
    cluster_uuid = info.get("cluster_uuid")
    if cluster_name in PROTECTED_SOURCE_CLUSTER_NAMES or cluster_uuid in PROTECTED_SOURCE_CLUSTER_UUIDS:
        raise RuntimeError(
            "Refusing to write to protected source cluster: "
            f"cluster_name={cluster_name!r}, cluster_uuid={cluster_uuid!r}. "
            "Use the OpenSearch endpoint as --target."
        )


def encoded_index(index: str) -> str:
    return urllib.parse.quote(index, safe="")


def count_docs(client: RestClient, index: str) -> int:
    result = client.get(f"/{encoded_index(index)}/_count")
    return int(result.get("count", 0))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def task_path(task_id: str) -> str:
    return "/_tasks/" + urllib.parse.quote(task_id, safe=":")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remote reindex one index and measure elapsed time")
    parser.add_argument("--source", required=True, help="Source Elasticsearch URL, for example http://ptyesnp01:9200")
    parser.add_argument("--target", required=True, help="Target OpenSearch URL, for example http://ptyesnp01:19200")
    parser.add_argument("--index", required=True, help="Index name to reindex")
    parser.add_argument("--output", default="./out-one-index-reindex", help="Directory for the JSON report")
    parser.add_argument("--batch-size", type=int, default=1000, help="Remote reindex source batch size")
    parser.add_argument("--requests-per-second", type=float, default=None, help="Throttle reindex requests per second")
    parser.add_argument("--wait-interval", type=float, default=5.0, help="Seconds between task polling checks")
    parser.add_argument("--refresh", action="store_true", help="Refresh target index after completion")
    parser.add_argument("--conflicts", choices=["abort", "proceed"], default="abort", help="Conflict handling for _reindex")
    parser.add_argument("--execute", action="store_true", help="Actually submit the reindex task")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = RestClient(args.source)
    target = RestClient(args.target, timeout=180)

    source_info = source.get("/")
    target_info = target.get("/")

    payload: dict[str, Any] = {
        "source": {
            "remote": {"host": args.source.rstrip("/")},
            "index": args.index,
            "size": args.batch_size,
        },
        "dest": {"index": args.index},
        "conflicts": args.conflicts,
    }

    query_params = {"wait_for_completion": "false"}
    if args.requests_per_second is not None:
        query_params["requests_per_second"] = str(args.requests_per_second)
    query = urllib.parse.urlencode(query_params)

    if not args.execute:
        print(json.dumps({"dry_run": True, "target": args.target, "path": f"/_reindex?{query}", "payload": payload}, indent=2))
        return

    assert_not_protected_source_target(target)

    source_count_before = count_docs(source, args.index)
    target_count_before = count_docs(target, args.index)

    started_at_epoch = time.time()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at_epoch))
    started = time.monotonic()

    print(f"Submitting remote reindex for index={args.index}")
    print(f"Source count before: {source_count_before}")
    print(f"Target count before: {target_count_before}")

    submit_result = target.post(f"/_reindex?{query}", payload)
    task_id = submit_result.get("task")
    if not task_id:
        raise RuntimeError(f"Reindex did not return a task id: {submit_result}")

    print(f"Task: {task_id}")

    task_result: dict[str, Any] = {}
    while True:
        task_result = target.get(task_path(task_id))
        elapsed = time.monotonic() - started
        task = task_result.get("task", {})
        status = task.get("status", {})
        total = status.get("total", 0)
        created = status.get("created", 0)
        updated = status.get("updated", 0)
        version_conflicts = status.get("version_conflicts", 0)
        print(
            f"elapsed={elapsed:.1f}s total={total} created={created} "
            f"updated={updated} version_conflicts={version_conflicts}"
        )
        if task_result.get("completed"):
            break
        time.sleep(args.wait_interval)

    if args.refresh:
        target.post(f"/{encoded_index(args.index)}/_refresh")

    elapsed_seconds = time.monotonic() - started
    target_count_after = count_docs(target, args.index)
    source_count_after = count_docs(source, args.index)
    completed_at_epoch = time.time()
    completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(completed_at_epoch))

    response = task_result.get("response", {})
    error = task_result.get("error")
    failures = response.get("failures", []) if isinstance(response, dict) else []

    report = {
        "index": args.index,
        "source": {"url": args.source, "cluster": source_info, "count_before": source_count_before, "count_after": source_count_after},
        "target": {"url": args.target, "cluster": target_info, "count_before": target_count_before, "count_after": target_count_after},
        "request": {"path": f"/_reindex?{query}", "payload": payload},
        "task_id": task_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "elapsed_minutes": round(elapsed_seconds / 60, 3),
        "response": response,
        "error": error,
        "failures_count": len(failures),
        "counts_match_after": source_count_after == target_count_after,
    }

    report_name = f"reindex-one-{args.index}-{int(started_at_epoch)}.json".replace("/", "_")
    report_path = Path(args.output) / "reports" / report_name
    write_json(report_path, report)

    print("\nSummary")
    print(f"Index: {args.index}")
    print(f"Elapsed seconds: {elapsed_seconds:.3f}")
    print(f"Elapsed minutes: {elapsed_seconds / 60:.3f}")
    print(f"Source count after: {source_count_after}")
    print(f"Target count after: {target_count_after}")
    print(f"Counts match after: {source_count_after == target_count_after}")
    print(f"Failures: {len(failures)}")
    print(f"Report: {report_path}")

    if error or failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
