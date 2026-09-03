# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31",
# ]
# ///
# -*- coding: utf-8 -*-
"""公众号合集（相册）文章列表爬取——公开接口，无登录、不受 appmsg 200013 限流影响。

用法：
    uv run scripts/wechat_kb/fetch_album.py \
        --album-url "https://mp.weixin.qq.com/mp/appmsgalbum?__biz=...&action=getalbum&album_id=..." \
        [--out-queue docs/knowledge-base/08_wechat_sources/queue/pending_shujuxiong.txt] \
        [--json-out /tmp/album_items.json]

合集翻页：末条 msgid/idx 作为 begin_msgid/beginidx 继续请求，直到 continue_flag=0。
输出按发布时间升序（旧的在前，入库顺序与时间线一致）。

安全约束：请求目标固定为 wechatlib.ALBUM_API 常量（https、mp.weixin.qq.com），业务参数
经 safe_get 的 params 由 requests 统一编码；输入 URL 仅用于解析参数，且经 check_url
校验协议、host 白名单与解析 IP 非内网/保留地址；禁用重定向。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wechatlib import check_url, safe_get, WECHAT_UA

CST = timezone(timedelta(hours=8))

# 唯一请求目标：常量 host，参数全部经 params 编码
ALBUM_API = "https://mp.weixin.qq.com/mp/appmsgalbum"
ALBUM_HOST = "mp.weixin.qq.com"


def fetch_album(album_url: str, max_pages: int = 200) -> list[dict]:
    check_url(album_url)  # 校验输入 URL 的协议/host/DNS，参数只作业务输入，不拼进请求目标
    base_params = {k: v[-1] for k, v in parse_qs(urlsplit(album_url).query).items()}
    if base_params.get("action") != "getalbum" or "album_id" not in base_params:
        raise RuntimeError("URL 缺少 action=getalbum 或 album_id")
    for k in ("begin_msgid", "begin_itemidx", "beginidx", "count", "f", "scene", "sessionid",
              "is_reverse", "isbackward"):
        base_params.pop(k, None)
    if any(("\x00" in v or "\n" in v) for v in base_params.values()):
        raise RuntimeError("URL 参数含非法字符")

    # 合集元信息：总篇数与是否倒序合集（is_reverse=1 时续页必须带 is_reverse=1，
    # 且翻页参数名为 begin_itemidx —— 与页面前端 album.js 协议一致）
    page_html = safe_get(album_url).text
    m = re.search(r"is_reverse:\s*'([^']*)'", page_html)
    reverse_flag = m.group(1) == "1" if m else False
    m_count = re.search(r"article_count:\s*'(\d+)'", page_html)
    total_hint = int(m_count.group(1)) if m_count else None
    print("  合集元信息：总篇数≈%s，倒序=%s" % (total_hint, reverse_flag))
    if reverse_flag:
        base_params["is_reverse"] = "1"

    items: list[dict] = []
    seen_keys: set[str] = set()
    begin_msgid, begin_itemidx = "0", "0"

    for page in range(max_pages):
        params = dict(base_params)
        params.update({"begin_msgid": begin_msgid, "begin_itemidx": begin_itemidx,
                       "count": "20", "f": "json"})
        # 目标恒为常量 ALBUM_API，host 受 safe_get 白名单约束
        resp = safe_get(ALBUM_API, referer="https://" + ALBUM_HOST + "/",
                        params=params, allowed_suffixes=(ALBUM_HOST,))
        data = resp.json()
        if data.get("base_resp", {}).get("ret", -1) != 0:
            raise RuntimeError("合集接口错误: %s" % json.dumps(data.get("base_resp"), ensure_ascii=False))
        album = data.get("getalbum_resp", {})
        batch = album.get("article_list", []) or []
        fresh = 0
        for it in batch:
            item_url = (it.get("url") or "").replace("\\/", "/").split("#")[0]
            key = str(it.get("msgid", "")) + "_" + str(it.get("itemidx", ""))
            if not item_url or key in seen_keys:
                continue
            seen_keys.add(key)
            items.append({
                "title": it.get("title", ""),
                "url": item_url,
                "create_time": int(it.get("create_time", 0)),
                "msgid": str(it.get("msgid", "")),
                "itemidx": str(it.get("itemidx", "")),
            })
            fresh += 1
        cont = album.get("continue_flag", "0")
        print("  page %d: +%d（累计 %d）continue=%s" % (page + 1, fresh, len(items), cont))
        if cont != "1" or fresh == 0 or not batch:
            break
        last = batch[-1]
        begin_msgid, begin_itemidx = str(last.get("msgid", "0")), str(last.get("itemidx", "0"))
        time.sleep(2.0)
        if total_hint and len(items) >= total_hint:
            break

    items.sort(key=lambda x: (x["create_time"], x["msgid"], x["itemidx"]))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号合集文章列表爬取")
    parser.add_argument("--album-url", required=True)
    parser.add_argument("--out-queue", type=Path, default=None,
                        help="追加到指定 pending 队列文件（去重）")
    parser.add_argument("--json-out", type=Path, default=None, help="完整清单 JSON 输出")
    args = parser.parse_args()

    items = fetch_album(args.album_url)
    for it in items:
        it["publish_time"] = datetime.fromtimestamp(it["create_time"], CST).strftime("%Y-%m-%d %H:%M")
    print("合计 %d 篇（%s ~ %s）" % (
        len(items),
        items[0]["publish_time"] if items else "-",
        items[-1]["publish_time"] if items else "-"))

    if args.json_out:
        args.json_out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        print("清单已写：%s" % args.json_out)

    if args.out_queue:
        existing = set()
        if args.out_queue.exists():
            for line in args.out_queue.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("http"):
                    existing.add(line.split("#")[0])
        added = 0
        lines = []
        for it in items:
            u = it["url"]
            if u not in existing:
                lines.append("%s  # %s %s" % (u, it["publish_time"][:10], it["title"][:40]))
                added += 1
        if lines:
            with args.out_queue.open("a", encoding="utf-8") as fh:
                fh.write("\n# ---- 合集导入 %s（%d 篇）----\n" % (
                    datetime.now(CST).strftime("%Y-%m-%d"), len(lines)))
                fh.write("\n".join(lines) + "\n")
        print("队列新增 %d 条 → %s" % (added, args.out_queue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
