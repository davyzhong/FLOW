#!/usr/bin/env python3
"""构建大麦演示静态发行版（实施计划 Task 4；确定性，可重复构建零漂移）。

用法（仓库根或 services/api 均可）：
    python3 scripts/build_damai_demo.py --output fixtures/damai
    python3 scripts/build_damai_demo.py --output fixtures/damai --check

产物（规格 §4.2）：
    canonical/*.jsonl、workbooks/damai_logistics_full_v1.xlsx、
    statements/damai_fy2025.yaml、damai_fy2026.yaml、
    forecast/rolling_forecast.jsonl、manifest.json、README.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
if str(REPOSITORY_ROOT / "services/api/src") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "services/api/src"))

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.workbook import render_workbook
from flow_api.fixtures.damai.canonical import (
    build_damai_canonical_package,
)
from flow_api.fixtures.damai.generator import build_damai_package
from flow_api.fixtures.damai.operations import build_damai_operations_payloads
from flow_api.fixtures.damai.statements import (
    build_damai_statement_payloads,
)
from flow_api.fixtures.generator import write_canonical_package

CONTRACT_PATH = REPOSITORY_ROOT / "templates/excel/flow_v1_contract.yaml"
GENERATOR_VERSION = "damai-demo-v2"
_WORKBOOK_REL = "workbooks/damai_logistics_full_v1.xlsx"
_STATEMENT_RELS = {
    "FY2022": "statements/damai_fy2022.yaml",
    "FY2023": "statements/damai_fy2023.yaml",
}
_FORECAST_REL = "forecast/rolling_forecast.jsonl"
_OPERATIONS_RELS = (
    "operations/damai_segment_series.yaml",
    "operations/damai_operating_metrics.yaml",
)
_MANIFEST_REL = "manifest.json"
_README_REL = "README.md"

README_TEXT = """---
doc_id: FLOW-GEN-DAMAI-FIXTURE-README-001
title: 大麦物流演示发行版 fixtures 说明
doc_type: generated
status: generated
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
generator_ref: scripts/build_damai_demo.py
input_hash: deterministic-static
---

# 大麦物流演示发行版（synthetic）

本目录由 `scripts/build_damai_demo.py` 确定性生成，**禁止手工修改**；重建命令：

    python3 scripts/build_damai_demo.py --output fixtures/damai --check

- `canonical/*.jsonl`：flow.excel.v1 canonical 数据包（批次/期间/维度/事实）；
- `canonical/financial_actuals.jsonl`：24 个月 × 4 个模拟业务单元 × 24 个科目，共 2,304 行；金额单位为人民币元。损益、现金流、资产负债关键余额分别勾稽至来源登记的菜鸟 FY2022/FY2023 年报；FY2021 年末余额用于月度插值起点。公开资料没有月度或事业部明细，故这些明细按登记的确定性规则分配，属于 synthetic allocation，不是菜鸟逐月/逐事业部实际值；
- 订单数和件量是基于演示客单价派生的整数，不是菜鸟披露的实际单量；每单件数按确定性演示参数派生；
- `workbooks/damai_logistics_full_v1.xlsx`：标准工作簿（Finance BP 导入用，
  actual/budget，无 forecast——预测在 sidecar，`persistence: static-only`、
  `page_coverage: excluded`，不得冒充已上线能力）；
- `statements/damai_fy2022.yaml`、`damai_fy2023.yaml`：菜鸟申请稿披露三表
  逐行原值（IFRS，千元；来源登记血缘，非合成投影）；
- `operations/damai_segment_series.yaml`、`damai_operating_metrics.yaml`：
  DAMAI.SYN 独立分部序列与运营事实（synthetic，血缘指向 manifest.json）；
- `forecast/rolling_forecast.jsonl`：静态预测 sidecar；
- `manifest.json`：期间、行数、披露年度汇总、年度来源 fact ID、合成分配说明、逐文件 SHA-256、`synthetic: true`。

