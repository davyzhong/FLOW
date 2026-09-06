"""公开财报抽取统一适配接口（B02）。

三个公司适配器（A 股表格版式、港股繁体年报、业绩公告简表）共享同一入口：
- `extract_statements(content, adapter_id=None)` 自动选择得分最高的适配器；
- 得分不足时抛出 `UnsupportedLayoutError`（未知版式显式降级，不猜测）；
- 抽取结果携带页定位、单位、结构化勾稽检查与警告；数值为披露原文原始值。

原 P5 脚本（scripts/p5_extract_*.py）改为本模块的薄 CLI 入口，行为不变。
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from typing import Any, Protocol

import pdfplumber

MIN_ADAPTER_SCORE = 2

HEADER_KEYS = ("项目", "期末余额", "期初余额", "本期发生额", "上期发生额")


class UnsupportedLayoutError(ValueError):
    """未知版式：没有任何适配器达到支持阈值。"""

    def __init__(self, scores: dict[str, int]) -> None:
        super().__init__(f"未知财报版式，显式降级（各适配器得分：{scores}）")
        self.scores = scores


@dataclass(frozen=True, slots=True)
class ExtractionCheck:
    label: str
    left: Any
    right: Any
    status: str  # 一致 / 不一致 / 披露缺失/未取到


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    adapter_id: str
    unit_note: str
    statements: dict[str, list[dict[str, Any]]]
    checks: tuple[ExtractionCheck, ...]
    warnings: tuple[str, ...]
    page_count: int
    source_sha256: str

    @property
    def checks_passed(self) -> bool:
        return all(check.status == "一致" for check in self.checks)


class StatementExtractor(Protocol):
    adapter_id: str

    def supports(self, pages: list[str]) -> int:
        """对页文本打分；>= MIN_ADAPTER_SCORE 视为可用。"""

    def extract(self, content: bytes) -> ExtractionResult:
        """执行抽取并返回统一结果。"""


def _norm_item(name: str) -> str:
    return re.sub(r"\s+", "", name or "")


_DASH_VARIANTS = "－—−‒–"


def _canon(name: str) -> str:
    """行名归一：去空白、统一括号与破折号变体、去掉「（或股东权益）」。"""

    s = _norm_item(name).replace("（", "(").replace("）", ")")
    for dash in _DASH_VARIANTS:
        s = s.replace(dash, "-")
    return s.replace("(或股东权益)", "")


def _g(items: list[dict[str, Any]], col: str, *names: str) -> Any:
    """按归一名查找行值（容忍 （或股东权益）/破折号/括号变体与补充后缀）。"""

    canons = {_canon(n) for n in names}
    for item in items:
        canon = _canon(item["item"])
        if canon in canons or any(canon.startswith(c + "(") for c in canons):
            value = item.get(col)
            if value is not None:
                return value
    return None


def _parse_num(cell: Any) -> Any:
    if cell is None:
        return None
    s = str(cell).strip().replace(",", "")
    if s in ("", "-", "—"):
        return None
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    return float(s) if "." in s else int(s)


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _page_texts(content: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return [(page.extract_text() or "") for page in pdf.pages]


def _find(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for item in items:
        if item["item"] == name:
            return item
    return None


def _check(diffs: list[ExtractionCheck], label: str, left: Any, right: Any) -> None:
    if left is None or right is None:
        diffs.append(ExtractionCheck(label, left, right, "披露缺失/未取到"))
        return
    try:
        equal = Decimal(str(left)) == Decimal(str(right))
    except ArithmeticError:
        equal = left == right
    diffs.append(ExtractionCheck(label, left, right, "一致" if equal else "不一致"))


# ---------------------------------------------------------------------------
# A 股表格版式适配器（顺丰/圆通等 A 股季报、年报；表头特征定位，不硬编码页码）
# ---------------------------------------------------------------------------

# 节锚 → 列语义；锚文本须整行精确匹配（规避目录页条目）
_A_SECTIONS = {
    "合并资产负债表": ("期末余额", "期初余额"),
    "合并利润表": ("本期发生额", "上期发生额"),
    "合并现金流量表": ("本期发生额", "上期发生额"),
}


class AShareTableExtractor:
    adapter_id = "cn_ashare_table"

    def supports(self, pages: list[str]) -> int:
        score = 0
        head = "\n".join(pages[:5])
        if "证券代码" in head:
            score += 1
        if re.search(r"合并(资产负债表|利润表|现金流量表)", "\n".join(pages)):
            score += 2
        return score

    def _extract_tables(self, content: bytes) -> dict[str, list[tuple[Any, int]]]:
        """按节锚/表头归属行项目：兼容表头在表格内（顺丰）与表头为文本行（圆通）。"""

        sections: dict[str, list[tuple[Any, int]]] = {}
        current: str | None = None
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page_no, page in enumerate(pdf.pages, start=1):
                anchors = [
                    (line["top"], _norm_item(line["text"]))
                    for line in page.extract_text_lines()
                    if _norm_item(line["text"]) in _A_SECTIONS
                ]
                tables = [(tbl.bbox[1], tbl.extract()) for tbl in page.find_tables()]
                events: list[tuple[Any, str, Any]] = sorted(
                    [(top, "anchor", payload) for top, payload in anchors]
                    + [(top, "table", payload) for top, payload in tables],
                    key=lambda event: event[0],
                )
                for _top, kind, payload in events:
                    if kind == "anchor":
                        current = str(payload)
                        sections.setdefault(current, [])
                        continue
                    table = payload
                    if not table:
                        continue
                    header = [_norm_item(c) for c in table[0]]
                    is_header = any(k in header for k in ("期末余额", "本期发生额")) and (
                        "项目" in header[0]
                    )
                    body = table[1:] if is_header else table
                    if is_header:
                        if "期末余额" in header:
                            current = "合并资产负债表"
                        elif any(
                            _norm_item(row[0]) == "一、营业总收入"
                            for row in body[:3]
                            if row and row[0]
                        ):
                            current = "合并利润表"
                        else:
                            current = "合并现金流量表"
                        sections.setdefault(current, [])
                    if current is None:
                        continue
                    for row in body:
                        if row and row[0] and _norm_item(row[0]) and _looks_like_data_row(row):
                            sections[current].append((row, page_no))
        return sections

    def _to_statements(
        self, sections: dict[str, list[tuple[Any, int]]]
    ) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for key, rows in sections.items():
            cols = _A_SECTIONS[key]
            items = []
            for row, page_no in rows:
                items.append(
                    {
                        "item": _norm_item(row[0]),
                        cols[0]: _parse_num(row[1] if len(row) > 1 else None),
                        cols[1]: _parse_num(row[2] if len(row) > 2 else None),
                        "page": page_no,
                    }
                )
            out[key] = items
        return out

    def _reconcile(self, st: dict[str, list[dict[str, Any]]]) -> list[ExtractionCheck]:
        diffs: list[ExtractionCheck] = []
        bs = st["合并资产负债表"]
        for col in ("期末余额", "期初余额"):
            g = partial(_g, bs, col)
            _check(diffs, f"资产总计=流动资产合计+非流动资产合计 [{col}]",
                   g("资产总计"),
                   (_dec(g("流动资产合计")) or 0) + (_dec(g("非流动资产合计")) or 0))
            _check(diffs, f"负债合计=流动负债合计+非流动负债合计 [{col}]",
                   g("负债合计"),
                   (_dec(g("流动负债合计")) or 0) + (_dec(g("非流动负债合计")) or 0))
            _check(diffs, f"资产总计=负债合计+所有者权益合计 [{col}]",
                   g("资产总计"),
                   (_dec(g("负债合计")) or 0) + (_dec(g("所有者权益合计", "股东权益合计")) or 0))
            _check(diffs, f"负债和所有者权益总计=资产总计 [{col}]",
                   g("负债和所有者权益总计", "负债和股东权益总计"), g("资产总计"))
            _check(diffs, f"所有者权益合计=归母+少数股东 [{col}]",
                   g("所有者权益合计", "股东权益合计"),
                   (_dec(g("归属于母公司所有者权益合计", "归属于母公司股东权益合计")) or 0)
                   + (_dec(g("少数股东权益")) or 0))
        if "合并利润表" not in st:
            return diffs
        is_ = st["合并利润表"]
        for col in ("本期发生额", "上期发生额"):
            g = partial(_g, is_, col)
            _check(diffs, f"净利润=归母+少数股东损益 [{col}]",
                   g("五、净利润（净亏损以“－”号填列）"),
                   (_dec(g("1.归属于母公司所有者的净利润", "1.归属于母公司股东的净利润")) or 0)
                   + (_dec(g("2.少数股东损益")) or 0))
            _check(diffs, f"利润总额=营业利润+营业外收入-营业外支出 [{col}]",
                   g("四、利润总额（亏损总额以“－”号填列）"),
                   (_dec(g("三、营业利润（亏损以“－”号填列）")) or 0)
                   + (_dec(g("加：营业外收入")) or 0) - (_dec(g("减：营业外支出")) or 0))
        if "合并现金流量表" not in st:
            return diffs
        cf = st["合并现金流量表"]
        for col in ("本期发生额", "上期发生额"):
            g = partial(_g, cf, col)
            _check(diffs, f"经营净额=流入小计-流出小计 [{col}]",
                   g("经营活动产生的现金流量净额"),
                   (_dec(g("经营活动现金流入小计")) or 0) - (_dec(g("经营活动现金流出小计")) or 0))
            _check(diffs, f"现金净增加额=经营+投资+筹资+汇率影响 [{col}]",
                   g("五、现金及现金等价物净增加额"),
                   (_dec(g("经营活动产生的现金流量净额")) or 0)
                   + (_dec(g("投资活动产生的现金流量净额")) or 0)
                   + (_dec(g("筹资活动产生的现金流量净额")) or 0)
                   + (_dec(g("四、汇率变动对现金及现金等价物的影响")) or 0))
            _check(diffs, f"期末现金=期初+净增加额 [{col}]",
                   g("六、期末现金及现金等价物余额"),
                   (_dec(g("加：期初现金及现金等价物余额")) or 0)
                   + (_dec(g("五、现金及现金等价物净增加额")) or 0))
        return diffs

    def extract(self, content: bytes) -> ExtractionResult:
        statements = self._to_statements(self._extract_tables(content))
        warnings: list[str] = []
        missing = {"合并资产负债表", "合并利润表", "合并现金流量表"} - set(statements)
        if missing:
            warnings.append(f"未定位到报表：{'、'.join(sorted(missing))}")
        return ExtractionResult(
            adapter_id=self.adapter_id,
            unit_note="人民币千元（每股收益为元）",
            statements=statements,
            checks=tuple(self._reconcile(statements)) if not missing else (),
            warnings=tuple(warnings),
            page_count=len(_page_texts(content)),
            source_sha256=hashlib.sha256(content).hexdigest(),
        )


# ---------------------------------------------------------------------------
# 港股繁体年报适配器（京东物流版式：繁体、功能法列报、附注号中缀、括号负数）
# ---------------------------------------------------------------------------

_HK_PAGES = {
    "合并利润表": (106, "合併損益表"),
    "合并资产负债表": (108, "合併財務狀況表"),
    "合并现金流量表": (112, "合併現金流量表"),
}
_HK_NUM = r"\(?-?[\d][\d,]*\)?"


class StatementExtractionError(ValueError):
    """锚点缺失或版式与适配器不符（锚点缺失即失败，不硬编码数字）。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _hk_parse_line(line: str) -> tuple[str, Any, Any] | None:
    tokens = line.split()
    nums: list[str | None] = []
    while tokens:
        tok = tokens[-1]
        if re.fullmatch(_HK_NUM, tok):
            nums.insert(0, tok)
            tokens.pop()
        elif tok in ("—", "-"):
            nums.insert(0, None)
            tokens.pop()
        else:
            break
    if not nums or not tokens:
        return None
    if (
        len(nums) > 2
        and nums[0] is not None
        and re.fullmatch(r"\d{1,3}", nums[0])
        and "," not in nums[0]
    ):
        nums = nums[1:]  # 附注号识别
    if len(nums) > 2:
        nums = nums[-2:]
    name = "".join(tokens)
    if not name or re.fullmatch(r"[\d.,()]+", name):
        return None

    def val(tok: str | None) -> Any:
        if tok is None:
            return None
        negative = tok.startswith("(")
        digits = tok.strip("()").replace(",", "")
        number = float(digits) if "." in digits else int(digits)
        return -number if negative else number

    current = val(nums[-2]) if len(nums) >= 2 else val(nums[-1])
    prior = val(nums[-1]) if len(nums) >= 2 else None
    if current is None and prior is None:
        return None
    return name, current, prior


