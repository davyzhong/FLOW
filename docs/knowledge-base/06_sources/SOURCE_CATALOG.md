# 原始资料与来源目录

## 来源组 A：历史会话

| 内容 | 原始位置 | 归档位置 | 说明 |
|---|---|---|---|
| Finance Intelligence OS 完整 ChatGPT 会话 | `/Users/qiming/workspace/FLOW/Finance_Intelligence_OS_完整会话归档.md` | `01_conversations/raw/chatgpt/` | 早期产品讨论的完整 Markdown 归档 |
| 当前 Codex 会话 2026-08-28 | `~/.codex/sessions/2026/08/28/...jsonl` | `01_conversations/raw/codex/` | 机器级原始会话 |
| 当前 Codex 会话 2026-08-29 | `~/.codex/sessions/2026/08/29/...jsonl` | `01_conversations/raw/codex/` | 机器级原始会话 |
| Codex 可读转录 | 由上述 JSONL 机械提取 | `01_conversations/readable/` | 仅保留 user/assistant 消息 |

## 来源组 B：五篇研究资料

| 内容 | 原始位置 | 归档位置 |
|---|---|---|
| 研究 Markdown、文本、HTML 和图片 | `/Users/qiming/.zcode/workspace/default/research/` | `02_research/original/` |
| 系统研究综合结论 | `/Users/qiming/Documents/Codex/2026-08-28/referenced-chatgpt-conversation-this-is-an/outputs/Finance_Intelligence_OS_系统研究结论.md` | `02_research/synthesis/` |

原始研究目录中的 `.mimosa` 运行状态不属于研究内容，未复制。

## 来源组 C：物流行业截图

| 内容 | 原始位置 | 归档位置 |
|---|---|---|
| 六张菜鸟供应链规模日报 | `/Users/qiming/workspace/FLOW/微信图片_*.png` | `03_assets/logistics_daily/` |

## 来源组 D：外部驾驶舱参考图

| 内容 | 原始位置 | 归档位置 |
|---|---|---|
| 集团财务智能驾驶舱图片 | 微信图片 CDN 链接，归档前下载到 `work/reference-dashboard.png` | `03_assets/external_reference/reference-dashboard.webp` |

归档文件按实际 WebP 内容保存为 `.webp`，避免原下载文件扩展名与内容类型不一致。

## 来源组 E：FLOW 设计产物

| 内容 | 原始位置 | 归档位置 |
|---|---|---|
| 浏览器视觉原型 | `.superpowers/brainstorm/68961-1787989304/content/` | `03_assets/visual_prototypes/` |
| V1 正式设计规格 | `docs/superpowers/specs/2026-08-29-flow-v1-design.md` | `05_design/approved/` 保存归档快照 |

## 来源组 F：公众号素材库（已移交 DavyBase 项目）

| 公众号 | 账号 ID | 内容位置 | 说明 |
|---|---|---|---|
| 数据熊 | gh_d55144ba7fe2 | vault：`微信知识库/数据熊/`（4 合集 412 篇） | 财务分析/财务管理/财务报表/经营分析 |
| 数研复盘狮 | gh_78506a7234d3 | vault：`微信知识库/数研复盘狮/` | 经营分析报告、毛利/净利润专题 |
| 花叔 | gh_13cc971d267c | vault：`微信知识库/花叔/` | Huashu Excel 作者 |

2026-09-03 起该能力整体移交 DavyBase 项目（多渠道知识抓取 → Obsidian 知识库）。
内容唯一存储于本机 Obsidian vault；本仓库仅保留引用入口（`08_wechat_sources/INDEX.md`）。
移交详情与流水线归属见 [`../08_wechat_sources/HANDOFF.md`](../08_wechat_sources/HANDOFF.md)。

## 完整文件级记录

逐文件路径、大小和修改时间见 `../99_manifest/inventory.tsv`；内容哈希见 `../99_manifest/sha256sums.txt`。

