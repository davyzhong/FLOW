# -*- coding: utf-8 -*-
"""微信公众号文章抓取与转换核心库。

约定（详见 docs/knowledge-base/08_wechat_sources/README.md）：
- 单篇文章 = article.md（正文 Markdown + YAML frontmatter）+ images/ + meta.json；
- 原始 HTML 只落在 work/ 缓存（不入库），KB 内保存转换后的正文与全部图片；
- 所有出站请求必须经过 safe_get：仅 http(s)、host 白名单、DNS 解析结果
  不得命中私有/环回/保留地址（生成前安全约束）。
"""

from __future__ import annotations

import html as html_mod
import hashlib
import ipaddress
import re
import socket
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

import requests

CST = timezone(timedelta(hours=8))

WECHAT_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.49 NetType/WIFI Language/zh_CN"
)
DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# 允许抓取的 host 后缀白名单（微信公众号正文与图片 CDN）。
ALLOWED_HOST_SUFFIXES = (
    "mp.weixin.qq.com",
    "mmbiz.qpic.cn",
    "mmbiz.qlogo.cn",
)

_BLOCK_MARKERS = ("环境异常", "请在微信客户端打开链接", "操作频繁", "该内容已被发布者删除")

IMG_PLACEHOLDER = "\x00IMG:%s\x00"


class FetchError(RuntimeError):
    pass


def _is_dangerous_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """SSRF 防护：拒绝环回/内网/链路本地等地址。

    例外：198.18.0.0/15（RFC 2544 基准段）是本机 TUN 代理 fake-ip 的占位段，
    连接它实际由本地代理按 host 白名单转发，不属于可触达的内网服务。
    """
    if ip.version == 4 and ip in ipaddress.ip_network("198.18.0.0/15"):
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def check_url(url: str, allowed_suffixes: tuple[str, ...] | None = ALLOWED_HOST_SUFFIXES) -> str:
    """校验并规范化 URL：仅 https、host 白名单、DNS 不指向内网/保留地址。

    allowed_suffixes=None 表示不限制 host 后缀（用于用户在 sources.yaml 显式配置的
    RSS 源等可信入口），但内网/保留地址防护始终生效。
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise FetchError("仅允许 http/https 协议: %s" % url)
    host = parts.hostname
    if not host:
        raise FetchError("URL 缺少 host: %s" % url)
    if allowed_suffixes is not None and not any(
        host == s or host.endswith("." + s) for s in allowed_suffixes
    ):
        raise FetchError("host 不在白名单内: %s" % host)
    for info in socket.getaddrinfo(host, None):
        ip = ipaddress.ip_address(info[4][0])
        if _is_dangerous_ip(ip):
            raise FetchError("host 解析到非公网地址，已拒绝: %s -> %s" % (host, ip))
    clean = "https://" + parts.netloc + parts.path
    if parts.query:
        clean += "?" + parts.query
    return clean


def safe_get(
    url: str,
    referer: str | None = None,
    timeout: int = 30,
    allowed_suffixes: tuple[str, ...] | None = ALLOWED_HOST_SUFFIXES,
) -> requests.Response:
    url = check_url(url, allowed_suffixes=allowed_suffixes)
    headers = {"User-Agent": WECHAT_UA}
    if referer:
        headers["Referer"] = referer
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


def looks_blocked(html_text: str) -> bool:
    if "js_content" not in html_text:
        return True
    return any(m in html_text for m in _BLOCK_MARKERS)


def fetch_article_html(url: str, cache_dir: Path | None = None) -> str:
    """抓取文章完整 HTML；被风控时换桌面 UA 重试一次。"""
    html_text = None
    try:
        html_text = safe_get(url).text
        if looks_blocked(html_text):
            html_text = None
    except requests.RequestException:
        html_text = None
    if html_text is None:
        resp = requests.get(check_url(url), headers={"User-Agent": DESKTOP_UA}, timeout=30)
        resp.raise_for_status()
        html_text = resp.text
        if looks_blocked(html_text):
            raise FetchError("文章被微信风控拦截，需稍后重试或手动导入: %s" % url)
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(CST).strftime("%Y%m%d%H%M%S%f")
        (cache_dir / ("wx_%s.html" % stamp)).write_text(html_text, encoding="utf-8")
    return html_text


def _regex1(pattern: str, text: str):
    m = re.search(pattern, text)
    if m:
        return html_mod.unescape(m.group(1)).strip()
    return None


def parse_article_meta(html_text: str) -> dict:
    """从文章 HTML 中提取标题/账号/作者/发布时间等元数据。"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "lxml")

    title = _regex1(r'<meta property="og:title" content="([^"]*)"', html_text)
    if not title:
        title = _regex1(r"var msg_title = ['\"](.*?)['\"]\s*\.html", html_text)
    if not title:
        node = soup.find(id="activity-name")
        title = node.get_text(strip=True) if node else None
    if not title and soup.title:
        title = soup.title.get_text(strip=True)

    nickname = _regex1(r'nickname = htmlDecode\("([^"]+)"\)', html_text)
    if not nickname:
        nickname = _regex1(r'var nickname = "([^"]+)"', html_text)
    if not nickname:
        nickname = _regex1(r'class="profile_nickname"[^>]*>([^<]+)<', html_text)
    if not nickname:
        node = soup.find(id="js_name")
        nickname = node.get_text(strip=True) if node else None

    gh_id = _regex1(r'var user_name = "([^"]+)"', html_text)
    biz = _regex1(r'var biz = "([^"]+)"', html_text) or _regex1(r"__biz=([A-Za-z0-9+=/]+)", html_text)
    author = _regex1(r'var author = ["\']([^"\']*)["\']', html_text)
    if not author:
        node = soup.find(id="js_author_name")
        author = node.get_text(strip=True) if node else None

    publish_time = None
    ct = _regex1(r'var ct = "(\d{10})"', html_text)
    if ct:
        publish_time = datetime.fromtimestamp(int(ct), CST).strftime("%Y-%m-%d %H:%M")
    if not publish_time:
        publish_time = _regex1(r"var createTime = ['\"]([0-9:\- ]+)['\"]", html_text)
    if not publish_time:
        node = soup.find(id="publish_time")
        publish_time = node.get_text(strip=True) if node else None

    digest = _regex1(r'<meta property="og:description" content="([^"]*)"', html_text)
    if not digest:
        digest = _regex1(r'var msg_desc = ["\'](.*?)["\']', html_text)
    cover = _regex1(r'var msg_cdn_url = "([^"]+)"', html_text)

    return {
        "title": title,
        "account": nickname,
        "account_id": gh_id,
        "biz": biz,
        "author": author,
        "publish_time": publish_time,
        "digest": digest,
        "cover_url": cover,
    }


