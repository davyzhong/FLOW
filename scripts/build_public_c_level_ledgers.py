"""从冻结的评审输入与订正前后 YAML 生成公开财报 C 级逐格台账。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "validation/financial_reports/review-inputs/jdl_review_values_v1.csv"
SUSPECTED_SNAPSHOT = (
    ROOT
    / "validation/financial_reports/review-inputs/suspected_109_candidate_cells_v1.csv"
)
JDL_CROSSWALK = (
    ROOT
    / "validation/financial_reports/review-inputs/jdl_readable_twin_crosswalk_v1.csv"
)
LEDGER_DIR = ROOT / "validation/financial_reports/review-ledgers"
OLD_JDL = ROOT / "docs/implementation/p5/jdl_2025fy_statements.yaml"
NEW_JDL = (
    ROOT / "validation/financial_reports/corrections/jdl_2025fy_statements_v3.yaml"
)
JDL_PDF = "docs/knowledge-base/02_research/original/p5_samples/jd_logistics_2618/JDL_FY2025_annual_report.pdf"
JDL_PDF_SHA = "809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c"
JDL_EN_SHA = "32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009"
CAINIAO_PDF = "docs/knowledge-base/02_research/original/p5_samples/cainiao_private/Cainiao_application_proof_20230926.pdf"
CAINIAO_PDF_SHA = "3e2c367958eacf3bb50c165204a1093383381f5cdb9d8af506636b880b54b13c"
BABA_PDF = "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY2023_annual_results.pdf"
BABA_PDF_SHA = "28256e2d4fcebbd94fd2d1c46d51c75af2f93fbe492b31b764a44da0813fa9a7"

SUSPICION_GROUPS = {
    "S109-BABA-FY2020-CURRENT": (
        "BABA FY2020资产负债表current列语义",
        "阿里巴巴",
        {"BABA_FY2020_annual_results.md"},
    ),
    "S109-ALI-CASH-SCOPE": (
        "阿里现金流行名范围",
        "阿里巴巴",
        {f"BABA_FY{year}_annual_results.md" for year in range(2020, 2027)},
    ),
    "S109-ALI-EQUITY-CURRENT": (
        "阿里股权证券及其他投资流动限定",
        "阿里巴巴",
        {f"BABA_FY{year}_annual_results.md" for year in range(2020, 2027)},
    ),
    "S109-CAINIAO-NONCURRENT": (
        "菜鸟非流动科目限定",
        "菜鸟集团",
        {"Cainiao_application_proof_20230926.md"},
    ),
    "S109-JDL-ATTRIBUTION": (
        "JDL利润与综合收益归属范围",
        "京东物流",
        {"JDL_FY2025_annual_report.md"},
    ),
}
ALI_CASH_ITEMS = {
    "匯率變動對現金的影響",
    "期初現金及現金等價物",
    "期末現金及現金等價物",
    "現金淨（減少）增加",
}
CAINIAO_NONCURRENT_ITEMS = {
    "借款",
    "租赁负债",
    "指定按公允价值计量的金融负债",
    "其他金融负债",
    "按公允价值计量的金融资产",
}

JDL_COLUMNS = {
    "value_begin": "期初余额",
    "value_end": "期末余额",
    "value_current": "本期发生额",
    "value_prior": "上期发生额",
}

JDL_COMPREHENSIVE_ITEMS = {
    "以公允價值計量且其變動計入其他綜合收益的權益工具的公允價值變動",
    "功能貨幣換算至列報貨幣產生的匯兌差額",
    "境外業務換算產生之匯兌差額",
    "年度其他綜合（虧損）╱收益",
    "年度綜合收益總額",
    "本公司所有者",
    "非控制性權益",
    "預期信用損失變動淨額",
}

CAINIAO_ERRORS = [
    ("股东注资", "current", 275000, "2021=275000；2022=—；2023=—", "474-475"),
    ("股东注资", "prior", 275000, "2021=275000；2022=—；2023=—", "474-475"),
    (
        "ABS发行受限现金解除",
        "current",
        249310,
        "2021=249310；2022=—；2023=—",
        "474-475",
    ),
    ("ABS发行受限现金解除", "prior", 249310, "2021=249310；2022=—；2023=—", "474-475"),
    (
        "卖出期权负债结算付款",
        "current",
        -730640,
        "2021=(730640)；2022=—；2023=—",
        "474-475",
    ),
    (
        "卖出期权负债结算付款",
        "prior",
        -730640,
        "2021=(730640)；2022=—；2023=—",
        "474-475",
    ),
    (
        "附属公司清算资产分配",
        "current",
        -11909,
        "2021=(11909)；2022=—；2023=—",
        "474-475",
    ),
    (
        "附属公司清算资产分配",
        "prior",
        -11909,
        "2021=(11909)；2022=—；2023=—",
        "474-475",
    ),
    ("ABS偿还", "current", -1220000, "2021=—；2022=(1220000)；2023=—", "474-475"),
    ("合并有限合伙现金注入", "current", 94183, "2021=—；2022=94183；2023=—", "474-475"),
    ("已付ABS利息", "current", -60355, "2021=(45490)；2022=(60355)；2023=—", "474-475"),
    (
        "购入联营及合营投资",
        "current",
        -3548978,
        "2021=(273217)；2022=(3548978)；2023=—",
        "474-475",
    ),
    (
        "贷予关联方款项",
        "current",
        -226800,
        "2021=(165000)；2022=(226800)；2023=—",
        "474-475",
    ),
    (
        "出售按公允价值计量金融资产所得",
        "prior",
        500000,
        "2021=500000；2022=—；2023=125347",
        "474-475",
    ),
    (
        "出售附属公司投资所得净额",
        "prior",
        231653,
        "2021=231653；2022=—；2023=326756",
        "474-475",
    ),
    (
        "存放三个月以上定期存款",
        "prior",
        -13838315,
        "2021=(13838315)；2022=—；2023=(11969285)",
        "474-475",
    ),
    (
        "非全资附属公司增资所得",
        "prior",
        182150,
        "2021=182150；2022=—；2023=1945959",
        "474-475",
    ),
    (
        "部分出售非全资附属公司权益所得",
        "prior",
        62850,
        "2021=62850；2022=—；2023=1821887",
        "474-475",
    ),
    ("定期存款", "prior", 8491570, "2021=8491570；2022=—；2023=6103798", "466"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot_bundle(source: Path) -> int:
    """把忽略目录中的评审表一次性冻结为可版本化、可复用的紧凑输入表。"""
    lines = source.read_text(encoding="utf-8").splitlines()
    extracted: list[list[str]] = []
    for line in lines:
        if line.startswith("## 2."):
            break
        match = re.match(
            r"^\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*$", line
        )
        if not match:
            continue
        row = [part.strip() for part in match.groups()]
        if row[0] in {"报表", "---"}:
            continue
        extracted.append(row)
    if len(extracted) != 222:
        raise ValueError(f"JDL 评审表预期222格，实际解析{len(extracted)}格")
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "review_bundle_sha256",
        "source_pdf",
        "source_pdf_sha256",
        "statement",
        "item",
        "column",
        "value",
    ]
    with SNAPSHOT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for statement, item, column, value in extracted:
            writer.writerow(
                {
                    "review_bundle_sha256": sha256(source),
                    "source_pdf": JDL_PDF,
                    "source_pdf_sha256": JDL_PDF_SHA,
                    "statement": statement,
                    "item": item,
                    "column": column,
                    "value": value,
                }
            )
    return len(extracted)


def snapshot_suspicion_sources(source_dir: Path) -> int:
    """冻结 109 口径疑点底层评审表中可按描述枚举的候选格。"""
    rows: list[dict[str, str]] = []
    for bundle in sorted(source_dir.glob("*.md")):
        filename = bundle.name
        group_ids = [
            group_id
            for group_id, (_, _, names) in SUSPICION_GROUPS.items()
            if filename in names
        ]
        if not group_ids:
            continue
        bundle_sha = sha256(bundle)
        report = filename.removesuffix(".md")
        company = next(SUSPICION_GROUPS[group_id][1] for group_id in group_ids)
        for line in bundle.read_text(encoding="utf-8").splitlines():
            match = re.match(
                r"^\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*$", line
            )
            if not match:
                continue
            statement, item, column, value = (part.strip() for part in match.groups())
            matched_groups = []
            for group_id in group_ids:
                selected = {
                    "S109-BABA-FY2020-CURRENT": statement == "合并资产负债表"
                    and column == "value_current",
                    "S109-ALI-CASH-SCOPE": statement == "合并现金流量表"
                    and item in ALI_CASH_ITEMS
                    and column in {"value_current", "value_prior"},
                    "S109-ALI-EQUITY-CURRENT": statement == "合并资产负债表"
                    and item == "股權證券及其他投資"
                    and column in {"value_begin", "value_current", "value_end"},
                    "S109-CAINIAO-NONCURRENT": statement == "合并资产负债表"
                    and item in CAINIAO_NONCURRENT_ITEMS
                    and column in {"value_current", "value_prior"},
                    "S109-JDL-ATTRIBUTION": statement == "合并利润表"
                    and item in {"本公司所有者", "非控制性權益"}
                    and column in {"value_current", "value_prior"},
                }.get(group_id, False)
                if selected:
                    matched_groups.append(group_id)
            for group_id in matched_groups:
                rows.append(
                    {
                        "group_id": group_id,
                        "company": company,
                        "report": report,
                        "statement": statement,
                        "item": item,
                        "column": column,
                        "candidate_value": ""
                        if value in {"（空）", "(空)", "—", "–", "-"}
                        else value,
                        "source_bundle": f"work/ai-cross-review-bundle/{filename}",
                        "source_bundle_sha256": bundle_sha,
                    }
                )
    expected = {
        "S109-BABA-FY2020-CURRENT": 28,
        "S109-ALI-CASH-SCOPE": 56,
        "S109-ALI-EQUITY-CURRENT": 14,
        "S109-CAINIAO-NONCURRENT": 10,
        "S109-JDL-ATTRIBUTION": 4,
    }
    actual = {
        group_id: sum(row["group_id"] == group_id for row in rows)
        for group_id in expected
    }
    if actual != expected:
        raise ValueError(f"疑点候选分组数量不符：期望{expected}，实际{actual}")
    SUSPECTED_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    write_csv(SUSPECTED_SNAPSHOT, rows)
    return len(rows)


def read_yaml_cells(path: Path) -> dict[tuple[str, str, str], object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    cells = {}
    for statement, rows in payload["statements"].items():
        for row in rows:
            for column, value in row.items():
                if column not in {"item", "page"}:
                    cells[(statement, row["item"], column)] = value
    return cells


def jdl_review_comparison_cells(
    cells: dict[tuple[str, str, str], object],
) -> dict[tuple[str, str, str], object]:
    """按原评审表旧报表分类对齐新版综合收益表，保持台账分母稳定。"""
    normalized = dict(cells)
    for (statement, item, column), value in cells.items():
        if statement == "合并综合收益表" and item in JDL_COMPREHENSIVE_ITEMS:
            normalized[("合并利润表", item, column)] = value
    return normalized


def jdl_ledger() -> list[dict[str, str]]:
    old_cells = read_yaml_cells(OLD_JDL)
    new_cells = read_yaml_cells(NEW_JDL)
    comparison_cells = jdl_review_comparison_cells(new_cells)
    removed = {
        key: value for key, value in old_cells.items() if key not in comparison_cells
    }
    if (
        len(removed),
        sum(value is not None for value in removed.values()),
        sum(value is None for value in removed.values()),
    ) != (22, 19, 3):
        raise ValueError("JDL旧/新抽取差异不符合已验证的22格（19非空、3空值）")
    false_lookup = {
        (statement, item, column): value
        for (statement, item, column), value in removed.items()
    }
    with JDL_CROSSWALK.open(encoding="utf-8", newline="") as stream:
        crosswalk_rows = list(csv.DictReader(stream))
    crosswalk = {row["ledger_id"]: row for row in crosswalk_rows}
    if len(crosswalk_rows) != 200 or len(crosswalk) != 200:
        raise ValueError("JDL可读版逐格交叉表必须恰好覆盖200个唯一待核单元格")
    rows: list[dict[str, str]] = []
    with SNAPSHOT.open(encoding="utf-8", newline="") as stream:
        for index, source in enumerate(csv.DictReader(stream), start=1):
            try:
                value = (
                    None
                    if source["value"] in {"（空）", "(空)", ""}
                    else source["value"]
                )
                numeric = None if value is None else int(value)
            except ValueError as error:
                raise ValueError(
                    f"JDL评审输入第{index}格不是整数：{source['value']}"
                ) from error
            mapped_column = JDL_COLUMNS.get(source["column"], source["column"])
            key = (source["statement"], source["item"], mapped_column)
            status = "unknown_source_readability"
            decision = "未能以中文原件文本层完整核对；保持未决，不计通过"
            old_value = ""
            if key in false_lookup:
                status = "confirmed_wrong_statement_attribution"
                old_value = "" if false_lookup[key] is None else str(false_lookup[key])
                decision = "行来自权益变动表，不属于资产负债表；版本v2已排除"
            note = ""
            ledger_id = f"JDL-{index:03d}"
            evidence = (
                crosswalk.get(ledger_id)
                if status == "unknown_source_readability"
                else None
            )
            if status == "unknown_source_readability" and evidence is None:
                raise ValueError(f"JDL逐格交叉表缺少{ledger_id}")
            if evidence is not None:
                if (
                    evidence["source_pdf_sha256"] != JDL_PDF_SHA
                    or evidence["readable_twin_pdf_sha256"] != JDL_EN_SHA
                ):
                    raise ValueError(f"{ledger_id}交叉表源文件SHA不符")
                if evidence["status"] not in {
                    "source_line_value_verified",
                    "source_line_blank_verified",
                }:
                    raise ValueError(f"{ledger_id}交叉表状态非法：{evidence['status']}")
                status = evidence["status"]
                decision = evidence["decision"]
                source_page_physical = evidence["source_page_physical"]
                source_page_printed = evidence["source_page_printed"]
                source_coordinate = (
                    evidence["source_coordinate"]
                    + "；英文原文："
                    + evidence["source_line_evidence"]
                )
            else:
                source_page_physical = "110"
                source_page_printed = "109"
                source_coordinate = "权益变动表对应行；已由原始PDF定位"
            corrected_statement = (
                "合并综合收益表"
                if source["statement"] == "合并利润表"
                and source["item"] in JDL_COMPREHENSIVE_ITEMS
                else source["statement"]
            )
            corrected_value = new_cells.get(
                (corrected_statement, source["item"], mapped_column)
            )
            corrected_value_text = (
                "" if corrected_value is None else str(corrected_value)
            )
            rows.append(
                {
                    "ledger_id": ledger_id,
                    "company": "京东物流",
                    "report": "FY2025年报",
                    "statement": source["statement"],
                    "corrected_statement": corrected_statement,
                    "item": source["item"],
                    "column": source["column"],
                    "review_bundle_value": "" if numeric is None else str(numeric),
                    "pre_correction_extraction_value": old_value,
                    "corrected_extraction_value": corrected_value_text,
                    "source_page_physical": source_page_physical,
                    "source_page_printed": source_page_printed,
                    "source_coordinate": source_coordinate,
                    "source_pdf": source["source_pdf"],
                    "source_pdf_sha256": source["source_pdf_sha256"],
                    "readable_twin_pdf_sha256": JDL_EN_SHA,
                    "review_bundle_sha256": source["review_bundle_sha256"],
                    "status": status,
                    "decision": decision,
                    "followup_note": note,
                }
            )
    if (
        len(rows) != 222
        or sum(row["status"] == "confirmed_wrong_statement_attribution" for row in rows)
        != 22
    ):
        raise ValueError("JDL逐格台账应为222格，其中22格已确认为错误归属")
    return rows


def confirmed_42() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, (item, field, extracted, source_values, page) in enumerate(
        CAINIAO_ERRORS, start=1
    ):
        rows.append(
            {
                "finding_id": f"C42-CN-{index:02d}",
                "company": "菜鸟集团",
                "report": "招股书FY2021-FY2023",
                "statement": "合并资产负债表" if page == "466" else "合并现金流量表",
                "item": item,
                "column": field,
                "extracted_value": str(extracted),
                "source_expected_value": "NULL（原文破折号）",
                "source_page": page,
                "source_pdf": CAINIAO_PDF,
                "source_pdf_sha256": CAINIAO_PDF_SHA,
                "decision": "已确认真实抽取错误：跨列借值；空列必须为空值，不是零",
                "implementation_status": "待补列对齐修复；本轮仅建立归因台账",
            }
        )

    old_cells = read_yaml_cells(OLD_JDL)
    new_cells = read_yaml_cells(NEW_JDL)
    comparison_cells = jdl_review_comparison_cells(new_cells)
    removed = {
        key: value for key, value in old_cells.items() if key not in comparison_cells
    }
    for index, ((statement, item, column), value) in enumerate(
        sorted(removed.items()), start=1
    ):
        rows.append(
            {
                "finding_id": f"C42-JDL-{index:02d}",
                "company": "京东物流",
                "report": "FY2025年报",
                "statement": statement,
                "item": item,
                "column": column,
                "extracted_value": "NULL" if value is None else str(value),
                "source_expected_value": "不适用：该权益变动表行不属于资产负债表",
                "source_page": "物理110 / 印刷109",
                "source_pdf": JDL_PDF,
                "source_pdf_sha256": JDL_PDF_SHA,
                "decision": "已确认真实抽取错误：页区间/表识别将权益变动表误纳入资产负债表",
                "implementation_status": "已在JDL v2排除；5c84c81f同SHA CI 17/17",
            }
        )

    rows.append(
        {
            "finding_id": "C42-BABA-01",
            "company": "阿里巴巴",
            "report": "FY2023年报",
            "statement": "合并利润表",
            "item": "商譽減值",
            "column": "上期发生额",
            "extracted_value": "NULL",
            "source_expected_value": "-25141",
            "source_page": "38",
            "source_pdf": BABA_PDF,
            "source_pdf_sha256": BABA_PDF_SHA,
            "decision": "已确认真实抽取错误：FY2022比较列漏抽",
            "implementation_status": "待实现方修订并回归",
        }
    )
    if len(rows) != 42:
        raise ValueError(f"已确认异常应为42格，实际{len(rows)}格")
    return rows


def suspicion_groups() -> list[dict[str, str]]:
    groups = [
        (
            "S109-BABA-FY2020-CURRENT",
            "BABA FY2020资产负债表current列语义",
            36,
            "current列定义与begin重复关系不清",
        ),
        (
            "S109-ALI-CASH-SCOPE",
            "阿里七份报告现金流行名范围不完整",
            56,
            "数值可对照；名称漏写受限现金与应收托管资金范围",
        ),
        (
            "S109-ALI-EQUITY-CURRENT",
            "阿里股权证券及其他投资流动限定缺失",
            15,
            "流动/非流动同名项目需带限定；与BABA FY2020一格重叠",
        ),
        (
            "S109-CAINIAO-NONCURRENT",
            "菜鸟非流动科目限定缺失",
            10,
            "五类同名流动/非流动项目需回原页判定",
        ),
        (
            "S109-JDL-ATTRIBUTION",
            "JDL利润与综合收益归属范围不明",
            4,
            "包含在JDL 200个不可完整核验格内，不重复计总数",
        ),
    ]
    reconstructed_counts = {
        "S109-BABA-FY2020-CURRENT": 28,
        "S109-ALI-CASH-SCOPE": 56,
        "S109-ALI-EQUITY-CURRENT": 14,
        "S109-CAINIAO-NONCURRENT": 10,
        "S109-JDL-ATTRIBUTION": 4,
    }
    raw_total = sum(group[2] for group in groups)
    reconstructed_total = sum(reconstructed_counts.values())
    unique_cells = 111
    delta = unique_cells - 109
    return [
        {
            "group_id": group_id,
            "issue_group": title,
            "reported_cell_count": str(count),
            "reconstructed_candidate_count": str(reconstructed_counts[group_id]),
            "reported_minus_reconstructed": str(count - reconstructed_counts[group_id]),
            "exact_cell_membership": f"见suspected-109-cell-candidates-v1.csv；该组可枚举{reconstructed_counts[group_id]}格，候选集仍待逐格裁决",
            "source_ref": "docs/80_reviews/ai-cross-review/results/adjudication.md §三",
            "overlap_note": _,
            "arithmetic_reconciliation": f"裁决组计数合计{raw_total}；底层bundle可枚举{reconstructed_total}条；扣重复1格后唯一111；与总表109差{delta}格",
            "status": "candidate_members_reconstructed_two_cell_gap_open",
        }
        for group_id, title, count, _ in groups
    ]


def suspicion_candidates() -> list[dict[str, str]]:
    if not SUSPECTED_SNAPSHOT.is_file():
        raise FileNotFoundError(f"缺少疑点候选快照：{SUSPECTED_SNAPSHOT}")
    grouped: dict[tuple[str, str, str, str, str, str], dict[str, str]] = {}
    with SUSPECTED_SNAPSHOT.open(encoding="utf-8", newline="") as stream:
        for source in csv.DictReader(stream):
            key = (
                source["company"],
                source["report"],
                source["statement"],
                source["item"],
                source["column"],
                source["candidate_value"],
            )
            if key not in grouped:
                grouped[key] = {
                    "company": source["company"],
                    "report": source["report"],
                    "statement": source["statement"],
                    "item": source["item"],
                    "column": source["column"],
                    "candidate_value": source["candidate_value"],
                    "candidate_groups": source["group_id"],
                    "source_bundles": source["source_bundle"],
                    "source_bundle_sha256s": source["source_bundle_sha256"],
                    "status": "candidate_not_adjudicated",
                }
            else:
                entry = grouped[key]
                if source["group_id"] not in entry["candidate_groups"].split(";"):
                    entry["candidate_groups"] += ";" + source["group_id"]
                if source["source_bundle"] not in entry["source_bundles"].split(";"):
                    entry["source_bundles"] += ";" + source["source_bundle"]
                    entry["source_bundle_sha256s"] += (
                        ";" + source["source_bundle_sha256"]
                    )
    rows = []
    for index, row in enumerate(grouped.values(), start=1):
        row["candidate_id"] = f"S109-CAND-{index:03d}"
        row["status"] = (
            "excess_two_vs_FY2020_material_count_unresolved"
            if row["report"] == "BABA_FY2020_annual_results"
            and row["item"] == "股權證券及其他投資"
            and row["column"] in {"value_begin", "value_end"}
            else "candidate_not_adjudicated"
        )
        rows.append(row)
    if len(rows) != 111:
        raise ValueError(f"应重建111个唯一疑点候选格，实际{len(rows)}格")
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"拒绝写空台账：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot-source", type=Path, help="从本地忽略目录评审bundle冻结JDL 222格输入"
    )
    parser.add_argument(
        "--snapshot-suspicion-sources",
        type=Path,
        help="从本地忽略目录评审bundle冻结109疑点候选单元格输入",
    )
    args = parser.parse_args()
    if args.snapshot_source:
        count = snapshot_bundle(args.snapshot_source)
        print(f"JDL输入快照已冻结：{count}格 -> {SNAPSHOT.relative_to(ROOT)}")
    if args.snapshot_suspicion_sources:
        count = snapshot_suspicion_sources(args.snapshot_suspicion_sources)
        print(
            f"109疑点候选输入快照已冻结：{count}条分组候选 -> {SUSPECTED_SNAPSHOT.relative_to(ROOT)}"
        )
    if not SNAPSHOT.is_file():
        raise FileNotFoundError(f"缺少JDL评审输入快照：{SNAPSHOT}")
    jdl_rows = jdl_ledger()
    confirmed_rows = confirmed_42()
    group_rows = suspicion_groups()
    candidate_rows = suspicion_candidates()
    write_csv(LEDGER_DIR / "jdl-222-cell-reconciliation-v1.csv", jdl_rows)
    write_csv(LEDGER_DIR / "confirmed-42-exceptions-v1.csv", confirmed_rows)
    write_csv(LEDGER_DIR / "suspected-109-group-reconciliation-v1.csv", group_rows)
    write_csv(LEDGER_DIR / "suspected-109-cell-candidates-v1.csv", candidate_rows)
    statuses = {row["status"] for row in jdl_rows}
    status_counts = {
        status: sum(row["status"] == status for row in jdl_rows) for status in statuses
    }
    print(
        f"JDL格数={len(jdl_rows)}；"
        f"JDL已确认错误归属={status_counts.get('confirmed_wrong_statement_attribution', 0)}；"
        f"源行已核验={status_counts.get('source_line_value_verified', 0)}；"
        f"源空值已核验={status_counts.get('source_line_blank_verified', 0)}；"
        f"表级归属待裁决={status_counts.get('source_line_verified_statement_boundary_unresolved', 0)}"
    )
    print(
        f"已确认异常={len(confirmed_rows)}；存疑组={len(group_rows)}；唯一候选格={len(candidate_rows)}；较109摘要多2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
