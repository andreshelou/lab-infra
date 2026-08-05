#!/usr/bin/env python3
"""Seed local lab Elasticsearch indices with synthetic documents."""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request(method: str, base_url: str, path: str, payload: object | None = None) -> object:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=60) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: {exc.code} {error_body}") from exc
    return json.loads(text) if text.strip() else {}


def es_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]


def graylog_doc(index: str, seq: int, now: datetime) -> dict[str, object]:
    ts = es_date(now - timedelta(seconds=seq * 15))
    message_id = f"synthetic-{index}-{seq}-{uuid.uuid4().hex[:8]}"
    return {
        "timestamp": ts,
        "gl2_receive_timestamp": ts,
        "gl2_processing_timestamp": ts,
        "gl2_message_id": message_id,
        "gl2_source_node": "lab-graylog-node",
        "gl2_source_input": "synthetic-input",
        "gl2_accounted_message_size": 256 + seq,
        "gl2_processing_duration_ms": random.randint(1, 25),
        "source": "lab-generator",
        "message": f"Synthetic message {seq} for {index}",
        "full_message": f"Synthetic full message generated for migration lab index {index}, document {seq}",
        "streams": ["000000000000000000000001"],
        "level": random.choice([3, 4, 5, 6]),
        "facility": "lab",
        "application": "migration-test",
        "environment": "local",
        "version": "synthetic",
    }


def event_doc(index: str, seq: int, now: datetime) -> dict[str, object]:
    ts = es_date(now - timedelta(seconds=seq * 15))
    event_id = f"synthetic-event-{index}-{seq}-{uuid.uuid4().hex[:8]}"
    return {
        "id": event_id,
        "timestamp": ts,
        "timestamp_processing": ts,
        "timerange_start": ts,
        "timerange_end": ts,
        "event_definition_id": "synthetic-definition",
        "event_definition_type": "aggregation-v1",
        "origin_context": "synthetic",
        "message": f"Synthetic Graylog event {seq} for {index}",
        "source": "lab-generator",
        "key": f"synthetic-key-{seq}",
        "key_tuple": f"synthetic-key-tuple-{seq}",
        "priority": random.randint(1, 3),
        "alert": False,
        "streams": ["000000000000000000000001"],
        "source_streams": ["000000000000000000000001"],
        "triggered_jobs": [],
        "fields": {
            "environment": "local",
            "generator": "es2os-lab",
            "index": index,
        },
        "group_by_fields": {
            "source": "lab-generator",
        },
        "scores": {
            "score": float(seq),
        },
    }


def build_doc(index: str, seq: int, now: datetime) -> dict[str, object]:
    if index.startswith("gl-events_") or index.startswith("gl-system-events_"):
        return event_doc(index, seq, now)
    return graylog_doc(index, seq, now)


def mapping_properties(base_url: str, index: str) -> dict[str, object]:
    mapping = request("GET", base_url, f"/{index}/_mapping")
    properties = mapping.get(index, {}).get("mappings", {}).get("properties", {})
    return properties


def filter_to_mapping(doc: dict[str, object], properties: dict[str, object]) -> dict[str, object]:
    # Some migrated Graylog indices are already at index.mapping.total_fields.limit.
    # Keep only mapped top-level fields to avoid creating new fields while seeding.
    filtered = {}
    for key, value in doc.items():
        mapping = properties.get(key)
        if not isinstance(mapping, dict):
            continue
        # Avoid adding subfields under dynamic object mappings. This keeps the
        # lab mapping identical to the captured source mapping.
        if isinstance(value, dict) and (
            mapping.get("type") == "object" or "properties" in mapping or "dynamic" in mapping
        ):
            continue
        filtered[key] = value
    return filtered


def bulk_insert(base_url: str, index: str, docs: list[dict[str, object]]) -> None:
    lines = []
    for doc in docs:
        lines.append(json.dumps({"index": {"_index": index}}, separators=(",", ":")))
        lines.append(json.dumps(doc, separators=(",", ":")))
    body = ("\n".join(lines) + "\n").encode("utf-8")
    req = Request(
        f"{base_url.rstrip('/')}/_bulk",
        data=body,
        headers={"Content-Type": "application/x-ndjson"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"bulk insert failed for {index}: {exc.code} {error_body}") from exc
    if result.get("errors"):
        failures = [item for item in result.get("items", []) if item.get("index", {}).get("error")]
        raise RuntimeError(f"bulk insert had errors for {index}: {json.dumps(failures[:5], indent=2)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed local lab indices with synthetic data")
    parser.add_argument("--target", default="http://localhost:9200")
    parser.add_argument("--indices", default="./out-origin/discovery/indices.json")
    parser.add_argument("--docs-per-index", type=int, default=5)
    args = parser.parse_args()

    info = request("GET", args.target, "/")
    if info.get("cluster_name") != "lab-es":
        raise RuntimeError(f"Refusing to seed non-lab cluster: {info}")

    indices = json.loads(Path(args.indices).read_text(encoding="utf-8"))
    now = datetime.now()
    for item in indices:
        index = item["index"]
        current_count = request("GET", args.target, f"/{index}/_count").get("count", 0)
        docs_to_add = max(0, args.docs_per_index - int(current_count))
        if docs_to_add == 0:
            print(f"Skipped {index}: count={current_count}")
            continue
        properties = mapping_properties(args.target, index)
        docs = [
            filter_to_mapping(build_doc(index, seq + 1, now), properties)
            for seq in range(docs_to_add)
        ]
        docs = [doc for doc in docs if doc]
        if not docs:
            print(f"Skipped {index}: no compatible mapped fields found")
            continue
        bulk_insert(args.target, index, docs)
        request("POST", args.target, f"/{index}/_refresh")
        count = request("GET", args.target, f"/{index}/_count").get("count")
        print(f"Seeded {index}: count={count}")


if __name__ == "__main__":
    main()
