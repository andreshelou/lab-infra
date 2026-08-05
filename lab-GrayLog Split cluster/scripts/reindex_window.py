#!/usr/bin/env python3
"""Remote reindex indices using a timestamp window and report timings."""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
import urllib.parse
from datetime import datetime
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


def task_path(task_id: str) -> str:
    return "/_tasks/" + urllib.parse.quote(task_id, safe=":")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_indices(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError(f"Expected a JSON list in {path}")
    result = []
    for item in data:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and "index" in item:
            result.append(str(item["index"]))
        else:
            raise RuntimeError(f"Invalid index item in {path}: {item!r}")
    return result


def normalize_bound(value: str | None, now_value: str) -> str | None:
    if value is None:
        return None
    if value.lower() == "now":
        return now_value
    return value


def build_range(args: argparse.Namespace, now_value: str) -> dict[str, str]:
    result = {}
    for key in ("gt", "gte", "lt", "lte"):
        value = normalize_bound(getattr(args, key), now_value)
        if value is not None:
            result[key] = value
    if not result:
        raise RuntimeError("At least one date bound is required: --gt, --gte, --lt, or --lte")
    return result


def mapping_has_field(client: RestClient, index: str, field: str) -> bool:
    mapping = client.get(f"/{encoded_index(index)}/_mapping")
    properties = mapping.get(index, {}).get("mappings", {}).get("properties", {})
    cursor: Any = properties
    parts = field.split(".")
    for pos, part in enumerate(parts):
        if not isinstance(cursor, dict) or part not in cursor:
            return False
        field_mapping = cursor[part]
        if pos == len(parts) - 1:
            return isinstance(field_mapping, dict)
        cursor = field_mapping.get("properties", {}) if isinstance(field_mapping, dict) else {}
    return False


def build_query(timestamp_field: str, range_bounds: dict[str, str]) -> dict[str, Any]:
    return {"range": {timestamp_field: range_bounds}}


def count_docs(client: RestClient, index: str, query_body: dict[str, Any] | None) -> int:
    payload = {"query": query_body} if query_body else None
    result = client.request("GET", f"/{encoded_index(index)}/_count", payload)
    return int(result.get("count", 0))


def reindex_index(args: argparse.Namespace, index: str, range_bounds: dict[str, str], now_value: str) -> dict[str, Any]:
    source = RestClient(args.source)
    target = RestClient(args.target, timeout=180)
    started_monotonic = time.monotonic()
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    has_timestamp = mapping_has_field(source, index, args.timestamp_field)
    if has_timestamp:
        query_body: dict[str, Any] | None = build_query(args.timestamp_field, range_bounds)
        mode = "window"
    elif args.no_date_policy == "skip":
        return {
            "index": index,
            "mode": "skipped_no_timestamp",
            "timestamp_field": args.timestamp_field,
            "elapsed_seconds": 0,
            "counts_match_after": None,
        }
    elif args.no_date_policy == "fail":
        raise RuntimeError(f"Index {index} does not have timestamp field {args.timestamp_field!r}")
    else:
        query_body = None
        mode = "full_no_timestamp"

    source_count_before = count_docs(source, index, query_body)
    target_count_before = count_docs(target, index, query_body)
    payload: dict[str, Any] = {
        "source": {"remote": {"host": args.source.rstrip("/")}, "index": index, "size": args.batch_size},
        "dest": {"index": index},
        "conflicts": args.conflicts,
    }
    if query_body:
        payload["source"]["query"] = query_body

    query_params = {"wait_for_completion": "false"}
    if args.requests_per_second is not None:
        query_params["requests_per_second"] = str(args.requests_per_second)
    query = urllib.parse.urlencode(query_params)

    submit_result = target.post(f"/_reindex?{query}", payload)
    task_id = submit_result.get("task")
    if not task_id:
        raise RuntimeError(f"Reindex did not return a task id for {index}: {submit_result}")

    task_result: dict[str, Any] = {}
    if args.wait:
        while True:
            task_result = target.get(task_path(task_id))
            if task_result.get("completed"):
                break
            time.sleep(args.wait_interval)

    if args.refresh and args.wait:
        target.post(f"/{encoded_index(index)}/_refresh")

    elapsed_seconds = time.monotonic() - started_monotonic
    source_count_after = count_docs(source, index, query_body)
    target_count_after = count_docs(target, index, query_body)
    response = task_result.get("response", {}) if task_result else {}
    failures = response.get("failures", []) if isinstance(response, dict) else []

    return {
        "index": index,
        "mode": mode,
        "timestamp_field": args.timestamp_field,
        "range": range_bounds if has_timestamp else None,
        "now_resolved_at_start": now_value,
        "source_count_before": source_count_before,
        "target_count_before": target_count_before,
        "source_count_after": source_count_after,
        "target_count_after": target_count_after,
        "counts_match_after": source_count_after == target_count_after,
        "task_id": task_id,
        "task_result": task_result,
        "failures_count": len(failures),
        "started_at": started_at,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "elapsed_minutes": round(elapsed_seconds / 60, 3),
    }


def worker(args: argparse.Namespace, work: queue.Queue[str], results: list[dict[str, Any]], lock: threading.Lock, range_bounds: dict[str, str], now_value: str) -> None:
    while True:
        try:
            index = work.get_nowait()
        except queue.Empty:
            return
        try:
            print(f"Reindexing {index}")
            result = reindex_index(args, index, range_bounds, now_value)
            print(f"Finished {index}: mode={result['mode']} elapsed={result['elapsed_seconds']}s match={result['counts_match_after']}")
        except Exception as exc:
            result = {"index": index, "mode": "error", "error": str(exc), "counts_match_after": False}
            print(f"ERROR {index}: {exc}", file=sys.stderr)
        with lock:
            results.append(result)
        work.task_done()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remote reindex indices by timestamp window")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--indices", required=True)
    parser.add_argument("--timestamp-field", default="timestamp")
    parser.add_argument("--gt")
    parser.add_argument("--gte")
    parser.add_argument("--lt")
    parser.add_argument("--lte")
    parser.add_argument("--output", default="./out-window-reindex")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--requests-per-second", type=float, default=None)
    parser.add_argument("--max-parallel", type=int, default=1)
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--wait-interval", type=float, default=10.0)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--conflicts", choices=["abort", "proceed"], default="proceed")
    parser.add_argument("--no-date-policy", choices=["skip", "full", "fail"], default="skip")
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    now_value = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
    range_bounds = build_range(args, now_value)
    indices = load_indices(Path(args.indices))

    if not args.execute:
        print(json.dumps({
            "dry_run": True,
            "source": args.source,
            "target": args.target,
            "indices_count": len(indices),
            "timestamp_field": args.timestamp_field,
            "range": range_bounds,
            "no_date_policy": args.no_date_policy,
            "max_parallel": args.max_parallel,
        }, indent=2, sort_keys=True))
        return

    assert_not_protected_source_target(RestClient(args.target))

    work: queue.Queue[str] = queue.Queue()
    for index in indices:
        work.put(index)
    results: list[dict[str, Any]] = []
    lock = threading.Lock()
    threads = [threading.Thread(target=worker, args=(args, work, results, lock, range_bounds, now_value)) for _ in range(max(1, args.max_parallel))]
    started = time.monotonic()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed = time.monotonic() - started

    summary = {
        "source": args.source,
        "target": args.target,
        "timestamp_field": args.timestamp_field,
        "range": range_bounds,
        "now_resolved_at_start": now_value,
        "indices_count": len(indices),
        "elapsed_seconds": round(elapsed, 3),
        "elapsed_minutes": round(elapsed / 60, 3),
        "results": sorted(results, key=lambda item: item.get("index", "")),
        "errors": [item for item in results if item.get("mode") == "error"],
        "mismatches": [item for item in results if item.get("counts_match_after") is False],
    }
    output = Path(args.output) / "reports" / f"window-reindex-{int(time.time())}.json"
    write_json(output, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2, sort_keys=True))
    print(f"Report: {output}")
    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
