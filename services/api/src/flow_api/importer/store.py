"""导入数据集存储（R2）：validated 行写入 SQLite，按 dataset_id 与演示数据隔离。

金额以原始字符串落库（Decimal 精度由调用方保证），读取时再转 Decimal。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from flow_api.importer.validation import ValidationResult


def _new_id() -> str:
    return str(uuid.uuid4())


class ImportStore:
    """导入数据集的最小存储门面；engine 由调用方注入（隔离测试友好）。"""

    def __init__(self, engine: Any) -> None:
        self._engine = engine
        self._session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        import sqlalchemy as sa

        meta = sa.MetaData()
        self._datasets = sa.Table(
            "import_dataset",
            meta,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("source_filename", sa.String(512), nullable=False),
        )
        self._tb_rows = sa.Table(
            "import_trial_balance_row",
            meta,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("dataset_id", sa.String(36), nullable=False),
            sa.Column("period", sa.String(7), nullable=False),
            sa.Column("account_code", sa.String(64), nullable=False),
            sa.Column("account_name", sa.String(255), nullable=False),
            sa.Column("account_category", sa.String(16), nullable=False),
            sa.Column("direction", sa.String(2), nullable=False),
            sa.Column("opening_balance", sa.String(64), nullable=False),
            sa.Column("debit_amount", sa.String(64), nullable=False),
            sa.Column("credit_amount", sa.String(64), nullable=False),
            sa.Column("closing_balance", sa.String(64), nullable=False),
            sa.Column("row_index", sa.Integer(), nullable=False),
        )
        self._is_rows = sa.Table(
            "import_income_statement_row",
            meta,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("dataset_id", sa.String(36), nullable=False),
            sa.Column("period", sa.String(7), nullable=False),
            sa.Column("item", sa.String(255), nullable=False),
            sa.Column("current_amount", sa.String(64), nullable=False),
            sa.Column("ytd_amount", sa.String(64), nullable=False),
            sa.Column("row_index", sa.Integer(), nullable=False),
        )
        meta.create_all(self._engine)

    def save_dataset(
        self,
        name: str,
        source_filename: str,
        trial_balance: ValidationResult,
        income_statement: ValidationResult | None,
    ) -> str:
        dataset_id = _new_id()
        with Session(self._engine) as session, session.begin():
            session.execute(
                self._datasets.insert().values(
                    id=dataset_id,
                    name=name,
                    created_at=datetime.now(),
                    source_filename=source_filename,
                )
            )
            for index, row in enumerate(trial_balance.rows, start=1):
                session.execute(
                    self._tb_rows.insert().values(
                        id=_new_id(),
                        dataset_id=dataset_id,
                        period=row["会计期间"],
                        account_code=row["科目编码"],
                        account_name=row["科目名称"],
                        account_category=row["科目类别"],
                        direction=row["方向"],
                        opening_balance=row["期初余额"],
                        debit_amount=row["本期借方发生额"],
                        credit_amount=row["本期贷方发生额"],
                        closing_balance=row["期末余额"],
                        row_index=index,
                    )
                )
            if income_statement is not None:
                for index, row in enumerate(income_statement.rows, start=1):
                    session.execute(
                        self._is_rows.insert().values(
                            id=_new_id(),
                            dataset_id=dataset_id,
                            period=row["会计期间"],
                            item=row["项目"],
                            current_amount=row["本期金额"],
                            ytd_amount=row["本年累计金额"],
                            row_index=index,
                        )
                    )
        return dataset_id

    def list_datasets(self) -> list[dict[str, str]]:
        with Session(self._engine) as session:
            rows = session.execute(
                select(
                    self._datasets.c.id,
                    self._datasets.c.name,
                    self._datasets.c.created_at,
                    self._datasets.c.source_filename,
                ).order_by(self._datasets.c.created_at.desc())
            ).all()
        return [
            {
                "id": row.id,
                "name": row.name,
                "created_at": row.created_at.isoformat(),
                "source_filename": row.source_filename,
            }
            for row in rows
        ]

    def dataset_balances(self, dataset_id: str) -> list[dict[str, Any]]:
        with Session(self._engine) as session:
            rows = session.execute(
                select(self._tb_rows)
                .where(self._tb_rows.c.dataset_id == dataset_id)
                .order_by(self._tb_rows.c.row_index)
            ).all()
        return [
            {
                "period": row.period,
                "account_code": row.account_code,
                "account_name": row.account_name,
                "account_category": row.account_category,
                "direction": row.direction,
                "opening_balance": Decimal(row.opening_balance),
                "debit_amount": Decimal(row.debit_amount),
                "credit_amount": Decimal(row.credit_amount),
                "closing_balance": Decimal(row.closing_balance),
            }
            for row in rows
        ]

    def dataset_income_items(self, dataset_id: str) -> list[dict[str, Any]]:
        """利润表存储行（M2）；金额读回 Decimal，与余额行同口径。"""
        with Session(self._engine) as session:
            rows = session.execute(
                select(self._is_rows)
                .where(self._is_rows.c.dataset_id == dataset_id)
                .order_by(self._is_rows.c.row_index)
            ).all()
        return [
            {
                "period": row.period,
                "item": row.item,
                "current_amount": Decimal(row.current_amount),
                "ytd_amount": Decimal(row.ytd_amount),
            }
            for row in rows
        ]

    def delete_dataset(self, dataset_id: str) -> bool:
        from sqlalchemy import delete as sa_delete

        with Session(self._engine) as session, session.begin():
            result: Any = session.execute(
                sa_delete(self._datasets).where(self._datasets.c.id == dataset_id)
            )
            deleted = result.rowcount
            session.execute(
                sa_delete(self._tb_rows).where(self._tb_rows.c.dataset_id == dataset_id)
            )
            session.execute(
                sa_delete(self._is_rows).where(self._is_rows.c.dataset_id == dataset_id)
            )
        return bool(deleted)

    def dataset_overview(self, dataset_id: str) -> dict[str, Any] | None:
        """从科目余额表直接聚合的概览口径（不进治理发布链，只读校验视图）。

        资产合计=期末余额方向为借且类别为资产的行合计；负债/权益同理。
        勾稽校验=资产 −(负债+权益)，理想为 0（不等说明科目类别标注有误）。
        """
        balances = self.dataset_balances(dataset_id)
        if not balances:
            return None
        assets = liabilities = equity = Decimal("0")
        periods: set[str] = set()
        for row in balances:
            periods.add(row["period"])
            closing = row["closing_balance"]
            category = row["account_category"]
            if category == "资产":
                assets += closing
            elif category == "负债":
                liabilities += closing
            elif category == "权益":
                equity += closing
        return {
            "dataset_id": dataset_id,
            "periods": sorted(periods),
            "account_count": len(balances),
            "total_assets": str(assets),
            "total_liabilities": str(liabilities),
            "total_equity": str(equity),
            "identity_check": str(assets - liabilities - equity),
        }


def default_store(database_url: str) -> ImportStore:
    return ImportStore(create_engine(database_url))
