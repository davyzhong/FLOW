from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from flow_api.dashboard.fixture import (
    bootstrap_dashboard_demo,
    publish_dashboard_snapshot_series,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.metrics.catalog import load_metric_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish the idempotent 12-month FLOW dashboard snapshot series."
    )
    parser.add_argument("--batch-id", type=UUID)
    parser.add_argument(
        "--fresh-batch",
        action="store_true",
        help="Publish a brand-new demo batch so findings start in candidate review state.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    catalog = load_metric_catalog(
        REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml"
    )
    with get_session_factory()() as session:
        batch_id = arguments.batch_id
        if batch_id is None:
            publication = bootstrap_dashboard_demo(
                session,
                repository_root=REPOSITORY_ROOT,
                fresh_batch=arguments.fresh_batch,
            )
            batch_id = publication.batch_id
            snapshots_count = len(publication.metric_snapshot_ids)
            analysis_run_id = publication.analysis_run_id
        else:
            snapshots = publish_dashboard_snapshot_series(
                session, batch_id=batch_id, catalog=catalog
            )
            snapshots_count = len(snapshots)
            analysis_run_id = None
        session.commit()
        print(f"published {snapshots_count} dashboard snapshots for batch {batch_id}")
        if analysis_run_id is not None:
            print(f"published dashboard analysis run {analysis_run_id}")


if __name__ == "__main__":
    main()
