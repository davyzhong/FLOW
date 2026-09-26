"""Run a safe, hash-only GET visibility matrix against an isolated Damai API."""

from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class VisibilityTarget:
    alias: str
    path: str
    context: str = ""
    expected_status: int = 200
    expected_error_code: str | None = None


def _records(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def build_visibility_targets(
    seed: dict[str, Any], discovery: dict[str, Any]
) -> list[VisibilityTarget]:
    """Build only read-only paths; freezing/rendering GET endpoints are excluded."""
    targets: list[VisibilityTarget] = []
    seen: set[str] = set()

    def add(alias: str, path: str, context: str = "") -> None:
        if path not in seen:
            seen.add(path)
            targets.append(VisibilityTarget(alias, path, context))

    roots = (
        ("dashboard-month", "/api/v1/dashboard/overview", "dataset=damai"),
        ("dashboard-ytd", "/api/v1/dashboard/overview?period_view=ytd", "dataset=damai"),
        ("statements", "/api/v1/statements", "all-companies"),
        ("statement-sources", "/api/v1/statements/sources", "source-catalog"),
        ("public-periods", "/api/v1/operations/public-periods", "public-catalog"),
        ("metric-library", "/api/v1/metric-library", "governed-dictionary"),
        ("metric-semantic-context", "/api/v1/metric-library/semantic-context", "governed-dictionary"),
        ("metric-computation-inventory", "/api/v1/metric-library/computation-inventory", "public-facts"),
        ("coverage-public", "/api/v1/metric-library/coverage?dataset=public", "dataset=public"),
        ("coverage-damai", "/api/v1/metric-library/coverage?dataset=damai", "dataset=damai"),
        ("publishing-snapshots", "/api/v1/publishing/snapshots", "enterprise"),
        ("freeze-candidates", "/api/v1/publishing/freeze-candidates", "enterprise"),
        ("operations-snapshots", "/api/v1/operations/snapshots", "enterprise"),
        ("findings", "/api/v1/investigations", "enterprise"),
        ("intake-batches", "/api/v1/intake/batches", "current-actor-enterprise"),
    )
    for alias, path, context in roots:
        add(alias, path, context)

    dimension_params = {
        "organization": "organization_id",
        "customer_segment": "customer_segment_id",
        "logistics_product": "logistics_product_id",
        "region": "region_id",
    }
    dashboard = discovery.get("dashboard", {})
    filter_options = dashboard.get("filter_options", {})
    dimensions = _records(filter_options, "dimensions")
    dimension_options: dict[str, tuple[str, list[str]]] = {}
    for row in dimensions:
        dimension = row.get("dimension")
        param = dimension_params.get(str(dimension))
        options = _records(row, "options")
        if not param:
            continue
        option_ids = [str(option["id"]) for option in options if option.get("id")]
        dimension_options[str(dimension)] = (param, option_ids)
        for option in options:
            if not option.get("id"):
                continue
            option_id = str(option["id"])
            add(
                f"dashboard-filter-{dimension}-{option_id}",
                f"/api/v1/dashboard/overview?{param}={option_id}",
                f"dataset=damai;period_view=month;{param}={option_id}",
            )
            add(
                f"dashboard-ytd-filter-{dimension}-{option_id}",
                f"/api/v1/dashboard/overview?period_view=ytd&{param}={option_id}",
                f"dataset=damai;period_view=ytd;{param}={option_id}",
            )

    advertised_combinations = {
        tuple(sorted(str(item) for item in combination))
        for combination in filter_options.get("supported_combinations", [])
        if isinstance(combination, list)
    }
    # Verify every supported two-dimension value pair; for unsupported dimension sets,
    # probe one representative per period and assert the API's typed 422 rejection.
    for (left_dimension, (left_param, left_ids)), (
        right_dimension,
        (right_param, right_ids),
    ) in combinations(sorted(dimension_options.items()), 2):
        pair = tuple(sorted((left_dimension, right_dimension)))
        supported = pair in advertised_combinations
        value_pairs = (
            [(left_id, right_id) for left_id in left_ids for right_id in right_ids]
            if supported
            else list(zip(left_ids[:1], right_ids[:1], strict=True))
        )
        for left_id, right_id in value_pairs:
            for period_view in ("month", "ytd"):
                query = urlencode(
                    {
                        "period_view": period_view,
                        left_param: left_id,
                        right_param: right_id,
                    }
                )
                add(
                    f"dashboard-pair-{left_dimension}-{left_id}-{right_dimension}-{right_id}-{period_view}",
                    f"/api/v1/dashboard/overview?{query}",
                    f"dataset=damai;period_view={period_view};{left_param}={left_id};{right_param}={right_id}",
                )
                if not supported:
                    target = targets[-1]
                    targets[-1] = VisibilityTarget(
                        alias=target.alias,
                        path=target.path,
                        context=target.context,
                        expected_status=422,
                        expected_error_code="unsupported_filter_combination",
                    )

    report_rows = _records(seed, "reports") + _records(
        discovery.get("statements", {}), "reports"
    )
    reports: dict[str, dict[str, Any]] = {}
    for row in report_rows:
        report_id = row.get("report_id") or row.get("id")
        if report_id:
            reports[str(report_id)] = row
    for report_id, row in sorted(reports.items()):
        company = str(row.get("company_name") or row.get("stock_code") or "unknown-company")
        period = str(row.get("fy") or row.get("period_label") or "unknown-period")
        context = f"company={company};period={period};dataset=damai"
        add(f"statement-{period}", f"/api/v1/statements/{report_id}", context)
        add(f"projection-{period}", f"/api/v1/statements/{report_id}/projection", context)
        add(f"corrections-{period}", f"/api/v1/statements/{report_id}/corrections", context)
        add(f"workbench-{period}", f"/api/v1/analysis/workbench/{report_id}", context)
        add(f"operations-{period}", f"/api/v1/operations/overview/{report_id}", context)

    for row in _records(discovery.get("public_periods", {}), "periods"):
        stock_code = row.get("stock_code")
        public_period = row.get("period_label") or row.get("period")
        if stock_code and public_period:
            add(
                f"public-{stock_code}-{public_period}",
                f"/api/v1/operations/public/{stock_code}/{public_period}",
                f"company={stock_code};period={public_period};dataset=public",
            )

    for row in _records(discovery.get("findings", {}), "findings"):
        finding_id = row.get("finding_id") or row.get("id")
        if not finding_id:
            continue
        params = []
        for key in ("batch_id", "metric_snapshot_id", "analysis_run_id"):
            if row.get(key):
                params.append(f"{key}={row[key]}")
        query = f"?{'&'.join(params)}" if params else ""
        add(f"finding-{finding_id}", f"/api/v1/investigations/{finding_id}{query}", "enterprise")

    intake_versions = {
        str(row.get("batch_id")): row.get("versions", {})
        for row in discovery.get("intake_versions", [])
        if isinstance(row, dict) and row.get("batch_id")
    }
    for row in _records(discovery.get("intake_batches", {}), "batches", "items"):
        batch_id = row.get("batch_id") or row.get("id")
        if batch_id:
            context = f"batch={batch_id};scope=current-actor-enterprise"
            add(f"intake-versions-{batch_id}", f"/api/v1/intake/batches/{batch_id}/versions", context)
            version_payload = intake_versions.get(str(batch_id), {})
            for version in _records(version_payload, "versions"):
                import_id = version.get("id") or version.get("import_version_id")
                if not import_id:
                    continue
                add(
                    f"intake-cleaning-{import_id}",
                    f"/api/v1/intake/imports/{import_id}/cleaning-summary",
                    context,
                )

    snapshot_rows = _records(discovery.get("report_snapshots", {}), "snapshots")
    for row in snapshot_rows:
        snapshot_id = row.get("id") or row.get("report_snapshot_id")
        if snapshot_id:
            add(
                f"report-attempts-{snapshot_id}",
                f"/api/v1/publishing/snapshots/{snapshot_id}/attempts",
                f"report_snapshot={snapshot_id};enterprise",
            )

    for row in _records(discovery.get("operations_snapshots", {}), "snapshots"):
        snapshot_id = row.get("id") or row.get("snapshot_id")
        if snapshot_id:
            add(
                f"operations-attempts-{snapshot_id}",
                f"/api/v1/operations/snapshots/{snapshot_id}/attempts",
                f"operations_snapshot={snapshot_id};enterprise",
            )

    return targets


def _get_json(api_url: str, target: VisibilityTarget) -> tuple[int, bytes]:
    request = Request(f"{api_url.rstrip('/')}{target.path}", method="GET")
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()
    except URLError as error:
        raise RuntimeError(f"{target.alias}: request failed: {error}") from error


def run_matrix(api_url: str, seed_path: Path, output_path: Path) -> dict[str, Any]:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    discovery_specs = {
        "statements": VisibilityTarget("discovery-statements", "/api/v1/statements"),
        "public_periods": VisibilityTarget("discovery-public-periods", "/api/v1/operations/public-periods"),
        "findings": VisibilityTarget("discovery-findings", "/api/v1/investigations"),
        "intake_batches": VisibilityTarget("discovery-intake-batches", "/api/v1/intake/batches"),
        "report_snapshots": VisibilityTarget("discovery-report-snapshots", "/api/v1/publishing/snapshots"),
        "operations_snapshots": VisibilityTarget("discovery-operations-snapshots", "/api/v1/operations/snapshots"),
        "dashboard": VisibilityTarget("discovery-dashboard", "/api/v1/dashboard/overview"),
    }
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    discovery: dict[str, Any] = {}
    seen: set[str] = set()

    def fetch(target: VisibilityTarget) -> dict[str, Any]:
        try:
            status, body = _get_json(api_url, target)
        except RuntimeError as error:
            status, body = 0, str(error).encode("utf-8")
            failures.append(f"{target.alias}: {error}")
        error_code: str | None = None
        if target.expected_error_code and status == target.expected_status:
            try:
                error_code = str(json.loads(body)["detail"]["code"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                error_code = None
        record = {
            **asdict(target),
            "method": "GET",
            "status": status,
            "response_bytes": len(body),
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "error_code": error_code,
        }
        records.append(record)
        seen.add(target.path)
        if status != target.expected_status:
            failures.append(
                f"{target.alias}: expected {target.expected_status}, got {status}"
            )
        elif target.expected_error_code and error_code != target.expected_error_code:
            failures.append(
                f"{target.alias}: expected error {target.expected_error_code}, got {error_code}"
            )
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            if status == 200:
                failures.append(f"{target.alias}: expected JSON response")
            return {}

    for name, target in discovery_specs.items():
        discovery[name] = fetch(target)

    discovery["intake_versions"] = []
    for batch in _records(discovery.get("intake_batches", {}), "batches", "items"):
        batch_id = batch.get("batch_id") or batch.get("id")
        if batch_id:
            version_payload = fetch(
                VisibilityTarget(
                    f"discovery-intake-versions-{batch_id}",
                    f"/api/v1/intake/batches/{batch_id}/versions",
                    f"batch={batch_id};scope=current-actor-enterprise",
                )
            )
            discovery["intake_versions"].append(
                {"batch_id": str(batch_id), "versions": version_payload}
            )

    for target in build_visibility_targets(seed, discovery):
        if target.path not in seen:
            fetch(target)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return {
        "schema_version": "damai-visibility-matrix/v1",
        "api_url": api_url,
        "ok": not failures,
        "route_count": len(records),
        "http_200": sum(record["status"] == 200 for record in records),
        "expected_rejections": sum(
            record["status"] == record["expected_status"]
            and record["expected_error_code"] is not None
            and record["error_code"] == record["expected_error_code"]
            for record in records
        ),
        "failures": failures,
        "sha256_manifest": hashlib.sha256(
            "\n".join(record["response_sha256"] for record in records).encode("ascii")
        ).hexdigest(),
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--seed-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = run_matrix(args.api_url, args.seed_receipt, args.output)
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
