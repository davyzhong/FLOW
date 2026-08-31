from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricDefinitionDependency,
    MetricSnapshot,
    MetricValue,
)

from .intake_service_support import intake_session_fixture


@pytest.fixture(name="metric_session")
def metric_session_fixture(
    intake_session: Session,
) -> Iterator[Session]:
    yield intake_session
    intake_session.rollback()
    for model in (
        MetricValue,
        MetricDefinitionDependency,
        MetricSnapshot,
        MetricDefinition,
    ):
        intake_session.execute(delete(model))
    intake_session.commit()


_intake_session_fixture = intake_session_fixture
