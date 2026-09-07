"""固定 Chromium PDF 打印机：把报告 HTML 打为独立 PDF 文件。

Chromium 定位顺序：环境变量 FLOW_CHROMIUM_PATH → Playwright 浏览器缓存
（ms-playwright/chromium-*，与前端 e2e 共用同一固定版本）。缺失时抛
ChromiumNotFoundError（调用方决定跳过或失败，不产生假成功）。
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


class ChromiumNotFoundError(RuntimeError):
    pass


def find_chromium() -> Path:
    override = os.environ.get("FLOW_CHROMIUM_PATH")
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return candidate
        raise ChromiumNotFoundError(f"FLOW_CHROMIUM_PATH 指向的文件不存在: {override}")
    cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    candidates = sorted(
        set(
            cache.glob("chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium")
        )
        | set(
            cache.glob(
                "chromium-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/"
                "Google Chrome for Testing"
            )
        )
        | set(cache.glob("chromium-*/chrome-linux*/chrome"))
    )
    if not candidates:
        raise ChromiumNotFoundError("未找到 Playwright Chromium；请安装或设置 FLOW_CHROMIUM_PATH")
    return candidates[-1]  # 版本号排序取最新


def print_pdf(html: str, *, out_path: Path, chromium: Path | None = None) -> Path:
    """把 HTML 打为 PDF（A4，无页眉页脚），写入 out_path。"""
    binary = chromium or find_chromium()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "report.html"
        html_path.write_text(html, encoding="utf-8")
        command = [
            str(binary),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_path}",
            html_path.as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, timeout=120)
        if result.returncode != 0 or not out_path.exists():
            raise RuntimeError(
                f"Chromium 打印失败 rc={result.returncode}: "
                f"{result.stderr.decode('utf-8', errors='replace')[:300]}"
            )
    if out_path.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError("Chromium 输出不是有效 PDF")
    return out_path


__all__ = ["ChromiumNotFoundError", "find_chromium", "print_pdf"]
