from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from flow_api.enterprise.models import Enterprise
from flow_api.fixtures.damai.initialize import ENTERPRISE_CODE, initialize_damai_enterprise
from flow_api.fixtures.damai.loader import seed_damai_demo
from flow_api.fixtures.damai.reset import reset_damai_business_data
from flow_api.infrastructure.models.analytics import (
    AnalysisRun,
    Finding,
    MetricSnapshot,
    ReviewEvent,
)
from flow_api.infrastructure.models.canonical import (
    FactArCollection,
    FactBudget,
    FactFinancialActual,
    FactOperatingActual,
)
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.security.models import AuditEvent


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def test_reset_archives_review_history_and_rebuilds_business_data() -> None:
    from flow_api.settings import get_settings

    engine = create_engine(get_settings().database_url)
    try:
        with Session(engine) as session:
            seed_damai_demo(session)
            session.commit()
            enterprise = session.scalar(
                select(Enterprise).where(Enterprise.code == ENTERPRISE_CODE)
            )
            assert enterprise is not None
            batch = session.scalar(
                select(AnalysisBatch).where(AnalysisBatch.name == "damai-demo-v1")
            )
            assert batch is not None
            target_snapshot_ids = select(MetricSnapshot.id).where(
                MetricSnapshot.batch_id == batch.id
            )
            target_run_ids = select(AnalysisRun.id).where(
                AnalysisRun.metric_snapshot_id.in_(target_snapshot_ids)
            )
            target_finding_ids = select(Finding.id).where(
                Finding.analysis_run_id.in_(target_run_ids)
                | Finding.metric_snapshot_id.in_(target_snapshot_ids)
            )
            review_count = session.scalar(
                select(func.count())
                .select_from(ReviewEvent)
                .where(ReviewEvent.finding_id.in_(target_finding_ids))
            )
            assert review_count and review_count > 0

            old_batch_id = batch.id
            enterprise_id = enterprise.id
            old_archive_count = session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.enterprise_id == enterprise_id,
                    AuditEvent.event_type == "finding.review_history.archived",
                )
            )

            def fail_seed(_session, *, sync_organization, upsert_enterprise):
                raise RuntimeError("injected initialization failure")

            session.rollback()  # close the read transaction before simulating CLI transaction scope
            with (
                pytest.raises(RuntimeError, match="injected initialization failure"),
                session.begin(),
            ):
                initialize_damai_enterprise(session, "full", seed=fail_seed)
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(AnalysisBatch)
                    .where(AnalysisBatch.id == old_batch_id)
                )
                == 1
            )
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(AuditEvent)
                    .where(
                        AuditEvent.enterprise_id == enterprise_id,
                        AuditEvent.event_type == "finding.review_history.archived",
                    )
                )
                == old_archive_count
            )

            reset_receipt = reset_damai_business_data(session, enterprise_id)
            assert reset_receipt["batches_deleted"] == 1
            assert reset_receipt["review_events_archived"] == review_count
            session.flush()
            archived = session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.enterprise_id == enterprise_id,
                    AuditEvent.event_type == "finding.review_history.archived",
                )
            )
            assert archived >= review_count
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(AnalysisBatch)
                    .where(AnalysisBatch.id == old_batch_id)
                )
                == 0
            )
            session.commit()

            assert (
                session.scalar(
                    select(func.count())
                    .select_from(AnalysisBatch)
                    .where(AnalysisBatch.id == old_batch_id)
                )
                == 0
            )
            for model in (FactFinancialActual, FactBudget, FactOperatingActual, FactArCollection):
                assert session.scalar(select(func.count()).select_from(model)) == 0
            session.commit()
    finally:
        engine.dispose()
