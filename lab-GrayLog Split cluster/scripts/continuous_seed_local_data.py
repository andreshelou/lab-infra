#!/usr/bin/env python3
"""Continuously seed lab Elasticsearch/OpenSearch indices with synthetic documents."""

from __future__ import annotations

import argparse
import json
import random
import signal
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


STOP = False


def request(method: str, base_url: str, path: str, payload: object | None = None, timeout: int = 120) -> Any:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {error_body}") from exc
    return json.loads(text) if text.strip() else {}


def es_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]


def graylog_doc(index: str, cycle: int, seq: int, now: datetime) -> dict[str, object]:
    ts = es_date(now)
    message_id = f"continuous-{index}-{cycle}-{seq}-{uuid.uuid4().hex[:8]}"
    return {
        "timestamp": ts,
        "gl2_receive_timestamp": ts,
        "gl2_processing_timestamp": ts,
        "gl2_message_id": message_id,
        "gl2_source_node": "continuous-lab-node",
        "gl2_source_input": "continuous-synthetic-input",
        "gl2_accounted_message_size": random.randint(180, 480),
        "gl2_processing_duration_ms": random.randint(1, 30),
        "source": f"continuous-{index}",
        "message": f"Continuous synthetic message cycle={cycle} seq={seq} index={index}",
        "full_message": f"Continuous synthetic full message for migration lab. index={index} cycle={cycle} seq={seq}",
        "streams": ["000000000000000000000001"],
        "level": random.choice([3, 4, 5, 6]),
        "facility": "continuous-lab",
        "application": "migration-continuous-test",
        "environment": "local",
        "version": "continuous-synthetic",
    }


def event_doc(index: str, cycle: int, seq: int, now: datetime) -> dict[str, object]:
    ts = es_date(now)
    event_id = f"continuous-event-{index}-{cycle}-{seq}-{uuid.uuid4().hex[:8]}"
    return {
        "id": event_id,
        "timestamp": ts,
        "timestamp_processing": ts,
        "timerange_start": ts,
        "timerange_end": ts,
        "event_definition_id": "continuous-synthetic-definition",
        "event_definition_type": "aggregation-v1",
        "origin_context": "continuous-synthetic",
        "message": f"Continuous synthetic Graylog event cycle={cycle} seq={seq} index={index}",
        "source": f"continuous-{index}",
        "key": f"continuous-key-{cycle}-{seq}",
        "key_tuple": f"continuous-key-tuple-{cycle}-{seq}",
        "priority": random.randint(1, 3),
        "alert": False,
        "streams": ["000000000000000000000001"],
        "source_streams": ["000000000000000000000001"],
        "triggered_jobs": [],
        "fields": {
            "environment": "local",
            "generator": "continuous-seed-local-data",
            "index": index,
        },
    }


def build_doc(index: str, cycle: int, seq: int, now: datetime) -> dict[str, object]:
    if index.startswith("gl-events_") or index.startswith("gl-system-events_"):
        return event_doc(index, cycle, seq, now)
    return graylog_doc(index, cycle, seq, now)


def mapping_properties(base_url: str, index: str) -> dict[str, object]:
    mapping = request("GET", base_url, f"/{index}/_mapping")
    return mapping.get(index, {}).get("mappings", {}).get("properties", {})


def filter_to_mapping(doc: dict[str, object], properties: dict[str, object]) -> dict[str, object]:
    filtered = {}
    for key, value in doc.items():
        mapping = properties.get(key)
        if not isinstance(mapping, dict):
            continue
        if isinstance(value, dict) and (
            mapping.get("type") == "object" or "properties" in mapping or "dynamic" in mapping
        ):
            continue
        filtered[key] = value
    return filtered


def bulk_insert(base_url: str, index: str, docs: list[dict[str, object]]) -> int:
    if not docs:
        return 0
    lines = []
    for doc in docs:
        lines.append(json.dumps({"index": {"_index": index}}, separators=(",", ":")))
        lines.append(json.dumps(doc, separators=(",", ":")))
    body = "\n".join(lines) + "\n"
    req = Request(
        f"{base_url.rstrip('/')}/_bulk",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/x-ndjson"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"bulk insert failed for {index}: {exc.code} {error_body}") from exc
    if result.get("errors"):
        failures = [item for item in result.get("items", []) if item.get("index", {}).get("error")]
        raise RuntimeError(f"bulk insert had errors for {index}: {json.dumps(failures[:5], indent=2)}")
    return len(docs)


def load_indices(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    indices = []
    for item in data:
        if isinstance(item, str):
            indices.append(item)
        else:
            indices.append(item["index"])
    return indices


def handle_stop(signum: int, frame: object) -> None:
    global STOP
    STOP = True


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuously seed lab indices with synthetic data")
    parser.add_argument("--target", default="http://localhost:9200")
    parser.add_argument("--indices", default="./out-poc-current/discovery/indices.json")
    parser.add_argument("--docs-per-index", type=int, default=1)
    parser.add_argument("--interval-seconds", type=float, default=10.0)
    parser.add_argument("--cycles", type=int, default=0, help="0 means run until interrupted")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--allow-cluster", action="append", default=["lab-es", "lab-os"])
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    info = request("GET", args.target, "/")
    cluster_name = info.get("cluster_name")
    if cluster_name not in set(args.allow_cluster):
        raise RuntimeError(f"Refusing to seed cluster {cluster_name!r}. Allowed: {args.allow_cluster}")

    indices = load_indices(Path(args.indices))
    properties_by_index = {index: mapping_properties(args.target, index) for index in indices}
    print(
        json.dumps(
            {
                "target": args.target,
                "cluster_name": cluster_name,
                "indices": len(indices),
                "docs_per_index": args.docs_per_index,
                "interval_seconds": args.interval_seconds,
                "cycles": args.cycles or "until interrupted",
            },
            indent=2,
            sort_keys=True,
        )
    )

    cycle = 0
    while not STOP:
        cycle += 1
        now = datetime.now(timezone.utc)
        inserted_total = 0
        for index in indices:
            docs = [
                filter_to_mapping(build_doc(index, cycle, seq + 1, now), properties_by_index[index])
                for seq in range(args.docs_per_index)
            ]
            docs = [doc for doc in docs if doc]
            inserted_total += bulk_insert(args.target, index, docs)
            if args.refresh:
                request("POST", args.target, f"/{index}/_refresh", timeout=60)
        print(f"cycle={cycle} inserted={inserted_total} timestamp={es_date(now)}")
        if args.cycles and cycle >= args.cycles:
            break
        time.sleep(args.interval_seconds)

    print(f"stopped cycles={cycle}")


if __name__ == "__main__":
    main()