class HkTraditionalExtractor:
    adapter_id = "hk_traditional_text"

    def supports(self, pages: list[str]) -> int:
        score = 0
        joined = "\n".join(pages)
        if re.search(r"合併(損益表|財務狀況表|現金流量表)", joined):
            score += 2
        if re.search(r"(股份代號|Stock Code)", "\n".join(pages[:5])):
            score += 1
        return score

    def _locate_start(self, pages: list[str], hint: int, anchor: str) -> int:
        for pno in range(max(0, hint - 6), min(len(pages), hint + 5)):
            lines = pages[pno].split("\n")
            if any(anchor in line for line in lines[:4]):
                return pno
        raise StatementExtractionError(
            "anchor_missing", f"未在提示页 {hint}±5 内定位到「{anchor}」页首标题"
        )

    def _extract_statement(
        self, pages: list[str], start_hint: int, anchor: str, end_page: int | None = None
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        start = self._locate_start(pages, start_hint, anchor)
        stop = end_page or (start + 5)
        for pno in range(start, min(stop, len(pages))):
            for line in pages[pno].split("\n"):
                if "年度報告" in line or "人民幣元" in line:
                    continue
                parsed = _hk_parse_line(line)
                if parsed:
                    name, current, prior = parsed
                    items.append(
                        {"item": name, "本期发生额": current, "上期发生额": prior, "page": pno + 1}
                    )
        return items

    @staticmethod
    def _to_balance_columns(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "item": it["item"],
                "期末余额": it["本期发生额"],
                "期初余额": it["上期发生额"],
                "page": it.get("page"),
            }
            for it in items
        ]

    def _reconcile(self, st: dict[str, list[dict[str, Any]]]) -> list[ExtractionCheck]:
        diffs: list[ExtractionCheck] = []
        if "合并利润表" not in st:
            return diffs
        is_ = st["合并利润表"]
        bs = st["合并资产负债表"]
        cf = st["合并现金流量表"]
        for col in ("本期发生额", "上期发生额"):
            def g(n: str, col: str = col) -> Any:
                return (_find(is_, n) or {}).get(col)
            _check(diffs, f"毛利=收入-營業成本 [{col}]", g("毛利"),
                   (g("收入") or 0) + (g("營業成本") or 0))
            _check(diffs, f"除稅前利潤逐項加總 [{col}]", g("除稅前利潤"),
                   (g("毛利") or 0) + (g("銷售及市場推廣開支") or 0) + (g("研發開支") or 0)
                   + (g("一般及行政開支") or 0) + (g("其他收入、收益╱（虧損）淨額") or 0)
                   + (g("出售產業園的收益") or 0) + (g("財務收入") or 0) + (g("財務成本") or 0)
                   + (g("金融資產減值損失（包括減值損失轉回）") or 0)
                   + (g("應佔聯營企業及合營企業損益") or 0))
            _check(diffs, f"年度利潤=除稅前+所得稅 [{col}]", g("年度利潤"),
                   (g("除稅前利潤") or 0) + (g("所得稅開支") or 0))
            _check(diffs, f"年度利潤=本公司所有者+非控制性權益 [{col}]", g("年度利潤"),
                   (g("本公司所有者") or 0) + (g("非控制性權益") or 0))
        for col in ("期末余额", "期初余额"):
            def g(n: str, col: str = col) -> Any:
                return (_find(bs, n) or {}).get(col)
            _check(diffs, f"資產總額=非流動+流動 [{col}]", g("資產總額"),
                   (g("非流動資產總額") or 0) + (g("流動資產總額") or 0))
            _check(diffs, f"負債總額=非流動+流動 [{col}]", g("負債總額"),
                   (g("非流動負債總額") or 0) + (g("流動負債總額") or 0))
            _check(diffs, f"權益總額=歸母+非控制性 [{col}]", g("權益總額"),
                   (g("歸屬於本公司所有者的權益") or 0) + (g("非控制性權益") or 0))
            _check(diffs, f"權益及負債總額=權益+負債=資產 [{col}]", g("權益及負債總額"),
                   (g("權益總額") or 0) + (g("負債總額") or 0))
            _check(diffs, f"資產總額=權益及負債總額 [{col}]", g("資產總額"),
                   g("權益及負債總額"))
        for col in ("本期发生额", "上期发生额"):
            def g(n: str, col: str = col) -> Any:
                return (_find(cf, n) or {}).get(col)
            _check(diffs, f"現金淨變動=經營+投資+融資 [{col}]",
                   g("現金及現金等價物（減少）╱增加淨額"),
                   (g("經營活動所得現金淨額") or 0) + (g("投資活動所用現金淨額") or 0)
                   + (g("融資活動所用現金淨額") or 0))
            _check(diffs, f"年末現金=年初+淨變動+外匯 [{col}]", g("年末現金及現金等價物"),
                   (g("年初現金及現金等價物") or 0)
                   + (g("現金及現金等價物（減少）╱增加淨額") or 0)
                   + (g("外匯匯率變動對現金及現金等價物的影響") or 0))
            _check(diffs, f"財狀表現金=現金流量表年末 [{col}]",
                   (_find(bs, "現金及現金等價物") or {}).get(
                       "期末余额" if col == "本期发生额" else "期初余额"),
                   g("年末現金及現金等價物"))
        return diffs

    def extract(self, content: bytes) -> ExtractionResult:
        pages = _page_texts(content)
        statements = {
            "合并利润表": self._extract_statement(pages, *_HK_PAGES["合并利润表"], end_page=107),
            "合并资产负债表": self._to_balance_columns(
                self._extract_statement(pages, *_HK_PAGES["合并资产负债表"], end_page=110)
            ),
            "合并现金流量表": self._extract_statement(
                pages, *_HK_PAGES["合并现金流量表"], end_page=114
            ),
        }
        return ExtractionResult(
            adapter_id=self.adapter_id,
            unit_note="人民币千元（每股收益为元）",
            statements=statements,
            checks=tuple(self._reconcile(statements)),
            warnings=(),
            page_count=len(pages),
            source_sha256=hashlib.sha256(content).hexdigest(),
        )


