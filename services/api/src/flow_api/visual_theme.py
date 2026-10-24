"""将可移植 FLOW 视觉 token 映射到文档导出表面。"""
from __future__ import annotations

from typing import Any

from flow_api.visual_tokens import VISUAL_TOKENS


def _primary_font(token: str) -> str:
    return VISUAL_TOKENS[token].split(",", maxsplit=1)[0].strip().strip("\"'")


def _rgb(token: str) -> Any:
    from pptx.dml.color import RGBColor

    value = VISUAL_TOKENS[token].removeprefix("#")
    return RGBColor.from_string(value)  # type: ignore[no-untyped-call]


def apply_pptx_visual_theme(presentation: Any) -> None:
    """统一标题、正文与颜色；不改变冻结报告的数据与分页结构。"""
    title_color = _rgb("colors-brand-navy")
    body_color = _rgb("colors-text-primary")
    for slide in presentation.slides:
        title_shape = slide.shapes.title
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            is_title = shape is title_shape
            family = _primary_font(
                "typography-family-display" if is_title else "typography-family-body"
            )
            color = title_color if is_title else body_color
            for paragraph in shape.text_frame.paragraphs:
                paragraph.font.name = family
                paragraph.font.color.rgb = color
                for run in paragraph.runs:
                    run.font.name = family
                    run.font.color.rgb = color


def style_workbook_headers(workbook: Any) -> None:
    """为 XLSX 表头加深海军蓝层级，保留工作簿的数据优先结构。"""
    from openpyxl.styles import Alignment, Font, PatternFill

    fill = PatternFill("solid", fgColor=VISUAL_TOKENS["colors-surface-nav"].lstrip("#"))
    font = Font(
        name=_primary_font("typography-family-body"),
        bold=True,
        color=VISUAL_TOKENS["colors-text-inverse"].lstrip("#"),
    )
    for sheet in workbook.worksheets:
        if sheet.max_row < 1:
            continue
        for cell in sheet[1]:
            cell.fill = fill
            cell.font = font
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
