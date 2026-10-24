#!/usr/bin/env python3
"""显式重置指定企业的大麦经营数据；保留组织身份与平台治理数据。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api/src"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enterprise-id", required=True, type=UUID)
    args = parser.parse_args()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from flow_api.fixtures.damai.reset import reset_damai_business_data
    from flow_api.settings import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        with Session(engine) as session:
            counts = reset_damai_business_data(session, args.enterprise_id)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        engine.dispose()
    print(f"已重置企业 {args.enterprise_id} 的经营演示数据：{counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