装载：`python3 scripts/seed_damai_demo.py`（幂等，经 IntakeService/领域服务链，
见规格《大麦物流演示数据设计》§4.3）。
"""

REQUIRED_FILES: tuple[str, ...] = (
    "canonical/ar_collections.jsonl",
    "canonical/batch.jsonl",
    "canonical/customer_segments.jsonl",
    "canonical/customers.jsonl",
    "canonical/financial_actuals.jsonl",
    "canonical/logistics_products.jsonl",
    "canonical/management_accounts.jsonl",
    "canonical/monthly_budgets.jsonl",
    "canonical/operating_actuals.jsonl",
    "canonical/organizations.jsonl",
    "canonical/periods.jsonl",
    "canonical/regions.jsonl",
    "canonical/scenario_versions.jsonl",
    _WORKBOOK_REL,
    _STATEMENT_RELS["FY2022"],
    _STATEMENT_RELS["FY2023"],
    _FORECAST_REL,
    *_OPERATIONS_RELS,
    _MANIFEST_REL,
    _README_REL,
)


def _workbook_semantic_digest(path: Path) -> str:
    """xlsx 的单元格值级指纹：zip 容器（时间戳/顺序）不参与，语义漂移才漂移。"""

    from openpyxl import load_workbook

    workbook = load_workbook(path, data_only=True, read_only=True)
    payload: list[Any] = []
    for sheet in workbook.worksheets:
        payload.append([sheet.title])
        for row in sheet.iter_rows(values_only=True):
            payload.append(["" if v is None else str(v) for v in row])
    workbook.close()
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return "semantic:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decimal(value: Any) -> Any:
    from decimal import Decimal

    if isinstance(value, Decimal):
        return format(value, ".4f")
    return value


def _dump_statements(destination: Path) -> dict[str, int]:
    payloads = build_damai_statement_payloads()
    counts: dict[str, int] = {}
    for fy, rel in _STATEMENT_RELS.items():
        payload = payloads[fy]
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=True, width=100),
            encoding="utf-8",
        )
        statement_rows = payload.get("statements") or payload.get("report") or payload
        counts[rel] = len(statement_rows) if isinstance(statement_rows, (list, dict)) else 0
    return counts


def _dump_operations(destination: Path, package: dict[str, Any]) -> None:
    payloads = build_damai_operations_payloads()
    for key, rel in zip(
        ("segment_series", "operating_metrics"), _OPERATIONS_RELS, strict=True
    ):
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.safe_dump(payloads[key], allow_unicode=True, sort_keys=True, width=100),
            encoding="utf-8",
        )


def _dump_forecast(destination: Path, sidecar: dict[str, Any]) -> None:
    target = destination / _FORECAST_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = sidecar.get("rows", [])
    lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    target.write_bytes(("\n".join(lines) + ("\n" if lines else "")).encode("utf-8"))


def _summaries(destination: Path) -> dict[str, str]:
    from decimal import Decimal

    total_revenue = Decimal(0)
    path = destination / "canonical/operating_actuals.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            total_revenue += Decimal(json.loads(line)["revenue"])
    return {"operating_revenue_total": format(total_revenue, ".4f")}


def _dimension_coverage(package: Any) -> dict[str, Any]:
    orgs = package.organizations
    return {
        "organizations": {
            "group": sum(1 for o in orgs if o.level == "group"),
            "business_unit": sum(1 for o in orgs if o.level == "business_unit"),
        },
        "customer_segments": len(package.customer_segments),
        "customers": len(package.customers),
        "logistics_products": len(package.logistics_products),
        "regions": len(package.regions),
        "operating_actuals": {
            "rows": len(package.operating_actuals),
            "grain": "month × customer × product",
        },
        "financial_actuals": {
            "rows": len(package.financial_actuals),
            "grain": "month × business_unit × management_account",
        },
        "monthly_budgets": {
            "rows": len(package.monthly_budgets),
            "grain": "month × business_unit × customer_segment × product × account",
        },
        "ar_collections": {
            "rows": len(package.ar_collections),
            "grain": "month × customer × bucket",
        },
    }


def _fiscal_year_summary(raw: dict[str, Any]) -> dict[str, Any]:
    from decimal import Decimal

    all_months = tuple(
        sorted({row["month"] for row in raw["monthly_facts"]["operating_actual"]})
    )
    months_by_fy = {"FY2022": all_months[:12], "FY2023": all_months[12:]}
    summary: dict[str, Any] = {}
    for fy, months in months_by_fy.items():
        revenue = Decimal(0)
        cost = Decimal(0)
        ocf = Decimal(0)
        closing_cash = Decimal(0)
        for row in raw["monthly_facts"]["operating_actual"]:
            if row["month"] in months:
                revenue += Decimal(str(row["revenue"]))
                cost += Decimal(str(row["cost"]))
        for row in raw["monthly_facts"]["cash_flow"]:
            if row["month"] in months:
                ocf += Decimal(str(row["ocf"]))
                if row["month"] == months[-1]:
                    closing_cash = Decimal(str(row["cash_balance"]))
        statement_totals = {
            account: sum(
                (
                    Decimal(str(row[account]))
                    for row in raw["monthly_facts"]["statement_lines"]
                    if row["month"] in months
                ),
                Decimal("0"),
            )
            for account in ("OPERATING_PROFIT", "net_profit")
        }
        closing_balance = next(
            row
            for row in raw["monthly_facts"]["balance_sheet"]
            if row["month"] == months[-1]
        )
        summary[fy] = {
            "months": [months[0], months[-1]],
            "revenue_wan": format(revenue, ".4f"),
            "gross_margin": format((revenue - cost) / revenue, ".4f"),
            "operating_profit_wan": format(statement_totals["OPERATING_PROFIT"], ".4f"),
            "net_profit_wan": format(statement_totals["net_profit"], ".4f"),
            "operating_cash_flow_wan": format(ocf, ".4f"),
            "closing_cash_wan": format(closing_cash, ".4f"),
            "total_assets_wan": closing_balance["TOTAL_ASSETS"],
            "total_liabilities_wan": closing_balance["TOTAL_LIABILITIES"],
            "total_equity_wan": closing_balance["TOTAL_EQUITY"],
            "current_assets_wan": closing_balance["CURRENT_ASSETS"],
            "current_liabilities_wan": closing_balance["CURRENT_LIABILITIES"],
            "ar_balance_wan": closing_balance["AR_BALANCE"],
            "inventory_wan": closing_balance["INVENTORY_BALANCE"],
            "borrowings_wan": closing_balance["BORROWINGS"],
        }
    return summary


_EVENT_TRACES: dict[str, str] = {
    "E1": "operating_actual：国际族 Q4（10-12 月）明细行毛利率 −1.5pp",
    "E2": "operating_actual：国内族分析期后 6 月明细行毛利率 +0.8pp",
    "E3": "ar_aging：DM-CUST-007/019 自 2022-10 逾期桶 ×1.35、回款 ×0.75",
    "E4": "budget vs operating_actual：国内仓配事业部单元格预算 ×1.12，实际低于预算",
    "E5": "cash_flow：2022-12/2023-01 OCF = 经营利润 × 0.55（利润-现金背离）",
    "E6": "operating_actual：分析期后 6 月 index%8∈{0,2} 客户第二产品轮换",
}


def _planted_events(raw: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            **event,
            "discoverable": True,
            "trace": _EVENT_TRACES.get(event["event_id"], ""),
        }
        for event in raw["planted_events"]
    ]


def _lineage(raw: dict[str, Any]) -> dict[str, Any]:
    import yaml

    registry = yaml.safe_load(
        (REPOSITORY_ROOT / "config/damai/source_facts_v1.yaml").read_text(
            encoding="utf-8"
        )
    )
    anchor_items = {
        "REVENUE": ("合并利润表", "收入"),
        "GROSS_PROFIT": ("合并利润表", "毛利"),
        "SALES_MARKETING_EXPENSE": ("合并利润表", "销售及市场推广开支"),
        "GENERAL_ADMIN_EXPENSE": ("合并利润表", "一般及行政开支"),
        "PRODUCT_DEVELOPMENT_EXPENSE": ("合并利润表", "产品开发开支"),
        "FINANCIAL_ASSET_IMPAIRMENT": (
            "合并利润表",
            "金融资产减值(转回)/计提",
        ),
        "OTHER_INCOME": ("合并利润表", "其他收入"),
        "OTHER_NET_GAIN_LOSS": ("合并利润表", "其他收益/(亏损)净额"),
        "OPERATING_PROFIT": ("合并利润表", "经营亏损/利润"),
        "NET_PROFIT": ("合并利润表", "年度亏损/利润"),
        "OPERATING_CASH_FLOW": ("合并现金流量表", "经营活动所得现金净额"),
        "CASH_AND_CASH_EQUIVALENTS": (
            "合并现金流量表",
            "年末现金及现金等价物",
        ),
        "TOTAL_ASSETS": ("合并资产负债表", "资产总计"),
        "TOTAL_LIABILITIES": ("合并资产负债表", "负债合计"),
        "TOTAL_EQUITY": ("合并资产负债表", "权益总额"),
        "CURRENT_ASSETS": ("合并资产负债表", "流动资产合计"),
        "CURRENT_LIABILITIES": ("合并资产负债表", "流动负债合计"),
        "AR_BALANCE": ("合并资产负债表", "贸易应收及其他预付款(流动)"),
        "INVENTORY_BALANCE": ("合并资产负债表", "存货"),
        "BORROWINGS": ("合并资产负债表", "借款"),
    }
    facts_by_period = {
        period: {
            (fact["statement"], fact["item_zh"]): fact["fact_id"]
            for fact in registry["facts"]
            if fact["period"] == period
        }
        for period in ("FY2021", "FY2022", "FY2023")
    }
    annual_fact_ids = {
        period: {
            account: facts_by_period[period][statement_item]
            for account, statement_item in anchor_items.items()
        }
        for period in ("FY2022", "FY2023")
    }
    annual_fact_ids["FY2021"] = {
        account: facts_by_period["FY2021"][statement_item]
        for account, statement_item in anchor_items.items()
        if account in {"CASH_AND_CASH_EQUIVALENTS", *{
            "TOTAL_ASSETS", "TOTAL_LIABILITIES", "TOTAL_EQUITY", "CURRENT_ASSETS",
            "CURRENT_LIABILITIES", "AR_BALANCE", "INVENTORY_BALANCE", "BORROWINGS",
        }}
    }
    return {
        "generator": "scripts/build_damai_demo.py",
        "generator_version": GENERATOR_VERSION,
        "profile_version": raw["profile_version"],
        "determinism": "uuid5 record_id + Decimal 全程 + fixed Random(42) 族权重扰动",
        "units": {
            "canonical": "人民币元（原始公开锚点千元→万元→元）",
            "statements": "人民币千元（菜鸟申请稿披露原值，非 canonical 换算）",
        },
        "annual_public_anchors": {
            "registry": "config/damai/source_facts_v1.yaml",
            "allocation": "公开财报仅披露年度/期末数；月度、组织明细是 synthetic 分配，尾差保留以逐级勾稽年度锚点",
            "fact_ids": annual_fact_ids,
            "methods": {
                "income_statement_by_month": "各披露行按同财年 synthetic 月度收入权重分配",
                "canonical_amount_conversion": "源事实人民币千元先转换万元用于可读生成，再按 10,000 转换为 flow.excel.v1 的人民币元",
                "operating_expense_net": "管理口径 OPERATING_EXPENSE = 销售/行政/研发/减值开支 - 其他收入 - 其他收益/(亏损)净额；营业利润 = 毛利 - 该净额",
                "operating_cash_flow_by_month": "按月度毛利权重分配；E5 异常月权重乘 0.55 后年度归一",
                "organization_detail": "按同月 synthetic 业务单元收入占比分配，尾差并入最后单元",
                "cash_balance_by_month": "FY2021/FY2022/FY2023 年末披露余额之间按月线性插值；每年年末精确锚定",
                "balance_sheet_by_month": "资产负债项目按 FY2021/FY2022/FY2023 年末披露锚点线性插值；年末总额与资产=负债+权益恒等式精确校验",
                "direct_cost_by_category": "披露收入与毛利之间的营业成本按仓储 30%、运输 60%、其他 10% synthetic 拆分",
            "order_and_shipment_counts": "按每单 120 元确定性派生，订单四舍五入为整数，每单 2 件；属于演示派生量",
            },
        },
        "derived_parameters": {
            "cost_split": {
                "WAREHOUSING_COST": "0.30",
                "TRANSPORTATION_COST": "0.60",
                "OTHER_DIRECT_COST": "0.10",
            },
            "budget_multiplier": {"default": "1.03", "国内仓配事业部": "1.12"},
            "budget_ocf_rate": "0.92",
            "ar_outstanding_basis": (
                "customer_month_revenue × credit_term_days / 120（客群信用期 30/45/60/90）"
            ),
            "ar_bucket_rates": {
                "current": "0.70", "1-30": "0.12", "31-60": "0.08",
                "61-90": "0.06", "90+": "尾差",
            },
            "order_unit_price_cny": "120",
            "shipments_per_order": "2",
            "order_count_rounding": "ROUND_HALF_UP to integer",
        },
    }


def build_release(destination: Path) -> dict[str, Any]:
    """构建完整发行版并返回 {manifest, files: {rel: sha256}}。"""

    destination.mkdir(parents=True, exist_ok=True)
    raw = build_damai_package()
    package = build_damai_canonical_package()

    canonical_dir = destination / "canonical"
    write_canonical_package(package, canonical_dir)

    contract = load_contract(CONTRACT_PATH)
    render_workbook(contract, package, destination / _WORKBOOK_REL)

    statement_counts = _dump_statements(destination)
    _dump_forecast(destination, raw["forecast_sidecar"])
    _dump_operations(destination, raw)

    (destination / _README_REL).write_text(README_TEXT, encoding="utf-8")

    written = tuple(rel for rel in REQUIRED_FILES if rel != _MANIFEST_REL)
    files: dict[str, str] = {}
    for rel in written:
        target = destination / rel
        if not target.is_file():
            raise FileNotFoundError(f"发行版缺失文件：{rel}")
        # xlsx 的 zip 容器非字节确定（openpyxl 时间戳/顺序），以语义指纹入册
        files[rel] = (
            _workbook_semantic_digest(target) if rel == _WORKBOOK_REL else _sha256_of(target)
        )

    row_counts = {
        rel: sum(
            1
            for line in (destination / rel).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        for rel in written
        if rel.startswith("canonical/") and rel.endswith(".jsonl")
    }
    manifest: dict[str, Any] = {
        "generator": "scripts/build_damai_demo.py",
        "generator_version": GENERATOR_VERSION,
        "synthetic": True,
        "profile_version": raw["profile_version"],
        "batch_code": package.batch.batch_code,
        "periods": {
            "total": len(package.periods),
            "comparison": sum(1 for p in package.periods if p.window == "comparison"),
            "analysis": sum(1 for p in package.periods if p.window == "analysis"),
            "analysis_start": package.batch.analysis_start_month,
            "analysis_end": package.batch.analysis_end_month,
        },
        "row_counts": row_counts,
        "statement_row_counts": statement_counts,
        "dimension_coverage": _dimension_coverage(package),
        "fiscal_year_summary": _fiscal_year_summary(raw),
        "planted_events": _planted_events(raw),
        "lineage": _lineage(raw),
        "summaries": _summaries(destination),
        "files": {rel: files[rel] for rel in written},
    }
    (destination / _MANIFEST_REL).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    files[_MANIFEST_REL] = _sha256_of(destination / _MANIFEST_REL)
    return {"manifest": manifest, "files": files}


def check_release(destination: Path) -> int:
    with __import__("tempfile").TemporaryDirectory() as td:
        rebuilt = build_release(Path(td))
    committed = {
        rel: (
            _workbook_semantic_digest(destination / rel)
            if rel == _WORKBOOK_REL
            else _sha256_of(destination / rel)
        )
        for rel in REQUIRED_FILES
    }
    drift = [rel for rel in REQUIRED_FILES if committed[rel] != rebuilt["files"][rel]]
    for rel in drift:
        print(f"DRIFT {rel}: committed {committed[rel]} != rebuilt {rebuilt['files'][rel]}", file=sys.stderr)
    print("release check: " + ("PASS" if not drift else "FAIL"))
    return 0 if not drift else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPOSITORY_ROOT / "fixtures/damai")
    parser.add_argument("--check", action="store_true", help="重建对账已提交产物")
    args = parser.parse_args(argv)
    root = args.output.resolve()
    if args.check:
        return check_release(root)
    result = build_release(root)
    print(f"release built at {root} ({len(result['files'])} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
