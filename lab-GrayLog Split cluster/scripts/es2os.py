#!/usr/bin/env python3
"""Elasticsearch 7.17 to OpenSearch migration helper.

Default commands are read-only or dry-run. Any command that writes to
OpenSearch requires --execute.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen


FORBIDDEN_SETTING_PATHS = [
    ("uuid",),
    ("creation_date",),
    ("creation_date_string",),
    ("provided_name",),
    ("version",),
    ("routing", "allocation", "include", "_tier_preference"),
    ("blocks",),
    ("lifecycle",),
]

ALLOWED_INDEX_SETTINGS = {
    "number_of_shards",
    "number_of_replicas",
    "refresh_interval",
    "analysis",
}

FORBIDDEN_PAYLOAD_KEYS = {
    "uuid",
    "creation_date",
    "creation_date_string",
    "provided_name",
    "version",
    "lifecycle",
    "blocks",
    "_tier_preference",
}

FORBIDDEN_PAYLOAD_SETTING_PATHS = [
    ("settings", "index", "uuid"),
    ("settings", "index", "creation_date"),
    ("settings", "index", "creation_date_string"),
    ("settings", "index", "provided_name"),
    ("settings", "index", "version"),
    ("settings", "index", "routing", "allocation", "include", "_tier_preference"),
    ("settings", "index", "blocks"),
    ("settings", "index", "lifecycle"),
]

PROTECTED_SOURCE_CLUSTER_NAMES = {"elasticsearch-nonprod"}
PROTECTED_SOURCE_CLUSTER_UUIDS = {"0WP9AgGdTmKIpRPJRryFOw"}


class RestClient:
    def __init__(self, base_url: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Any:
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
        if response_body.strip():
            return json.loads(response_body)
        return {}

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def put(self, path: str, payload: Dict[str, Any]) -> Any:
        return self.request("PUT", path, payload)

    def post(self, path: str, payload: Dict[str, Any]) -> Any:
        return self.request("POST", path, payload)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)


def assert_not_protected_source_target(client: RestClient) -> None:
    """Refuse write operations if target is the known source cluster."""
    info = client.get("/")
    cluster_name = info.get("cluster_name")
    cluster_uuid = info.get("cluster_uuid")
    if cluster_name in PROTECTED_SOURCE_CLUSTER_NAMES or cluster_uuid in PROTECTED_SOURCE_CLUSTER_UUIDS:
        raise RuntimeError(
            "Refusing to write to protected source cluster: "
            f"cluster_name={cluster_name!r}, cluster_uuid={cluster_uuid!r}. "
            "Use a lab OpenSearch/Elasticsearch endpoint as --target."
        )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def is_internal_index(index: str) -> bool:
    return index.startswith(".")


def remove_path(obj: Dict[str, Any], path: Tuple[str, ...]) -> bool:
    cursor: Any = obj
    for part in path[:-1]:
        if not isinstance(cursor, dict) or part not in cursor:
            return False
        cursor = cursor[part]
    if isinstance(cursor, dict) and path[-1] in cursor:
        del cursor[path[-1]]
        return True
    return False


def prune_empty_dicts(obj: Any) -> Any:
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            obj[key] = prune_empty_dicts(obj[key])
            if obj[key] == {}:
                del obj[key]
    return obj


def flatten_paths(obj: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            yield from flatten_paths(value, next_prefix)
    else:
        yield prefix


def has_path(obj: Dict[str, Any], path: Tuple[str, ...]) -> bool:
    cursor: Any = obj
    for part in path:
        if not isinstance(cursor, dict) or part not in cursor:
            return False
        cursor = cursor[part]
    return True


def discover_indices(client: RestClient, exclude_internal: bool) -> List[Dict[str, Any]]:
    rows = client.get("/_cat/indices?format=json&h=index,status,docs.count,pri,rep")
    indices = []
    for row in rows:
        index = row["index"]
        if exclude_internal and is_internal_index(index):
            continue
        indices.append(
            {
                "index": index,
                "status": row.get("status"),
                "docs_count": int(row.get("docs.count") or 0),
                "primary_shards": int(row.get("pri") or 0),
                "replicas": int(row.get("rep") or 0),
            }
        )
    return sorted(indices, key=lambda item: item["index"])


def collect_index_metadata(client: RestClient, index: str) -> Dict[str, Any]:
    settings = client.get(f"/{index}/_settings?include_defaults=false")
    mappings = client.get(f"/{index}/_mapping")
    aliases = client.get(f"/{index}/_alias")
    count = client.get(f"/{index}/_count")
    shards = client.get(f"/_cat/shards/{index}?format=json")
    return {
        "index": index,
        "settings": settings[index].get("settings", {}),
        "mappings": mappings[index].get("mappings", {}),
        "aliases": aliases.get(index, {}).get("aliases", {}),
        "count": count.get("count", 0),
        "shards": shards,
    }


def transform_settings(settings: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    source_index_settings = json.loads(json.dumps(settings.get("index", {})))
    removed: List[str] = []
    warnings: List[str] = []

    for path in FORBIDDEN_SETTING_PATHS:
        if remove_path(source_index_settings, path):
            removed.append("index." + ".".join(path))

    if "routing" in source_index_settings:
        removed.append("index.routing")
        source_index_settings.pop("routing", None)

    kept_settings: Dict[str, Any] = {}
    for key in ALLOWED_INDEX_SETTINGS:
        if key in source_index_settings:
            kept_settings[key] = source_index_settings[key]

    for key in source_index_settings:
        if key not in ALLOWED_INDEX_SETTINGS:
            warnings.append(f"setting not copied automatically: index.{key}")

    prune_empty_dicts(kept_settings)
    return {"index": kept_settings} if kept_settings else {}, {"removed": removed, "warnings": warnings}


def build_payload(metadata: Dict[str, Any], aliases_mode: str, target_version: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    clean_settings, transform_info = transform_settings(metadata["settings"])
    payload: Dict[str, Any] = {}
    if clean_settings:
        payload["settings"] = clean_settings
    payload["mappings"] = metadata["mappings"]
    if aliases_mode == "inline" and metadata["aliases"]:
        payload["aliases"] = metadata["aliases"]

    report = {
        "index": metadata["index"],
        "source": {
            "docs_count": metadata["count"],
            "aliases": sorted(metadata["aliases"].keys()),
            "shards": metadata["shards"],
        },
        "target": {"engine": "opensearch", "version": target_version},
        "transformations": {
            "kept_settings": sorted(flatten_paths(clean_settings)),
            "removed_settings": transform_info["removed"],
            "deferred_aliases": sorted(metadata["aliases"].keys()) if aliases_mode == "separate" else [],
        },
        "warnings": transform_info["warnings"],
    }
    return payload, report


def command_discover(args: argparse.Namespace) -> None:
    client = RestClient(args.source)
    cluster = client.get("/")
    health = client.get("/_cluster/health")
    indices = discover_indices(client, args.exclude_internal)
    output = Path(args.output)
    write_json(output / "discovery" / "indices.json", indices)
    write_json(
        output / "reports" / "summary.json",
        {
            "source": {"url": args.source, "cluster": cluster, "health": health},
            "indices_count": len(indices),
            "indices": indices,
        },
    )
    print(f"Discovered {len(indices)} indices. Output: {output}")


def command_generate_payloads(args: argparse.Namespace) -> None:
    client = RestClient(args.source)
    output = Path(args.output)
    indices = discover_indices(client, args.exclude_internal)
    alias_plan = {"aliases": []}
    reports = []

    for item in indices:
        index = item["index"]
        metadata = collect_index_metadata(client, index)
        payload, report = build_payload(metadata, args.aliases_mode, args.target_version)
        write_json(output / "payloads" / f"{index}.create.json", payload)
        write_json(output / "reports" / f"{index}.report.json", report)
        reports.append(report)
        if args.aliases_mode == "separate":
            for alias in sorted(metadata["aliases"].keys()):
                alias_plan["aliases"].append(
                    {
                        "alias": alias,
                        "index": index,
                        "action": "add_after_reindex",
                        "reason": "Graylog deflector aliases should be applied after documents are migrated",
                    }
                )

    write_json(output / "discovery" / "indices.json", indices)
    write_json(output / "aliases" / "aliases-plan.json", alias_plan)
    write_json(
        output / "reports" / "summary.json",
        {
            "target": {"engine": "opensearch", "version": args.target_version},
            "indices_count": len(indices),
            "payloads_dir": str(output / "payloads"),
            "aliases_mode": args.aliases_mode,
            "warnings_count": sum(len(report["warnings"]) for report in reports),
            "reports": reports,
        },
    )
    print(f"Generated {len(indices)} payloads. Output: {output}")


def iter_payload_files(payloads_dir: Path) -> Iterable[Path]:
    return sorted(payloads_dir.glob("*.create.json"))


def command_scan_payloads(args: argparse.Namespace) -> None:
    payloads_dir = Path(args.payloads)
    failures = []
    for path in iter_payload_files(payloads_dir):
        payload = read_json(path)
        found = sorted(
            ".".join(setting_path)
            for setting_path in FORBIDDEN_PAYLOAD_SETTING_PATHS
            if has_path(payload, setting_path)
        )
        if found:
            failures.append({"file": str(path), "forbidden_setting_paths": found})
    if failures:
        write_json(Path("payload-scan-failures.json"), failures)
        print("Forbidden keys found. Details: payload-scan-failures.json", file=sys.stderr)
        sys.exit(1)
    print(f"Payload scan OK: {payloads_dir}")


def command_validate(args: argparse.Namespace) -> None:
    target = RestClient(args.target)
    payloads_dir = Path(args.payloads)
    files = list(iter_payload_files(payloads_dir))
    if not args.execute:
        print(f"Dry-run: would validate {len(files)} payloads against {args.target}")
        return

    assert_not_protected_source_target(target)

    for path in files:
        source_index = path.name.removesuffix(".create.json")
        temp_index = f"validate_{int(time.time())}_{source_index}".lower().replace(".", "_")
        payload = read_json(path)
        print(f"Validating {source_index} as temporary index {temp_index}")
        target.put(f"/{temp_index}", payload)
        target.delete(f"/{temp_index}")
    print(f"Validated {len(files)} payloads against {args.target}")


def command_create_indices(args: argparse.Namespace) -> None:
    target = RestClient(args.target)
    files = list(iter_payload_files(Path(args.payloads)))
    if not args.execute:
        print(f"Dry-run: would create {len(files)} indices on {args.target}")
        return

    assert_not_protected_source_target(target)

    for path in files:
        index = path.name.removesuffix(".create.json")
        print(f"Creating {index}")
        target.put(f"/{index}", read_json(path))
    print(f"Created {len(files)} indices")


def command_remote_reindex(args: argparse.Namespace) -> None:
    target = RestClient(args.target, timeout=120)
    indices = read_json(Path(args.indices))
    if not args.execute:
        print(f"Dry-run: would submit {len(indices)} remote reindex tasks to {args.target}")
        return

    assert_not_protected_source_target(target)

    tasks = []
    for item in indices:
        index = item["index"]
        payload = {
            "source": {"remote": {"host": args.source}, "index": index},
            "dest": {"index": index},
        }
        print(f"Submitting remote reindex for {index}")
        result = target.post("/_reindex?wait_for_completion=false", payload)
        tasks.append({"index": index, "task": result})
    write_json(Path(args.output) / "reports" / "reindex-tasks.json", tasks)
    print(f"Submitted {len(tasks)} reindex tasks")


def command_compare_counts(args: argparse.Namespace) -> None:
    source = RestClient(args.source)
    target = RestClient(args.target)
    indices = read_json(Path(args.indices))
    results = []
    for item in indices:
        index = item["index"]
        source_count = source.get(f"/{index}/_count").get("count", 0)
        target_count = target.get(f"/{index}/_count").get("count", 0)
        results.append(
            {
                "index": index,
                "source_count": source_count,
                "target_count": target_count,
                "match": source_count == target_count,
            }
        )
    write_json(Path(args.output) / "reports" / "count-comparison.json", results)
    mismatches = [row for row in results if not row["match"]]
    print(f"Compared {len(results)} indices. Mismatches: {len(mismatches)}")
    if mismatches:
        sys.exit(1)


def command_apply_aliases(args: argparse.Namespace) -> None:
    target = RestClient(args.target)
    plan = read_json(Path(args.aliases_plan))
    actions = [{"add": {"index": item["index"], "alias": item["alias"]}} for item in plan.get("aliases", [])]
    payload = {"actions": actions}
    if not args.execute:
        print(json.dumps(payload, indent=2, sort_keys=True))
        print(f"Dry-run: would apply {len(actions)} alias actions to {args.target}")
        return
    assert_not_protected_source_target(target)
    result = target.post("/_aliases", payload)
    print(json.dumps(result, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ES 7.17 to OpenSearch migration helper")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover")
    discover.add_argument("--source", required=True)
    discover.add_argument("--output", default="./out")
    discover.add_argument("--exclude-internal", action="store_true")
    discover.set_defaults(func=command_discover)

    generate = sub.add_parser("generate-payloads")
    generate.add_argument("--source", required=True)
    generate.add_argument("--target-version", default="2.15")
    generate.add_argument("--output", default="./out")
    generate.add_argument("--exclude-internal", action="store_true")
    generate.add_argument("--aliases-mode", choices=["separate", "inline", "none"], default="separate")
    generate.set_defaults(func=command_generate_payloads)

    scan = sub.add_parser("scan-payloads")
    scan.add_argument("--payloads", required=True)
    scan.set_defaults(func=command_scan_payloads)

    validate = sub.add_parser("validate")
    validate.add_argument("--target", required=True)
    validate.add_argument("--payloads", required=True)
    validate.add_argument("--execute", action="store_true")
    validate.set_defaults(func=command_validate)

    create = sub.add_parser("create-indices")
    create.add_argument("--target", required=True)
    create.add_argument("--payloads", required=True)
    create.add_argument("--execute", action="store_true")
    create.set_defaults(func=command_create_indices)

    reindex = sub.add_parser("remote-reindex")
    reindex.add_argument("--source", required=True)
    reindex.add_argument("--target", required=True)
    reindex.add_argument("--indices", required=True)
    reindex.add_argument("--output", default="./out")
    reindex.add_argument("--execute", action="store_true")
    reindex.set_defaults(func=command_remote_reindex)

    compare = sub.add_parser("compare-counts")
    compare.add_argument("--source", required=True)
    compare.add_argument("--target", required=True)
    compare.add_argument("--indices", required=True)
    compare.add_argument("--output", default="./out")
    compare.set_defaults(func=command_compare_counts)

    aliases = sub.add_parser("apply-aliases")
    aliases.add_argument("--target", required=True)
    aliases.add_argument("--aliases-plan", required=True)
    aliases.add_argument("--execute", action="store_true")
    aliases.set_defaults(func=command_apply_aliases)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
