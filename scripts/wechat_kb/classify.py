# -*- coding: utf-8 -*-
"""财经/经营管理相关性分类：关键词加权打分，输出类别与得分。"""

from __future__ import annotations

import re

# 强信号：直接对应 FLOW 的财务/经营分析主题（标题命中权重更高）
STRONG_KEYWORDS = [
    "财务", "财经", "会计", "管理会计", "经营分析", "财务分析", "成本分析", "财报",
    "毛利", "净利", "利润", "现金流", "资产负债", "利润表", "预算", "决算",
    "应收", "应付", "账款", "报表", "驾驶舱", "指标", "KPI", "kpi",
    "复盘", "降本", "增效", "增收", "ROI", "roi", "资金", "税务", "报销",
    "月度分析", "年度分析", "经营报告", "分析报告", "经营", "本量利", "盈亏",
    "杜邦", "FinanceBP", "财务BP", "业务财务", "经营管理", "稽核", "对账",
    "收入", "营收", "毛利率", "回款", "存货", "固定资产", "折旧", "融资",
]
# 弱信号：泛管理/数据主题
WEAK_KEYWORDS = [
    "数据分析", "Excel", "excel", "PPT", "ppt", "汇报", "总结", "模板", "效率",
    "管理", "运营", "业务", "增长", "战略", "绩效", "薪酬", "风控", "数字化",
    "AI", "智能化", "SaaS", "看板", "数据", "方法论", "职场", "思维", "模型",
    "流程", "SOP", "sop", "复盘会", "周报", "月报", "年报",
]
# 负信号：明显无关时抵扣
NEGATIVE_KEYWORDS = [
    "招聘", "广告", "红包", "抽奖", "荐股", "小说", "养生", "星座", "八卦",
]

CATEGORY_RULES = [
    ("财务分析", ["财务分析", "毛利", "净利", "利润", "报表", "现金流", "资产负债", "杜邦", "本量利", "盈亏", "财报"]),
    ("经营分析", ["经营分析", "经营", "复盘", "驾驶舱", "指标", "KPI", "kpi", "经营报告", "运营"]),
    ("预算与成本", ["预算", "成本", "降本", "费用", "决算", "回款", "应收", "应付"]),
    ("报告与汇报模板", ["PPT", "ppt", "模板", "汇报", "总结", "月报", "周报", "年报", "月度分析", "年度分析", "分析报告"]),
    ("数据方法与工具", ["数据分析", "Excel", "excel", "看板", "数据", "方法论", "模型", "AI", "智能化", "SOP", "sop"]),
]

RELEVANT_THRESHOLD = 3.0
BORDERLINE_THRESHOLD = 1.5


def _hits(text: str, keywords: list[str]) -> list[str]:
    found = []
    for kw in keywords:
        if kw in text:
            found.append(kw)
    return found


def classify(title: str, content_text: str) -> dict:
    title_hits_s = _hits(title, STRONG_KEYWORDS)
    body_hits_s = _hits(content_text, STRONG_KEYWORDS)
    title_hits_w = _hits(title, WEAK_KEYWORDS)
    body_hits_w = _hits(content_text, WEAK_KEYWORDS)
    neg_hits = _hits(title + content_text[:2000], NEGATIVE_KEYWORDS)

    score = (
        len(title_hits_s) * 3.0
        + len(body_hits_s) * 1.0
        + len(title_hits_w) * 1.0
        + len(body_hits_w) * 0.2
        - len(neg_hits) * 2.0
    )
    score = max(score, 0.0)

    categories = []
    for cat, kws in CATEGORY_RULES:
        if _hits(title + " " + content_text[:4000], kws):
            categories.append(cat)
    if not categories:
        categories = ["其他"]

    if score >= RELEVANT_THRESHOLD:
        relevance = "relevant"
    elif score >= BORDERLINE_THRESHOLD:
        relevance = "borderline"
    else:
        relevance = "excluded"

    return {
        "score": round(score, 1),
        "relevance": relevance,
        "categories": categories,
        "title_hits": sorted(set(title_hits_s + title_hits_w)),
        "negative_hits": neg_hits,
    }


def content_to_text(markdown: str) -> str:
    """粗略去掉 Markdown 语法，用于关键词统计。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", markdown)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*`|\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text
