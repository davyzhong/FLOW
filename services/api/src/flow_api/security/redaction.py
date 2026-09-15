"""S01 §8.3 确定性 redact：审计自由文本的末端防线。

算法顺序冻结（不得交换）：NFC → CRLF/CR→LF → 去 C0/C1（留 LF/TAB）→
凭证 → 邮箱 → 手机号 → 连续 8 位以上数字 → 按 code point 截 256 →
utf8_bytes + sha256。pattern 与规格逐字节一致；输入非 str 即
AuditRedactionFailure（writer rollback → 503，不得保存原文）。
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

CREDENTIAL_RE = re.compile(
    r"(?i)(?:\bauthorization\s*:\s*)?(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]+"
    r"|\b(?:api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}"
    r"|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
)
EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{8,}(?!\d)")

_MAX_CODEPOINTS = 256


class AuditRedactionFailure(RuntimeError):
    """输入不可 redact（非 str 等）→ 审计写入失败，fail closed。"""


@dataclass(frozen=True)
class RedactedText:
    text: str
    utf8_bytes: int
    sha256: str


def _strip_control_chars(value: str) -> str:
    return "".join(
        ch
        for ch in value
        if ch in ("\n", "\t")
        or not (unicodedata.category(ch) == "Cc" or unicodedata.category(ch) == "Cf")
    )


def redact_audit_text(value: str) -> RedactedText:
    if not isinstance(value, str):
        raise AuditRedactionFailure("redact 输入必须是 str")
    try:
        normalized = unicodedata.normalize("NFC", value)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        normalized = _strip_control_chars(normalized)
        normalized = CREDENTIAL_RE.sub("[REDACTED_TOKEN]", normalized)
        normalized = EMAIL_RE.sub("[REDACTED_EMAIL]", normalized)
        normalized = PHONE_RE.sub("[REDACTED_PHONE]", normalized)
        normalized = LONG_NUMBER_RE.sub("[REDACTED_NUMBER]", normalized)
        truncated = normalized[:_MAX_CODEPOINTS]
    except Exception as error:  # noqa: BLE001 - 任何正则/规范化异常都 fail closed
        raise AuditRedactionFailure(f"redact 失败: {error}") from error
    encoded = truncated.encode("utf-8")
    return RedactedText(
        text=truncated,
        utf8_bytes=len(encoded),
        sha256=hashlib.sha256(encoded).hexdigest(),
    )


__all__ = ["AuditRedactionFailure", "RedactedText", "redact_audit_text"]
