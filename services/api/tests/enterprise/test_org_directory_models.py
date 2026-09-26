from __future__ import annotations

from flow_api.infrastructure.models import Base


def test_enterprise_directory_models_register_expected_tenant_constraints() -> None:
    org = Base.metadata.tables["enterprise_org_unit"]
    position = Base.metadata.tables["enterprise_position"]
    member = Base.metadata.tables["enterprise_member"]

    assert {"enterprise_id", "code", "parent_id", "attributes"} <= set(org.c.keys())
    assert {"enterprise_id", "org_unit_id", "code"} <= set(position.c.keys())
    assert {
        "enterprise_id",
        "actor_id",
        "employee_code",
        "org_unit_id",
        "position_id",
        "supervisor_actor_id",
        "identity_metadata",
    } <= set(member.c.keys())
    assert any(
        {"enterprise_id", "code"} <= {column.name for column in constraint.columns}
        for constraint in org.constraints
    )
    assert any(
        {"enterprise_id", "actor_id"} <= {column.name for column in constraint.columns}
        for constraint in member.constraints
    )
    assert any(
        {"parent_id", "enterprise_id"} <= {column.name for column in constraint.columns}
        for constraint in org.foreign_key_constraints
    )
    assert any(
        {"org_unit_id", "enterprise_id"} <= {column.name for column in constraint.columns}
        for constraint in position.foreign_key_constraints
    )
    assert any(
        {"position_id", "enterprise_id"} <= {column.name for column in constraint.columns}
        for constraint in member.foreign_key_constraints
    )


def test_member_identity_metadata_requires_synthetic_marker() -> None:
    member = Base.metadata.tables["enterprise_member"]
    check_sql = {
        str(constraint.sqltext)
        for constraint in member.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert any("identity_metadata" in sql and "synthetic" in sql for sql in check_sql)