# ---------------------------------------------------------------- Markdown 转换

_INLINE_TAGS = ("strong", "b", "em", "i", "code", "a", "span", "u", "sup", "sub")


def _img_ext(img_url: str, content_type: str | None, head: bytes) -> str:
    qs = parse_qs(urlsplit(img_url).query)
    fmt = (qs.get("wx_fmt") or [None])[0]
    if fmt in ("jpg", "jpeg", "png", "gif", "webp"):
        return "jpg" if fmt == "jpeg" else fmt
    if head.startswith(b"\xff\xd8"):
        return "jpg"
    if head.startswith(b"\x89PNG"):
        return "png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head.startswith(b"RIFF") and len(head) >= 12 and head[8:12] == b"WEBP":
        return "webp"
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        m = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp"}
        if ct in m:
            return m[ct]
    return "jpg"


def _inline_text(node) -> str:
    """行内元素 → 行内 Markdown（图片用占位符，统一回填）。"""
    from bs4 import NavigableString, Tag

    out = []
    for child in node.children:
        if isinstance(child, NavigableString):
            out.append(str(child))
        elif isinstance(child, Tag):
            name = child.name.lower()
            if name in ("strong", "b"):
                t = _inline_text(child).strip()
                if t:
                    out.append("**%s**" % t)
            elif name in ("em", "i"):
                t = _inline_text(child).strip()
                if t:
                    out.append("*%s*" % t)
            elif name == "code":
                out.append("`%s`" % child.get_text())
            elif name == "br":
                out.append("\n")
            elif name == "a":
                href = child.get("href") or ""
                t = _inline_text(child).strip()
                if href.startswith(("http://", "https://")) and t:
                    out.append("[%s](%s)" % (t, href))
                else:
                    out.append(t)
            elif name == "img":
                url = child.get("data-src") or child.get("src") or ""
                out.append(IMG_PLACEHOLDER % url)
            elif name in _INLINE_TAGS:
                out.append(_inline_text(child))
            else:
                out.append(_inline_text(child))
    return "".join(out)


def _table_to_md(table) -> str:
    rows = table.find_all("tr")
    if not rows:
        return ""
    lines = []
    for i, tr in enumerate(rows):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            txt = _inline_text(cell)
            txt = txt.replace("|", "\\|").replace("\n", " ").strip()
            cells.append(txt or " ")
        if not cells:
            continue
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            lines.append("|" + "---|" * len(cells))
    return "\n".join(lines)


