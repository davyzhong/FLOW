"""导入模板定义与 Excel 生成（R1）。

模板列名即导入契约：用户按中文列名填数，校验引擎按同名列解析。
金额一律 Decimal 字符串处理，禁止 float。
"""

from __future__ import annotations

from io import BytesIO
from typing import Final

# 科目余额表：借贷平衡校验的核心模板
TRIAL_BALANCE_SHEET: Final = "科目余额表"
TRIAL_BALANCE_COLUMNS: Final[tuple[str, ...]] = (
    "会计期间",
    "科目编码",
    "科目名称",
    "科目类别",
    "方向",
    "期初余额",
    "本期借方发生额",
    "本期贷方发生额",
    "期末余额",
)
# 科目类别白名单：用于报表归属与驾驶舱指标映射
ACCOUNT_CATEGORIES: Final[tuple[str, ...]] = ("资产", "负债", "权益", "成本", "损益")
# 方向白名单：余额所在方向
DIRECTIONS: Final[tuple[str, ...]] = ("借", "贷")

# 利润表：多期损益
INCOME_STATEMENT_SHEET: Final = "利润表"
INCOME_STATEMENT_COLUMNS: Final[tuple[str, ...]] = (
    "会计期间",
    "项目",
    "本期金额",
    "本年累计金额",
)

# 银行流水（M3）：现金收付口径；余额连续性校验锚定数据完整性
BANK_STATEMENT_SHEET: Final = "银行流水"
BANK_STATEMENT_COLUMNS: Final[tuple[str, ...]] = (
    "交易日期",
    "摘要",
    "收入金额",
    "支出金额",
    "账户余额",
)
_DATE_PATTERN_ERROR: Final = "交易日期须为 YYYY-MM-DD 格式（如 2025-01-05）"

PERIOD_PATTERN_ERROR: Final = "会计期间须为 YYYY-MM 格式（如 2025-01）"

_SAMPLE_TRIAL_ROWS: Final[tuple[tuple[str, ...], ...]] = (
    ("2025-01", "1001", "库存现金", "资产", "借", "10000.00", "5000.00", "3000.00", "12000.00"),
    ("2025-01", "2001", "短期借款", "负债", "贷", "50000.00", "0.00", "0.00", "50000.00"),
)

_SAMPLE_INCOME_ROWS: Final[tuple[tuple[str, ...], ...]] = (
    ("2025-01", "营业收入", "", "100000.00", "100000.00"),
    ("2025-01", "营业成本", "", "60000.00", "60000.00"),
)

_SAMPLE_BANK_ROWS: Final[tuple[tuple[str, ...], ...]] = (
    ("2025-01-05", "收到货款", "12000.00", "0.00", "112000.00"),
    ("2025-01-18", "支付房租", "0.00", "8000.00", "104000.00"),
)

_TEMPLATES: Final[dict[str, tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]]] = {
    TRIAL_BALANCE_SHEET: (TRIAL_BALANCE_COLUMNS, _SAMPLE_TRIAL_ROWS),
    INCOME_STATEMENT_SHEET: (INCOME_STATEMENT_COLUMNS, _SAMPLE_INCOME_ROWS),
    BANK_STATEMENT_SHEET: (BANK_STATEMENT_COLUMNS, _SAMPLE_BANK_ROWS),
}


def build_template_xlsx(sheet: str = TRIAL_BALANCE_SHEET) -> bytes:
    """生成带表头与两行示例的导入模板 xlsx（openpyxl，无公式无宏）。"""
    from openpyxl import Workbook

    try:
        columns, samples = _TEMPLATES[sheet]
    except KeyError as exc:  # pragma: no cover - 防御分支
        raise ValueError(f"unknown template sheet: {sheet}") from exc
    workbook = Workbook()
    ws = workbook.active
    assert ws is not None  # 新建工作簿必有活动表
    ws.title = sheet
    ws.append(list(columns))
    for row in samples:
        # 示例值一律写文本，避免 Excel 把长科目编码变成科学计数法
        ws.append([str(value) for value in row])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