# ---------------------------------------------------------------------------
# 业绩公告简表适配器（腾讯版式：简明综合收益表 + IFRS→Non-IFRS 调节表）
# ---------------------------------------------------------------------------

_TENCENT_PARENUM = r"-?[\d,]+(?:\.\d+)?| \([-\d,]+\)"
_TENCENT_LABELS = [
    "收入", "增值服务", "营销服务", "金融科技及企业服务", "其他", "收入成本", "毛利",
    "销售及市场推广开支", "一般及行政开支", "其他收益/（亏损）净额", "经营盈利",
    "投资收益/（亏损）净额及其他", "利息收入", "财务成本",
    "分占联营公司及合营公司盈利/（亏损）净额", "除税前盈利", "所得税开支", "期内盈利",
    "本公司权益持有人", "非控制性权益",
]


def _parse_signed(s: str) -> Any:
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        digits = s.strip("()").replace(",", "")
        number = float(digits) if "." in digits else int(digits)
        return -number
    digits = s.replace(",", "")
    return float(digits) if "." in digits else int(digits)


class ResultsAnnouncementExtractor:
    adapter_id = "hk_results_announcement"

    def supports(self, pages: list[str]) -> int:
        joined = "\n".join(pages)
        score = 0
        if "简明综合收益表" in joined:
            score += 2
        if "非国际财务报告准则" in joined or "Non-IFRS" in joined:
            score += 1
        return score

    def extract(self, content: bytes) -> ExtractionResult:
        pages = _page_texts(content)
        is_page = next(
            (i for i, text in enumerate(pages) if "简明综合收益表" in text), None
        )
        if is_page is None:
            raise StatementExtractionError("anchor_missing", "未定位到简明综合收益表页")

        is_lines = pages[is_page].split("\n")

        def grab3(label: str) -> list[Any]:
            for ln in is_lines:
                if ln.strip().split(" ")[0] == label:
                    found = re.findall(_TENCENT_PARENUM, ln)
                    if len(found) >= 3:
                        return [_parse_signed(x) for x in found[:3]]
            raise StatementExtractionError("anchor_missing", f"锚点未取到：{label}")

        stmt = {label: grab3(label) for label in _TENCENT_LABELS}

        checks: list[ExtractionCheck] = []
        seg_sum = sum(stmt[s][0] for s in ["增值服务", "营销服务", "金融科技及企业服务", "其他"])
        _check(checks, "收入分部加总=营业收入", seg_sum, stmt["收入"][0])
        _check(checks, "毛利=收入+收入成本", stmt["收入"][0] + stmt["收入成本"][0], stmt["毛利"][0])
        _check(checks, "期内盈利=归母+非控制",
               stmt["本公司权益持有人"][0] + stmt["非控制性权益"][0], stmt["期内盈利"][0])

        rec_candidates = [
            ln.strip()
            for text in pages
            for ln in text.split("\n")
            if ln.strip().startswith("本公司权益持有人应占盈利")
        ]
        rec_line = next(
            (ln for ln in rec_candidates if len(re.findall(_TENCENT_PARENUM, ln)) == 9),
            None,
        )
        if rec_line is None:
            raise StatementExtractionError("anchor_missing", "未定位到 Non-IFRS 调节表归母行")
        vals = [_parse_signed(x) for x in re.findall(_TENCENT_PARENUM, rec_line)]
        if len(vals) != 9:
            raise StatementExtractionError(
                "anchor_missing", f"调节表列数异常：{len(vals)}（预期 9）"
            )
        reported, adjustments, non_ifrs = vals[0], vals[1:8], vals[8]
        _check(checks, "IFRS→Non-IFRS 调节链闭合", reported + sum(adjustments), non_ifrs)
        _check(checks, "调节表归母=收益表归母", reported, stmt["本公司权益持有人"][0])

        items = [
            {
                "item": label,
                "本期发生额": vals3[0],
                "上期发生额": vals3[1],
                "page": is_page + 1,
            }
            for label, vals3 in stmt.items()
        ]
        return ExtractionResult(
            adapter_id=self.adapter_id,
            unit_note="人民币百万元",
            statements={"合并利润表": items},
            checks=tuple(checks),
            warnings=("业绩公告为简表：无资产负债全表/现金流量表/权益变动表（披露范围如此）",),
            page_count=len(pages),
            source_sha256=hashlib.sha256(content).hexdigest(),
        )


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------

