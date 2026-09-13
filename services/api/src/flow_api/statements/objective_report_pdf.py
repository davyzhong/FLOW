"""固定 Chromium PDF 打印机：把报告 HTML 打为独立 PDF 文件（含每页页脚与页码）。

Chromium 定位顺序：环境变量 FLOW_CHROMIUM_PATH → Playwright 浏览器缓存
（ms-playwright/chromium-*，与前端 e2e 共用同一固定版本）。缺失时抛
ChromiumNotFoundError（调用方决定跳过或失败，不产生假成功）。

每页页脚/页码通过 DevTools 协议 Page.printToPDF 的 displayHeaderFooter +
footerTemplate 实现（页码只能在打印时由浏览器生成，CSS 做不到）。
"""

from __future__ import annotations

import asyncio
import base64
import html
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

from websockets.asyncio.client import connect


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


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_debug_endpoint(port: int, timeout_s: float = 20.0) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/list", timeout=2
            ) as response:
                targets = json.load(response)
            for target in targets:
                if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                    return str(target["webSocketDebuggerUrl"])
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(0.3)
    raise RuntimeError("Chromium 调试端口未就绪（超时）")


def _footer_template(footer_left: str) -> str:
    left = html.escape(footer_left or "FLOW 客观财务分析引擎")
    style = (
        "width:100%; font-size:8px; color:#6b7280; padding:0 12mm;"
        " display:flex; justify-content:space-between;"
        " font-family:'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;"
    )
    return (
        f'<div style="{style}"><span>{left}</span>'
        '<span>第 <span class="pageNumber"></span> 页 / '
        '共 <span class="totalPages"></span> 页</span></div>'
    )


def _chromium_command(binary: Path, port: int, profile_dir: Path) -> list[str]:
    command = [
        str(binary),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "about:blank",
    ]
    if os.environ.get("FLOW_CHROMIUM_NO_SANDBOX") == "1":
        command.insert(1, "--no-sandbox")
    return command


async def _print_via_cdp(
    ws_url: str,
    page_url: str,
    footer_left: str,
    out_path: Path,
    timeout_s: float = 90.0,
) -> None:
    async def call(
        websocket: Any, request_id: int, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        await websocket.send(json.dumps({"id": request_id, "method": method, "params": params}))
        while True:
            message = json.loads(await asyncio.wait_for(websocket.recv(), timeout_s))
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"{method} 失败: {message['error']}")
                return dict(message.get("result", {}))

    async def wait_event(websocket: Any, method: str) -> dict[str, Any]:
        while True:
            message = json.loads(await asyncio.wait_for(websocket.recv(), timeout_s))
            if message.get("method") == method:
                return dict(message)

    async with connect(ws_url, max_size=64 * 1024 * 1024) as websocket:
        await call(websocket, 1, "Page.enable", {})
        await call(websocket, 2, "Page.navigate", {"url": page_url})
        await wait_event(websocket, "Page.loadEventFired")
        result = await call(
            websocket,
            3,
            "Page.printToPDF",
            {
                "displayHeaderFooter": True,
                "headerTemplate": "<span></span>",
                "footerTemplate": _footer_template(footer_left),
                "paperWidth": 8.27,
                "paperHeight": 11.69,
                "marginTop": 0.55,
                "marginBottom": 0.55,
                "marginLeft": 0.47,
                "marginRight": 0.47,
                "printBackground": True,
                "preferCSSPageSize": False,
            },
        )
        data = result.get("data")
        if not data:
            raise RuntimeError("Page.printToPDF 未返回数据")
        out_path.write_bytes(base64.b64decode(data))


def print_pdf(
    html: str,
    *,
    out_path: Path,
    chromium: Path | None = None,
    footer_left: str = "",
) -> Path:
    """把 HTML 打为 A4 PDF，每页页脚含 footer_left 与页码，写入 out_path。"""
    binary = chromium or find_chromium()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "report.html"
        html_path.write_text(html, encoding="utf-8")
        port = _free_port()
        profile_dir = Path(tmp) / "chromium-profile"
        process = subprocess.Popen(
            _chromium_command(binary, port, profile_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            ws_url = _wait_for_debug_endpoint(port)
            asyncio.run(
                _print_via_cdp(ws_url, html_path.as_uri(), footer_left, out_path)
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    if not out_path.exists() or out_path.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError("Chromium 输出不是有效 PDF")
    return out_path


__all__ = ["ChromiumNotFoundError", "find_chromium", "print_pdf"]
