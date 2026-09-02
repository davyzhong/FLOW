# -*- coding: utf-8 -*-
"""文章列表发现通道（providers）。

- seed        : 手动队列 queue/pending_<source_id>.txt，一行一个文章链接（# 为注释）；
- mp_platform : 微信公众平台 appmsg 接口，可枚举目标账号的全部历史文章。
                需要凭据（任一公众号账号登录 mp.weixin.qq.com 后获取）：
                  环境变量 WECHAT_MP_COOKIE / WECHAT_MP_TOKEN
                  或 <repo>/work/wechat_kb/mp_credentials.json（work/ 不入 git）；
- rss         : 通用 RSS/Atom 源（如 wechat2rss 源），sources.yaml 中配置 feed 字段。

所有出站 URL 经 wechatlib.check_url 白名单校验。
"""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from pathlib import Path
from defusedxml import ElementTree as SafeET

import requests

from wechatlib import WECHAT_UA, check_url, safe_get

MP_HOST = "https://mp.weixin.qq.com"


def extract_article_url(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = re.search(r"https?://mp\.weixin\.qq\.com/s[?/\S]*", line)
    return m.group(0) if m else None


def discover_seed(queue_dir: Path, source_id: str, consume: bool = True) -> list[str]:
    """读取该账号的 pending 队列文件，返回全部链接。

    不再原地标记"已处理"：去重统一由 sync 的 state/seen_urls.json 负责（含 excluded/
    skipped 状态），队列文件因此可以安全地批量预灌，--limit 截断也不会丢链接。
    """
    path = queue_dir / ("pending_%s.txt" % source_id)
    if not path.exists():
        return []
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        url = extract_article_url(line)
        if url:
            urls.append(url)
    return urls


def load_mp_credentials(cred_path: Path | None = None) -> tuple[str, str] | None:
    cookie = os.environ.get("WECHAT_MP_COOKIE", "").strip()
    token = os.environ.get("WECHAT_MP_TOKEN", "").strip()
    candidates = []
    if cred_path is not None:
        candidates.append(cred_path)
    candidates.append(Path.home() / ".config" / "wx-harvest" / "credentials.json")
    if not cookie:
        for cand in candidates:
            if cand.exists():
                data = json.loads(cand.read_text(encoding="utf-8"))
                cookie = str(data.get("cookie", "")).strip()
                token = str(data.get("token", "")).strip()
                if cookie and token:
                    break
    if cookie and token:
        return cookie, token
    return None


def _mp_get(session: requests.Session, url: str) -> dict:
    for attempt in range(4):
        resp = session.get(url, timeout=30)
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError("mp_platform 返回非 JSON（登录可能失效）: %s..." % resp.text[:120])
        base = data.get("base_resp", {})
        ret = base.get("ret", -1)
        if ret == 0:
            return data
        if ret == 200013:  # 频率限制
            time.sleep(30 * (attempt + 1))
            continue
        raise RuntimeError("mp_platform 错误 ret=%s msg=%s" % (ret, base.get("err_msg", "")))
    raise RuntimeError("mp_platform 频率限制重试耗尽")


def discover_mp_platform(source: dict, cred_path: Path) -> list[str]:
    """用公众平台接口枚举账号全部历史文章 URL（按时间升序）。"""
    cred = load_mp_credentials(cred_path)
    if not cred:
        return []
    cookie, token = cred
    nickname = source["name"]

    session = requests.Session()
    session.headers.update({"User-Agent": WECHAT_UA, "Cookie": cookie, "Referer": MP_HOST})
    check_url(MP_HOST)

    # 1) fakeid：优先用 sources 配置里的稳定值，避免 searchbiz 调用触发 200013
    fakeid = source.get("fakeid")
    if not fakeid:
        search_url = (
            MP_HOST + "/cgi-bin/searchbiz?action=search_biz&begin=0&count=5"
            "&query=%s&token=%s&lang=zh_CN&f=json&ajax=1&random=%s"
            % (requests.utils.quote(nickname), token, secrets.token_hex(16))
        )
        data = _mp_get(session, search_url)
        for item in data.get("list", []):
            if item.get("nickname") == nickname:
                fakeid = item.get("fakeid")
                break
        if not fakeid:
            raise RuntimeError("mp_platform 未找到公众号: %s" % nickname)

    # 2) 分页枚举全部文章
    urls = []
    begin = 0
    while True:
        list_url = (
            MP_HOST + "/cgi-bin/appmsg?action=list_ex&begin=%d&count=5&fakeid=%s"
            "&type=9&query=&token=%s&lang=zh_CN&f=json&ajax=1&random=%s"
            % (begin, fakeid, token, secrets.token_hex(16))
        )
        data = _mp_get(session, list_url)
        items = data.get("app_msg_list", [])
        if not items:
            break
        for item in items:
            link = item.get("link", "")
            if link:
                urls.append((int(item.get("create_time", 0)), link))
        if len(items) < 5 or begin > 2000:
            break
        begin += 5
        time.sleep(3.0)
    urls.sort()
    return [u for _, u in urls]


def discover_rss(source: dict) -> list[str]:
    feed = source.get("feed")
    if not feed:
        return []
    # RSS 源由 sources.yaml 显式配置，不限 host 后缀，但保留 https 与内网地址防护
    resp = safe_get(feed, allowed_suffixes=None)
    root = SafeET.fromstring(resp.content)
    urls = []
    for item in root.iter("item"):
        link = item.findtext("link")
        if link:
            urls.append(link.strip())
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
            href = link.get("href")
            if href:
                urls.append(href.strip())
    return urls


def discover(queue_dir: Path, source: dict, cred_path: Path, consume: bool = True) -> list[str]:
    """按可用性依次运行各通道并合并去重。"""
    urls: list[str] = list(discover_seed(queue_dir, source["id"], consume=consume))
    try:
        urls += discover_mp_platform(source, cred_path)
    except RuntimeError as exc:
        print("  [warn] mp_platform 通道失败（%s）" % exc)
    try:
        urls += discover_rss(source)
    except Exception as exc:
        print("  [warn] rss 通道失败（%s）" % exc)
    seen = set()
    unique = []
    for u in urls:
        u = u.split("#")[0]
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique
