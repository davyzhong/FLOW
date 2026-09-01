from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.infrastructure.models.analytics import AnalysisResult, AnalysisRun, Finding

from .analysis_run_support import ANALYSIS_POLICY, analysis_session_fixture, publish_snapshot
from .analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)

_analysis_session_fixture = analysis_session_fixture


def test_mid_write_failure_leaves_no_run_results_or_findings(
    analysis_session: Session,
) -> None:
    snapshot = publish_snapshot(analysis_session)

    def fail_before_publication() -> None:
        raise RuntimeError("injected analysis write failure")

    with pytest.raises(RuntimeError, match="injected analysis"):
        AnalysisRunService().create_run(
            analysis_session,
            snapshot_id=snapshot.id,
            loaded_policy=load_analysis_policy(Path(ANALYSIS_POLICY)),
            failure_hook=fail_before_publication,
        )

    assert analysis_session.scalar(select(func.count()).select_from(AnalysisRun)) == 0
    assert analysis_session.scalar(select(func.count()).select_from(AnalysisResult)) == 0
    assert analysis_session.scalar(select(func.count()).select_from(Finding)) == 0
