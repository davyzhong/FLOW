from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricDefinitionDependency,
)
from flow_api.metrics.models import MetricCatalog, MetricSpec


class MetricDefinitionConflictError(RuntimeError):
    pass


def _definition_config(metric: MetricSpec) -> dict[str, object]:
    return {
        "dependencies": list(metric.dependencies),
        "time_behavior": metric.time_behavior,
        "output_scale": metric.output_scale,
        "allowed_dimension_sets": [list(item) for item in metric.allowed_dimension_sets],
        "budget_dimension_sets": [list(item) for item in metric.budget_dimension_sets],
    }


def _definition_matches(definition: MetricDefinition, metric: MetricSpec) -> bool:
    return (
        definition.name == metric.name
        and definition.business_definition == metric.business_definition
        and definition.formula == metric.formula
        and definition.aggregation == metric.aggregation
        and definition.unit == metric.unit
        and definition.definition_config == _definition_config(metric)
    )


def upsert_metric_definitions(
    session: Session, catalog: MetricCatalog
) -> dict[str, MetricDefinition]:
    definitions: dict[str, MetricDefinition] = {}
    for metric in catalog.metrics:
        definition = session.scalar(
            select(MetricDefinition).where(
                MetricDefinition.metric_code == metric.metric_code,
                MetricDefinition.version == metric.version,
            )
        )
        if definition is None:
            definition = MetricDefinition(
                metric_code=metric.metric_code,
                version=metric.version,
                name=metric.name,
                business_definition=metric.business_definition,
                formula=metric.formula,
                aggregation=metric.aggregation,
                unit=metric.unit,
                definition_config=_definition_config(metric),
            )
            session.add(definition)
            session.flush()
        elif not _definition_matches(definition, metric):
            raise MetricDefinitionConflictError(
                f"metric definition identity has conflicting content: "
                f"{metric.metric_code}@{metric.version}"
            )
        definitions[metric.metric_code] = definition
    return definitions


def ensure_definition_dependencies(
    session: Session,
    catalog: MetricCatalog,
    definitions: Mapping[str, MetricDefinition],
) -> None:
    for metric in catalog.metrics:
        parent = definitions[metric.metric_code]
        existing = tuple(
            session.scalars(
                select(MetricDefinitionDependency)
                .where(MetricDefinitionDependency.metric_definition_id == parent.id)
                .order_by(MetricDefinitionDependency.position)
            )
        )
        expected_ids = tuple(definitions[code].id for code in metric.dependencies)
        existing_ids = tuple(item.dependency_definition_id for item in existing)
        if existing and existing_ids != expected_ids:
            raise MetricDefinitionConflictError(
                f"metric dependency graph conflicts with persisted identity: "
                f"{metric.metric_code}@{metric.version}"
            )
        if not existing:
            session.add_all(
                [
                    MetricDefinitionDependency(
                        metric_definition_id=parent.id,
                        dependency_definition_id=definitions[dependency].id,
                        position=position,
                    )
                    for position, dependency in enumerate(metric.dependencies, start=1)
                ]
            )
    session.flush()
