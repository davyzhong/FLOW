"""Initialize or reset the Damai enterprise package in one database transaction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))
sys.path.insert(0, str(ROOT / "scripts"))


def _assert_schema_head(database_url: str) -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine, text

    config = Config(str(ROOT / "services/api/alembic.ini"))
    script_heads = set(ScriptDirectory.from_config(config).get_heads())
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            if not connection.dialect.has_table(connection, "alembic_version"):
                raise RuntimeError("数据库缺少 alembic_version，请先部署系统迁移")
            database_heads = set(
                connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
            )
        if database_heads != script_heads:
            raise RuntimeError(
                f"数据库迁移未处于当前代码 head: database={sorted(database_heads)}, "
                f"expected={sorted(script_heads)}；请先由系统管理员部署迁移"
            )
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("full", "business"), help="full 同步组织并重置业务；business 只重置业务"
    )
    args = parser.parse_args()

    from build_enterprise_data_package import verify as verify_package

    manifest = verify_package()
    from flow_api.settings import get_settings

    settings = get_settings()
    database_url = settings.database_url
    _assert_schema_head(database_url)

    from flow_api.fixtures.damai.initialize import initialize_damai_enterprise
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    engine = create_engine(database_url)
    try:
        with Session(engine) as session, session.begin():
            connection = session.connection()
            connection.execute(
                text("SELECT set_config('flow.enterprise_code', :code, true)"),
                {"code": manifest["enterprise_code"]},
            )
            preflight = (
                ROOT / "data/enterprise/damai-logistics/v1/sql/00_preflight.sql"
            ).read_text(encoding="utf-8")
            connection.exec_driver_sql(preflight)
            receipt = initialize_damai_enterprise(session, args.mode)
        print(
            json.dumps(
                {
                    "package": manifest["package_id"],
                    "version": manifest["package_version"],
                    **receipt,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
