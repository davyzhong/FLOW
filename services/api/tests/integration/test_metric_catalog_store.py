"""P4 库内行业指标集一致性门禁。

守护三件事：
1. 双源一致：YAML 加载与库内文档加载的目录 definition_set_hash 完全一致
   （快照身份链不变的前提），且等于已发布基线哈希；
2. 导入幂等：重复导入不产生新版本、不重复行；
3. 兜底行为：库内无 effective 文档时 resolve 回退 YAML；未知定义集 typed 错误。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.metric_library import MetricCatalogDocument
from flow_api.metrics.catalog import load_metric_catalog, metric_catalog_hash
from flow_api.metrics.models import MetricCatalog
from flow_api.metrics.service import MetricSnapshotService
from flow_api.metrics_store import (
    MetricCatalogStoreError,
    import_metric_catalog_document,
    load_metric_catalog_from_db,
    resolve_metric_catalog,
)
from flow_api.settings import get_settings

from .intake_service_support import intake_session_fixture  # noqa: F401
from .metric_snapshot_support import metric_session_fixture  # noqa: F401

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG_YAML = REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml"
BASELINE_HASH = "4214ae85339eb7495defb69f1d59fdddec5e3183d5d4ba64c966be9f53270b38"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    session.execute(delete(MetricCatalogDocument))
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _yaml_catalog() -> MetricCatalog:
    return load_metric_catalog(CATALOG_YAML)


def test_yaml_baseline_hash_is_pinned(session: Session) -> None:
    """基线锚定：仓库 YAML 的目录哈希等于已发布基线（防止悄悄改契约）。"""

    assert metric_catalog_hash(_yaml_catalog()) == BASELINE_HASH


def test_db_document_matches_yaml_hash(session: Session) -> None:
    """双源一致：库内文档加载的目录与 YAML 逐位同哈希（快照身份不变）。"""

    summary = import_metric_catalog_document(session, CATALOG_YAML)
    assert summary["definition_set_id"] == "flow.metrics.logistics.v1"
    assert summary["content_hash"] == BASELINE_HASH

    db_catalog = load_metric_catalog_from_db(session, "flow.metrics.logistics.v1")
    assert metric_catalog_hash(db_catalog) == BASELINE_HASH
    assert [m.metric_code for m in db_catalog.metrics] == [
        m.metric_code for m in _yaml_catalog().metrics
    ]
    assert len(db_catalog.metrics) == 15


def test_import_is_idempotent(session: Session) -> None:
    import_metric_catalog_document(session, CATALOG_YAML)
    import_metric_catalog_document(session, CATALOG_YAML)
    rows = session.query(MetricCatalogDocument).all()
    assert len(rows) == 1
    assert rows[0].version == 1


def test_resolve_falls_back_to_yaml_when_db_empty(session: Session) -> None:
    catalog = resolve_metric_catalog(session, CATALOG_YAML)
    assert metric_catalog_hash(catalog) == BASELINE_HASH


def test_unknown_definition_set_raises_typed_error(session: Session) -> None:
    with pytest.raises(MetricCatalogStoreError) as excinfo:
        load_metric_catalog_from_db(session, "flow.metrics.nonexistent.v9")
    assert excinfo.value.code == "metric_catalog_not_found"


def test_db_catalog_builds_snapshot_with_baseline_identity(
    metric_session: Session,
) -> None:
    """实证：用库内文档加载的目录实际构建快照，definition_set_hash 等于基线。"""

    from .test_metric_source_repository import _publish_reference

    import_metric_catalog_document(metric_session, CATALOG_YAML)
    db_catalog = load_metric_catalog_from_db(metric_session, "flow.metrics.logistics.v1")
    _, batch, _ = _publish_reference(metric_session)
    snapshot = MetricSnapshotService().create_snapshot(
        metric_session, batch_id=batch.id, as_of_month=202608, catalog=db_catalog
    )
    assert snapshot.definition_set_hash == BASELINE_HASH

