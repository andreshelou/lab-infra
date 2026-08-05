#!/usr/bin/env python3
"""Copy a limited real sample from source Elasticsearch to local lab Elasticsearch.

The source cluster is read-only from this script: it only uses _search and
_search/scroll. The target cluster receives _bulk writes.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROTECTED_SOURCE_CLUSTER_UUID = "0WP9AgGdTmKIpRPJRryFOw"
LOCAL_LAB_CLUSTER_NAME = "lab-es"


def request(method: str, base_url: str, path: str, payload: object | None = None, timeout: int = 120) -> object:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {error_body}") from exc
    return json.loads(text) if text.strip() else {}


def bulk(target: str, index: str, hits: list[dict[str, object]]) -> None:
    lines = []
    for hit in hits:
        action = {"index": {"_index": index}}
        if "_id" in hit:
            action["index"]["_id"] = hit["_id"]
        lines.append(json.dumps(action, separators=(",", ":")))
        lines.append(json.dumps(hit["_source"], separators=(",", ":"), default=str))
    if not lines:
        return
    data = ("\n".join(lines) + "\n").encode("utf-8")
    req = Request(
        f"{target.rstrip('/')}/_bulk",
        data=data,
        headers={"Content-Type": "application/x-ndjson", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"bulk write failed for {index}: {exc.code} {error_body}") from exc
    if result.get("errors"):
        failures = [item for item in result.get("items", []) if item.get("index", {}).get("error")]
        raise RuntimeError(f"bulk write had errors for {index}: {json.dumps(failures[:10], indent=2)}")


def clear_scroll(source: str, scroll_id: str) -> None:
    try:
        request("DELETE", source, "/_search/scroll", {"scroll_id": [scroll_id]}, timeout=60)
    except Exception:
        pass


def copy_index(source: str, target: str, index: str, max_docs: int, batch_size: int, sleep_seconds: float) -> int:
    query = {
        "size": batch_size,
        "sort": ["_doc"],
        "query": {"match_all": {}},
    }
    result = request("POST", source, f"/{index}/_search?scroll=2m", query)
    scroll_id = result.get("_scroll_id")
    copied = 0
    try:
        while True:
            hits = result.get("hits", {}).get("hits", [])
            if not hits or copied >= max_docs:
                break
            remaining = max_docs - copied
            selected = hits[:remaining]
            bulk(target, index, selected)
            copied += len(selected)
            print(f"{index}: copied {copied}/{max_docs}")
            if copied >= max_docs:
                break
            if sleep_seconds:
                time.sleep(sleep_seconds)
            result = request("POST", source, "/_search/scroll", {"scroll": "2m", "scroll_id": scroll_id})
            scroll_id = result.get("_scroll_id", scroll_id)
    finally:
        if scroll_id:
            clear_scroll(source, scroll_id)
    request("POST", target, f"/{index}/_refresh")
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy a real read-only sample from source ES to local lab ES")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", default="http://localhost:9200")
    parser.add_argument("--indices", nargs="+", required=True)
    parser.add_argument("--max-docs", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--output", default="./out-origin/reports/real-sample-summary.json")
    args = parser.parse_args()

    source_info = request("GET", args.source, "/")
    target_info = request("GET", args.target, "/")
    if source_info.get("cluster_uuid") != PROTECTED_SOURCE_CLUSTER_UUID:
        raise RuntimeError(f"Unexpected source cluster: {source_info}")
    if target_info.get("cluster_name") != LOCAL_LAB_CLUSTER_NAME:
        raise RuntimeError(f"Refusing to write to non-lab target cluster: {target_info}")

    summary = []
    for index in args.indices:
        copied = copy_index(args.source, args.target, index, args.max_docs, args.batch_size, args.sleep_seconds)
        count = request("GET", args.target, f"/{index}/_count").get("count", 0)
        summary.append({"index": index, "copied": copied, "target_count": count})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Summary written to {output}")


if __name__ == "__main__":
    main()
