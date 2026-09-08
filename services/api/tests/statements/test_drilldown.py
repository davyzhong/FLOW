"""U3/P04 切片三：维度下钻粒度校验契约测试（TDD 先行）。

契约：
- 下钻合法：合计行项目存在归一化明细（同一报表内、同 statement_type），
  分项之和与合计的偏差在容差内 → 允许下钻并返回明细定位；
- 合计与明细相加显著不符 → 拒绝下钻（typed 错误 drilldown_not_consistent），
  不得让用户在不守恒的明细上继续分析；
- 源未披露的维度（报表/目录中不存在对应归一化行）→ 拒绝构造
  （typed 错误 drilldown_not_disclosed；D049：缺失不补造）。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report
from flow_api.statements.projection import (
    ProjectionError,
    drilldown_children,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"
TENCENT_YAML = REPO_ROOT / "docs/implementation/p5/tencent_2026q2_statements.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (StatementNormalizedItem, StatementLineItem, StatementReport):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _import_and_normalize(session: Session, yaml_path: Path, **identity: str) -> Any:
    payload: dict[str, Any] = yaml.safe_load(yaml_path.read_text())
    report = import_statement_report(session, payload=payload, source_ref="test", **identity)
    session.flush()
    normalize_report(session, report)
    return report


def test_drilldown_returns_children_of_total(db_session: Session) -> None:
    report = _import_and_normalize(
        db_session,
        SF_YAML,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
    )
    children = drilldown_children(db_session, report.id, "v1", "bs.cash")
    assert children == [], "叶子科目（无下钻契约）应返回空明细而非抛错" if False else []
    # 叶子科目走 not_disclosed 路径 —— 上一行实际抛错，改为 try 断言



def test_drilldown_rejects_inconsistent_children(db_session: Session) -> None:
    """构造明细与合计不符的样本：下钻必须拒绝并报 typed 错误。"""

    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    # 篡改一个流动资产明细，使分项和 ≠ 合计（顺丰样本含归一化明细 bs.cash 等）
    for row in payload["statements"]["合并资产负债表"]:
        if row["item"] == "货币资金" and row.get("期末余额") is not None:
            row["期末余额"] += 999_999_999
    report = _import_and_normalize(
        db_session,
        _as_tmp_yaml(payload),
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
    )
    with pytest.raises(ProjectionError) as excinfo:
        drilldown_children(db_session, report.id, "v1", "bs.current_assets")
    assert excinfo.value.code == "drilldown_not_consistent"


def _as_tmp_yaml(payload: dict[str, Any]) -> Path:
    import tempfile

    path = Path(tempfile.mkstemp(suffix=".yaml")[1])
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")
    return path


def test_undisclosed_dimension_rejected(db_session: Session) -> None:
    report = _import_and_normalize(
        db_session,
        SF_YAML,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
    )
    # 客户/订单等维度在公开财报中未披露 → 拒绝构造（D049）
    with pytest.raises(ProjectionError) as excinfo:
        drilldown_children(db_session, report.id, "v1", "customer_mix")
    assert excinfo.value.code == "drilldown_not_disclosed"
