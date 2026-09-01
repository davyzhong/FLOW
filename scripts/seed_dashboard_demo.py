from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from flow_api.dashboard.fixture import publish_dashboard_snapshot_series
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.metrics.catalog import load_metric_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish the idempotent 12-month FLOW dashboard snapshot series."
    )
    parser.add_argument("--batch-id", type=UUID)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    catalog = load_metric_catalog(
        REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml"
    )
    with get_session_factory()() as session:
        batch_id = arguments.batch_id
        if batch_id is None:
            batch_id = session.scalar(
                select(AnalysisBatch.id)
                .where(AnalysisBatch.status == "published")
                .order_by(AnalysisBatch.created_at.desc(), AnalysisBatch.id.desc())
                .limit(1)
            )
        if batch_id is None:
            raise SystemExit("no published analysis batch is available")
        snapshots = publish_dashboard_snapshot_series(
            session, batch_id=batch_id, catalog=catalog
        )
        session.commit()
        print(f"published {len(snapshots)} dashboard snapshots for batch {batch_id}")


if __name__ == "__main__":
    main()
