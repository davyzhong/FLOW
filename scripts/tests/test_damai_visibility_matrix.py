from __future__ import annotations

import json

from scripts import damai_visibility_matrix
from scripts.damai_visibility_matrix import VisibilityTarget, build_visibility_targets


def test_visibility_targets_cover_read_routes_and_exclude_freeze_gets() -> None:
    seed = {
        "reports": [
            {"report_id": "report-1", "stock_code": "DAMAI.SYN", "fy": "FY2026"}
        ],
        "analytics": {
            "batch_id": "batch-1",
            "import_version_id": "import-1",
            "analysis_run_id": "run-1",
            "metric_snapshot_ids": ["metric-snapshot-1"],
        },
        "workflow": {
            "findings": [{"finding_id": "finding-1"}],
            "freezes": {
                "internal_report": {"report_snapshot_id": "report-snapshot-1"},
                "operations_overview": [
                    {"snapshot_id": "operations-snapshot-1"}
                ],
            },
        },
    }
    discovery = {
        "dashboard": {
            "filter_options": {
                "dimensions": [
                    {"dimension": "region", "options": [{"id": "region-1"}]}
                ]
            }
        },
        "statements": {"reports": [{"id": "report-1"}]},
        "public_periods": {
            "periods": [
                {"stock_code": "CAINIAO", "period_label": "FY2023"}
            ]
        },
        "findings": {
            "findings": [
                {
                    "finding_id": "finding-1",
                    "batch_id": "batch-1",
                    "metric_snapshot_id": "metric-snapshot-1",
                    "analysis_run_id": "run-1",
                }
            ]
        },
        "intake_batches": {"batches": [{"batch_id": "batch-1"}]},
        "intake_versions": [
            {
                "batch_id": "batch-1",
                "versions": {"versions": [{"id": "import-1"}]},
            }
        ],
        "report_snapshots": {"snapshots": [{"id": "report-snapshot-1"}]},
        "operations_snapshots": {
            "snapshots": [{"id": "operations-snapshot-1"}]
        },
    }

    targets = build_visibility_targets(seed, discovery)
    paths = {target.path for target in targets}

    assert VisibilityTarget(
        "dashboard-month", "/api/v1/dashboard/overview", "dataset=damai"
    ) in targets
    assert VisibilityTarget(
        "dashboard-ytd",
        "/api/v1/dashboard/overview?period_view=ytd",
        "dataset=damai",
    ) in targets
    assert "/api/v1/statements/report-1/projection" in paths
    assert "/api/v1/operations/public/CAINIAO/FY2023" in paths
    assert "/api/v1/dashboard/overview?region_id=region-1" in paths
    assert "/api/v1/intake/batches/batch-1/versions" in paths
    assert "/api/v1/intake/imports/import-1/cleaning-summary" in paths
    assert "/api/v1/publishing/snapshots/report-snapshot-1/attempts" in paths
    assert "/api/v1/operations/snapshots/operations-snapshot-1/attempts" in paths
    assert not any("objective-snapshot" in path for path in paths)
    assert not any(path.endswith(("/html", "/xlsx", "/pptx", "/pdf")) for path in paths)
    assert len(targets) == len(paths)


def test_visibility_targets_keep_query_variants_distinct() -> None:
    targets = build_visibility_targets(
        {
            "reports": [],
            "analytics": {"batch_id": "batch-1", "import_version_id": "import-1"},
            "workflow": {"findings": [], "freezes": {}},
        },
        {
            "statements": {"reports": []},
            "dashboard": {"filter_options": {"dimensions": []}},
            "public_periods": {"periods": []},
            "findings": {"findings": []},
            "intake_batches": {"batches": []},
            "intake_versions": [],
            "report_snapshots": {"snapshots": []},
            "operations_snapshots": {"snapshots": []},
        },
    )

    assert len(targets) == len({target.path for target in targets})


def test_matrix_persists_all_read_evidence_when_a_route_fails(tmp_path, monkeypatch) -> None:
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(
        json.dumps(
            {
                "reports": [],
                "analytics": {"batch_id": "batch-1", "import_version_id": "import-1"},
                "workflow": {"findings": [], "freezes": {}},
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "matrix.jsonl"

    def fake_get(_api_url: str, target: VisibilityTarget) -> tuple[int, bytes]:
        return (503, b'{"error":"unavailable"}') if target.alias == "discovery-statements" else (200, b"{}")

    monkeypatch.setattr(damai_visibility_matrix, "_get_json", fake_get)
    summary = damai_visibility_matrix.run_matrix("http://isolated", seed_path, output_path)

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert summary["ok"] is False
    assert summary["http_200"] == len(records) - 1
    assert records[0]["status"] == 503
    assert records[0]["response_sha256"]