_EXTRACTORS: dict[str, StatementExtractor] = {
    extractor.adapter_id: extractor
    for extractor in (
        AShareTableExtractor(),
        HkTraditionalExtractor(),
        ResultsAnnouncementExtractor(),
    )
}


def extract_statements(content: bytes, *, adapter_id: str | None = None) -> ExtractionResult:
    """统一抽取入口：显式指定适配器，或按页文本自动选择得分最高者。

    所有适配器得分均低于阈值时抛出 UnsupportedLayoutError（未知版式显式降级）。
    """

    if adapter_id is not None:
        extractor = _EXTRACTORS.get(adapter_id)
        if extractor is None:
            raise StatementExtractionError(
                "unknown_adapter", f"未知适配器：{adapter_id}（可用：{sorted(_EXTRACTORS)}）"
            )
        return extractor.extract(content)

    pages = _page_texts(content)
    scores = {aid: ex.supports(pages) for aid, ex in _EXTRACTORS.items()}
    best_id = max(scores, key=lambda aid: scores[aid])
    if scores[best_id] < MIN_ADAPTER_SCORE:
        raise UnsupportedLayoutError(scores)
    return _EXTRACTORS[best_id].extract(content)


__all__ = [
    "AShareTableExtractor",
    "ExtractionCheck",
    "ExtractionResult",
    "HkTraditionalExtractor",
    "MIN_ADAPTER_SCORE",
    "ResultsAnnouncementExtractor",
    "StatementExtractionError",
    "StatementExtractor",
    "UnsupportedLayoutError",
    "extract_statements",
]


def _looks_like_data_row(row: Any) -> bool:
    """报表行项目：项目名 + 数值/空单元格；长文本单元格（股东说明等非报表表）排除。"""

    for cell in row[1:]:
        if cell is None:
            continue
        s = str(cell).strip()
        if s == "":
            continue
        if _parse_num(s) is None and s not in ("-", "—"):
            return False
    return True
