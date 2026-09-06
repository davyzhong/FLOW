"""引擎指标目录的库内存储（P4：库内行业指标集）。

- import_metric_catalog_document：验证 YAML 载荷后按 (definition_set_id,
  version) 幂等入库；同版本重导入整块替换 payload；
- load_metric_catalog_from_db：取指定定义集的最新 effective 文档并经同一
  MetricCatalog.model_validate 构建目录；
- resolve_metric_catalog：库内优先，空库回退 YAML 文件（兼容读取期）。

哈希一致性由构造保证（同一载荷 → 同一模型 → 同一 definition_set_hash），
并由 tests/integration/test_metric_catalog_store.py 门禁守护。
"""

from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.metric_library import MetricCatalogDocument
from flow_api.metrics.catalog import load_metric_catalog, metric_catalog_hash
from flow_api.metrics.models import MetricCatalog


class MetricCatalogStoreError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def import_metric_catalog_document(
    session: Session, path: str | Path
) -> dict[str, object]:
    """幂等导入引擎目录 YAML 为库内 effective 文档。"""

    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    catalog = MetricCatalog.model_validate(payload)  # 入库前先验证契约
    definition_set_id = catalog.definition_set_id
    version = _document_version(session, definition_set_id)
    existing = session.scalar(
        select(MetricCatalogDocument).where(
            MetricCatalogDocument.definition_set_id == definition_set_id,
            MetricCatalogDocument.version == version,
        )
    )
    if existing is None:
        existing = MetricCatalogDocument(
            definition_set_id=definition_set_id,
            version=version,
            status="effective",
            payload=payload,
        )
        session.add(existing)
    else:
        existing.payload = payload
        existing.status = "effective"
    session.flush()
    return {
        "definition_set_id": definition_set_id,
        "version": existing.version,
        "content_hash": metric_catalog_hash(catalog),
        "metric_count": len(catalog.metrics),
    }


def _document_version(session: Session, definition_set_id: str) -> int:
    latest = session.scalar(
        select(MetricCatalogDocument.version)
        .where(MetricCatalogDocument.definition_set_id == definition_set_id)
        .order_by(MetricCatalogDocument.version.desc())
        .limit(1)
    )
    return 1 if latest is None else latest


def load_metric_catalog_from_db(
    session: Session, definition_set_id: str
) -> MetricCatalog:
    document = session.scalar(
        select(MetricCatalogDocument)
        .where(
            MetricCatalogDocument.definition_set_id == definition_set_id,
            MetricCatalogDocument.status == "effective",
        )
        .order_by(MetricCatalogDocument.version.desc())
        .limit(1)
    )
    if document is None:
        raise MetricCatalogStoreError(
            "metric_catalog_not_found",
            f"库内没有定义集 {definition_set_id} 的 effective 目录文档",
        )
    return MetricCatalog.model_validate(document.payload)


def resolve_metric_catalog(session: Session, yaml_path: str | Path) -> MetricCatalog:
    """库内优先加载引擎目录；库内缺失时回退 YAML 文件（兼容读取期）。"""

    try:
        catalog = load_metric_catalog(yaml_path)
    except Exception:  # YAML 也读不到时让 DB 错误浮出
        catalog = None
    definition_set_id = catalog.definition_set_id if catalog is not None else None
    if definition_set_id is not None:
        try:
            return load_metric_catalog_from_db(session, definition_set_id)
        except MetricCatalogStoreError:
            pass
    if catalog is None:
        raise MetricCatalogStoreError(
            "metric_catalog_unavailable",
            f"库内与 YAML 均无法加载指标目录：{yaml_path}",
        )
    return catalog


__all__ = [
    "MetricCatalogStoreError",
    "import_metric_catalog_document",
    "load_metric_catalog_from_db",
    "resolve_metric_catalog",
]