class MarkdownBuilder:
    """把 js_content 递归转成 Markdown。

    图片先以 \x00IMG:url\x00 占位；图片文件名按出现顺序固定为 imgNNN，
    下载完成后由 render_images() 回填扩展名与本地路径。
    """

    SKIP_TAGS = {"script", "style", "svg", "iframe", "link", "meta", "mpvoice", "qqmusic"}

    def __init__(self):
        self.image_urls: list[str] = []
        self._seen: set[str] = set()

    def register(self, url: str) -> int:
        """登记图片 URL，返回其序号（1 起）。返回 0 表示无效。"""
        if not url or not url.startswith(("http://", "https://")):
            return 0
        if url not in self._seen:
            self._seen.add(url)
            self.image_urls.append(url)
        return self.image_urls.index(url) + 1

    def block(self, node, depth: int = 0) -> str:
        from bs4 import NavigableString, Tag

        if isinstance(node, NavigableString):
            return str(node)
        if not isinstance(node, Tag) or depth > 60:
            return ""
        name = node.name.lower()
        if name in self.SKIP_TAGS:
            return ""
        if name in ("video", "mpvideosnap"):
            return "\n> [视频内容，见原文]\n"
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = _inline_text(node).strip()
            return "\n%s %s\n" % ("#" * int(name[1]), text) if text else "\n"
        if name == "blockquote":
            inner = self.container(node, depth + 1).strip()
            if inner:
                return "\n" + "\n".join("> " + ln if ln else ">" for ln in inner.split("\n")) + "\n"
            return "\n"
        if name == "table":
            return "\n%s\n" % _table_to_md(node)
        if name == "hr":
            return "\n---\n"
        if name in ("ul", "ol"):
            items = []
            idx = 0
            for li in node.find_all("li", recursive=False):
                idx += 1
                marker = "- " if name == "ul" else "%d. " % idx
                content = self.container(li, depth + 1).strip()
                lines = [ln for ln in content.split("\n")]
                if not lines:
                    continue
                items.append(marker + lines[0])
                for extra in lines[1:]:
                    items.append(("   " if name == "ul" else "    ") + extra)
            return "\n" + "\n".join(items) + "\n"
        if name == "img":
            idx = self.register(node.get("data-src") or node.get("src") or "")
            if not idx:
                return "\n"
            return "\n\x00MDIMG:%03d\x00\n" % idx
        # 其余一律当块容器（p/section/div/figure/body/未知标签）
        return "\n" + self.container(node, depth + 1) + "\n"

    def container(self, node, depth: int = 0) -> str:
        from bs4 import NavigableString, Tag

        parts = []
        for child in node.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                name = child.name.lower()
                if name == "img":
                    idx = self.register(child.get("data-src") or child.get("src") or "")
                    parts.append(IMG_PLACEHOLDER % ("#%d" % idx if idx else ""))
                elif name in self.SKIP_TAGS:
                    continue
                else:
                    parts.append(self.block(child, depth))
        text = "".join(parts)
        text = text.replace("\u00a0", " ")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip("\n")


def render_images(markdown: str, builder: MarkdownBuilder, saved: list[dict]) -> str:
    """下载完成后回填图片占位符：\x00MDIMG:NNN\x00 → 本地相对路径。"""
    by_idx = {}
    for i, item in enumerate(saved, start=1):
        by_idx[i] = item

    def repl(m):
        idx = int(m.group(1))
        item = by_idx.get(idx)
        if not item or not item.get("file"):
            return "\n> [图片缺失，见原文]\n"
        return "\n![图片](%s)\n" % item["file"]

    markdown = re.sub(r"\x00MDIMG:(\d+)\x00", repl, markdown)
    # 行内占位（含 #idx 形式）
    def repl_inline(m):
        idx = int(m.group(1).lstrip("#"))
        item = by_idx.get(idx)
        if not item or not item.get("file"):
            return ""
        return "\n![图片](%s)\n" % item["file"]

    markdown = re.sub(r"\x00IMG:#(\d+)\x00", repl_inline, markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n"


def download_named_image(url: str, images_dir: Path, stem: str) -> str | None:
    """下载单张图片并固定文件名（如 cover.jpg），返回相对路径；失败返回 None。"""
    try:
        images_dir.mkdir(parents=True, exist_ok=True)
        resp = safe_get(url)
        head = resp.content[:16]
        if len(resp.content) < 400:
            return None
        ext = _img_ext(url, resp.headers.get("Content-Type"), head)
        rel = "images/%s.%s" % (stem, ext)
        (images_dir / ("%s.%s" % (stem, ext))).write_bytes(resp.content)
        return rel
    except Exception:
        return None


def download_images(image_urls: list[str], images_dir: Path) -> list[dict]:
    """按顺序下载全部图片；失败图片记录 error 并跳过，不阻断整篇。"""
    images_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for i, url in enumerate(image_urls, start=1):
        try:
            resp = safe_get(url)
            head = resp.content[:16]
            if len(resp.content) < 400:
                raise FetchError("image too small (%d bytes)" % len(resp.content))
            ext = _img_ext(url, resp.headers.get("Content-Type"), head)
            fname = "img%03d.%s" % (i, ext)
            (images_dir / fname).write_bytes(resp.content)
            saved.append(
                {
                    "url": url,
                    "file": "images/" + fname,
                    "size": len(resp.content),
                    "sha256": hashlib.sha256(resp.content).hexdigest(),
                }
            )
            time.sleep(0.4)
        except Exception as exc:  # 单图失败不阻断整篇
            saved.append({"url": url, "file": None, "error": str(exc)[:200]})
    return saved


def slugify_title(title: str, max_len: int = 50) -> str:
    t = re.sub(r'[\\/:*?"<>|\r\n\t#]', "", title)
    t = re.sub(r"\s+", "_", t.strip())
    return t[:max_len] or "untitled"
