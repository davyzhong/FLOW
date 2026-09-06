"""公开财报上传与来源登记（B01）。

职责：格式/大小校验、文本 PDF 探针（扫描件可解释拒绝）、公司/期间识别候选、
内容寻址不可变存储与幂等登记。首批仅支持文本 PDF；不支持扫描件与 OCR。
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass

import pdfplumber
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import StatementSource
from flow_api.infrastructure.object_store import ObjectStore

MIN_TEXT_CHARS = 200
PROBE_PAGES = 3

_STOCK_A = re.compile(r"证券代码[:：]?\s*(\d{6})")
_STOCK_HK = re.compile(r"(?:股份代號|股份代号|Stock Code)[:：]?\s*(\d{4,5})", re.IGNORECASE)
_COMPANY = re.compile(r"([一-龥（）()A-Za-z]{2,40}?(?:股份有限公司|控股有限公司|有限公司))")
_COMPANY_SHORT = re.compile(r"证券简称[:：]?\s*([一-龥A-Za-z]+)")
_PERIOD_Q = re.compile(r"(20\d{2})\s*年\s*第?\s*([一二三四1-4])\s*季度报告")
_PERIOD_H1 = re.compile(r"(20\d{2})\s*年\s*(?:半年度|中期)报告")
_PERIOD_FY_CN = re.compile(r"(20\d{2})\s*年\s*年度报告")
_PERIOD_FY_EN = re.compile(r"(?:FY\s*)?(20\d{2})\s*Annual Report", re.IGNORECASE)
_QUARTER_NAMES = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}


class StatementSourceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class SourceProbe:
    sha256: str
    size_bytes: int
    page_count: int
    text_chars: int
    company_candidate: str | None
    stock_code_candidate: str | None
    period_candidate: str | None
    report_kind_candidate: str | None


def _identify_candidates(text: str) -> dict[str, str | None]:
    company = None
    short = _COMPANY_SHORT.search(text)
    if short:
        company = short.group(1)
    if company is None:
        match = _COMPANY.search(text)
        if match:
            company = match.group(1)

    stock_code = None
    a_match = _STOCK_A.search(text)
    hk_match = _STOCK_HK.search(text)
    if a_match:
        stock_code = a_match.group(1)
    elif hk_match:
        stock_code = hk_match.group(1) + ".HK"

    period = None
    report_kind = None
    if match := _PERIOD_Q.search(text):
        quarter = _QUARTER_NAMES.get(match.group(2))
        if quarter:
            period = f"{match.group(1)}Q{quarter}"
            report_kind = "一季报" if quarter == 1 else ("中报" if quarter == 2 else "三季报")
    elif match := _PERIOD_H1.search(text):
        period = f"{match.group(1)}H1"
        report_kind = "中报"
    elif (match := _PERIOD_FY_CN.search(text)) or (match := _PERIOD_FY_EN.search(text)):
        period = f"FY{match.group(1)}"
        report_kind = "年报"

    return {
        "company_candidate": company,
        "stock_code_candidate": stock_code,
        "period_candidate": period,
        "report_kind_candidate": report_kind,
    }


def probe_statement_pdf(content: bytes, filename: str, *, max_bytes: int) -> SourceProbe:
    """格式与可解析性探针；任何不支持情形都以可解释错误拒绝。"""

    if not filename.lower().endswith(".pdf"):
        raise StatementSourceError(
            "unsupported_source_format",
            f"仅支持 PDF 财报原文（当前文件：{filename}）",
        )
    if not content.startswith(b"%PDF-"):
        raise StatementSourceError("invalid_pdf", "文件不是有效的 PDF（缺少 %PDF- 文件头）")
    if len(content) > max_bytes:
        raise StatementSourceError(
            "source_too_large",
            f"文件 {len(content)} 字节超过上限 {max_bytes} 字节",
        )
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_count = len(pdf.pages)
            text = "".join((page.extract_text() or "") for page in pdf.pages[:PROBE_PAGES])
    except Exception as error:
        raise StatementSourceError("invalid_pdf", f"PDF 无法解析：{error}") from error
    text_chars = len(text.strip())
    if text_chars < MIN_TEXT_CHARS:
        raise StatementSourceError(
            "scanned_pdf_unsupported",
            f"前 {PROBE_PAGES} 页仅提取到 {text_chars} 个字符，疑似扫描件；"
            "当前仅支持文本 PDF，不支持 OCR",
        )
    return SourceProbe(
        sha256=hashlib.sha256(content).hexdigest(),
        size_bytes=len(content),
        page_count=page_count,
        text_chars=text_chars,
        **_identify_candidates(text),
    )


class StatementSourceIntake:
    """登记公开财报原始文件：内容寻址存储 + 幂等数据库登记。"""

    def __init__(self, object_store: ObjectStore, *, max_bytes: int) -> None:
        self._object_store = object_store
        self._max_bytes = max_bytes

    def register(
        self, session: Session, *, content: bytes, filename: str
    ) -> tuple[StatementSource, bool]:
        """登记源文件；返回 (登记行, 是否新建)。同一 sha256 重复上传幂等。"""

        probe = probe_statement_pdf(content, filename, max_bytes=self._max_bytes)
        existing = session.scalar(
            select(StatementSource).where(StatementSource.sha256 == probe.sha256)
        )
        if existing is not None:
            return existing, False

        stored = self._object_store.put_immutable(content, filename)
        source = StatementSource(
            sha256=probe.sha256,
            object_key=stored.object_key,
            original_filename=filename,
            size_bytes=probe.size_bytes,
            page_count=probe.page_count,
            text_chars=probe.text_chars,
            status="registered",
            company_candidate=probe.company_candidate,
            stock_code_candidate=probe.stock_code_candidate,
            period_candidate=probe.period_candidate,
            report_kind_candidate=probe.report_kind_candidate,
        )
        session.add(source)
        session.flush()
        return source, True


__all__ = [
    "MIN_TEXT_CHARS",
    "SourceProbe",
    "StatementSourceError",
    "StatementSourceIntake",
    "probe_statement_pdf",
]
