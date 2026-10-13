"""大麦演示财务报表（披露事实版，2026-10-13 时间线迁移）。

报表载荷不再是 canonical 的合成投影（旧 65% 利息拆分、10% 折旧估算、
负债/现金流构成拆分等无来源行已全部移除，处置见来源登记 unavailable 节
U-DM-*），而是来源登记所依据的菜鸟申请稿披露三表逐行原值：

- statements/damai_fy2023.yaml：本期 FY2023（2022-04~2023-03）、上期 FY2022；
- statements/damai_fy2022.yaml：本期 FY2022（2021-04~2022-03）、上期 FY2021（期初锚）；
- 合并所有者权益变动表未在登记抽取范围 → 不再生成合成权益表，勾稽覆盖
  如实缺省（发布门禁对权益变动表缺失本就非阻断）；
- 资产负债表列名按 BS 惯例改为 期末余额/期初余额（原值不变，仅列名呈现）。

单位：人民币千元（披露原文，不换算）。血缘：docs/implementation/p5/
cainiao_*_statements.yaml（逐行值经登记构建脚本与 registry 交叉核验）→
原件 PDF SHA `3e2c3679…`。跨文件同期间值不一致时直接报错，静默取值。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_P5_DIR_REL = "docs/implementation/p5"
_STATEMENT_FILES = {
    "FY2021": "cainiao_2021fy_statements.yaml",  # 仅作 FY2022 上期列核验基准
    "FY2022": "cainiao_2022fy_statements.yaml",
    "FY2023": "cainiao_2023fy_statements.yaml",
}
_FISCAL_MONTHS = {
    "FY2021": ("2020-04", "2021-03"),
    "FY2022": ("2021-04", "2022-03"),
    "FY2023": ("2022-04", "2023-03"),
}
_BS_COLUMN_RENAME = {"本期发生额": "期末余额", "上期发生额": "期初余额"}


def _repo_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到仓库根（templates/excel/flow_v1_contract.yaml）")


def _load_p5_statements(fy: str) -> dict[str, Any]:
    path = _repo_root() / _P5_DIR_REL / _STATEMENT_FILES[fy]
    loaded: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded


def _month_tuple(fy: str) -> tuple[str, ...]:
    from flow_api.fixtures.damai.profile import ANALYSIS_MONTHS, PRIOR_MONTHS

    if fy == "FY2022":
        return PRIOR_MONTHS
    if fy == "FY2023":
        return ANALYSIS_MONTHS
    raise KeyError(f"演示报表不含期间 {fy}")


def _prior_year_values(fy: str) -> dict[tuple[str, str], Any]:
    """上一年度文件的本期值（期初/上期列的交叉核验基准）。"""

    prior_fy = {"FY2022": "FY2021", "FY2023": "FY2022"}[fy]
    doc = _load_p5_statements(prior_fy)
    values: dict[tuple[str, str], Any] = {}
    for statement, rows in (doc.get("statements") or {}).items():
        for row in rows:
            values[(statement, row["item"])] = row.get("本期发生额")
    return values


def build_damai_statement_payloads() -> dict[str, dict[str, Any]]:
    """从菜鸟申请稿整理资产生成 FY2022/FY2023 两份披露报表载荷（确定性）。"""

    payloads: dict[str, dict[str, Any]] = {}
    for fy in ("FY2022", "FY2023"):
        doc = _load_p5_statements(fy)
        source_statements = doc.get("statements")
        if not source_statements:
            raise ValueError(f"{_STATEMENT_FILES[fy]} 缺少 statements 节")
        prior_values = _prior_year_values(fy)

        statements: dict[str, list[dict[str, Any]]] = {}
        for statement, rows in source_statements.items():
            converted: list[dict[str, Any]] = []
            for row in rows:
                item = row["item"]
                current = row.get("本期发生额")
                prior = row.get("上期发生额")
                # 跨文件同期间值核验：本文件上期列必须等于上年文件本期值
                baseline = prior_values.get((statement, item))
                if baseline is not None and prior is not None and baseline != prior:
                    raise ValueError(
                        f"{fy} 报表跨文件值不一致：{statement}/{item} "
                        f"上期 {prior} != 上年文件本期 {baseline}"
                    )
                new_row: dict[str, Any] = {"item": item}
                if statement == "合并资产负债表":
                    new_row["期末余额"] = current
                    new_row["期初余额"] = prior
                else:
                    new_row["本期发生额"] = current
                    new_row["上期发生额"] = prior
                converted.append(new_row)
            statements[statement] = converted

        payloads[fy] = {
            "entity": "damai-logistics",
            "stock_code": "DAMAI.SYN",
            "company": "大麦物流",
            "unit": "人民币千元",
            "period": _month_tuple(fy),
            "data_layer": "disclosed_fact",
            "source_ref": f"{_P5_DIR_REL}/{_STATEMENT_FILES[fy]}",
            "provenance": {
                "registry": "config/damai/source_facts_v1.yaml",
                "registry_id": "flow.damai_source_facts.v1",
                "original": (
                    "菜鸟智慧物流网络港交所申请版本（2023-09-26 递交、2024-03 撤回）"
                    "附录 I 会计师报告（PwC，IFRS）；大麦物流为基于该披露构建的"
                    "演示主体（DAMAI.SYN），不是菜鸟本身"
                ),
                "statement_pages": {
                    "合并利润表": 464,
                    "合并资产负债表": 466,
                    "合并现金流量表": 474,
                },
            },
            "statements": statements,
            "notes_index": [
                "编制基础：菜鸟申请稿会计师报告（IFRS，人民币千元）；大麦演示主体引用，"
                "申请版本（draft）身份须随展示",
                "期间口径：财年截至 3 月 31 日；FY2022 = 2021-04~2022-03，"
                "FY2023 = 2022-04~2023-03",
                "逐行值与来源登记 config/damai/source_facts_v1.yaml 一致（含原件 SHA 与页锚）",
                (
                    "unavailable：FY2024 起无菜鸟完整三表披露（U-CN-FY2024PLUS-FULL-STATEMENTS）；"
                    "FY2026 起菜鸟并入「所有其他」（U-CN-FY2026-STANDALONE）；"
                    "合并所有者权益变动表未在登记抽取范围；"
                    "旧合成行（利息 65% 拆分、折旧 10% 估算、负债/现金流构成拆分）已移除"
                ),
            ],
        }
    return payloads


__all__ = ["build_damai_statement_payloads"]
