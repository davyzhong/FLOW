from __future__ import annotations

from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from flow_api.enterprise.models import AnalysisCycle, Enterprise
from flow_api.infrastructure.models.intake import AnalysisBatch


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def test_business_reset_deletes_only_named_batch_for_target_enterprise() -> None:
    from flow_api.fixtures.damai.reset import reset_damai_business_data
    from flow_api.settings import get_settings

    engine = create_engine(get_settings().database_url)
    target_id, other_id = uuid4(), uuid4()
    with Session(engine) as session:
        target = Enterprise(id=target_id, code=f"reset-target-{target_id}", name="目标企业")
        other = Enterprise(id=other_id, code=f"reset-other-{other_id}", name="其他企业")
        session.add_all([target, other])
        session.flush()
        target_cycle = AnalysisCycle(enterprise_id=target_id, period_key="2026-08", status="frozen")
        other_cycle = AnalysisCycle(enterprise_id=other_id, period_key="2026-08", status="open")
        session.add_all([target_cycle, other_cycle])
        session.flush()
        target_batch = AnalysisBatch(
            name="damai-demo-v1",
            analysis_cycle_id=target_cycle.id,
            module_kind="internal",
            fact_context_version=2,
        )
        other_batch = AnalysisBatch(
            name="damai-demo-v1",
            analysis_cycle_id=other_cycle.id,
            module_kind="internal",
            fact_context_version=2,
        )
        unrelated_batch = AnalysisBatch(
            name="unrelated",
            analysis_cycle_id=target_cycle.id,
            module_kind="internal",
            fact_context_version=2,
        )
        session.add_all([target_batch, other_batch, unrelated_batch])
        session.flush()

        receipt = reset_damai_business_data(session, target_id)
        session.flush()

        remaining_ids = set(
            session.scalars(
                select(AnalysisBatch.id).where(
                    AnalysisBatch.id.in_([target_batch.id, other_batch.id, unrelated_batch.id])
                )
            ).all()
        )
        assert target_batch.id not in remaining_ids
        assert other_batch.id in remaining_ids
        assert unrelated_batch.id in remaining_ids
        assert receipt["batches_deleted"] == 1
        assert receipt["cycles_reopened"] == 1
        assert (
            session.scalar(
                select(AnalysisCycle.status).where(AnalysisCycle.enterprise_id == target_id)
            )
            == "open"
        )
        session.rollback()
    engine.dispose()
