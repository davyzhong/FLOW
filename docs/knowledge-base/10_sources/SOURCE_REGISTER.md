---
doc_id: FLOW-SRC-REGISTER-001
title: 来源登记册
doc_type: source-evidence
status: registered
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: knowledge-base
snapshot_id: obsidian-2026-09-12T15:46+08:00
sensitivity: project-internal
---

# 来源登记册（基线截面 obsidian-2026-09-12T15:46+08:00）

## 分层登记策略（V1.1 §4.2/§4.8 落地）

「全部整理」的完成标准 = **所有来源组均有处置记录**，而非逐篇复制。登记分两层：

1. **组级（group）**：12 个来源组全覆盖基线声明范围（合计 3035 篇正文：非微信 1575 + 微信 1460），每组登记范围定义、声明篇数、处置与 K 域路由；
2. **篇级（article）**：仅登记具备稳定定位符（wechat-id / 笔记数字 ID）的已识别 HIGH 代表篇；知识卡（20_knowledge_cards）实际引用某篇时，**按需追加篇级条目**并回填 `source_refs`——正式知识永远可反查到具体来源。

## 组级登记（与评估册声明值对账）

| 组 | 范围 | 声明篇数 | 处置 | 核验等级 |
|---|---|---:|---|---|
| GRP-A-finance | vault `03_财务与会计` 两个目录 | 231 | adopted-candidate | representative-read |
| GRP-B-management | vault `02_企业管理` | 441 | background（HIGH 66 单列候选） | program-routed |
| GRP-C-logistics | vault `04_跨境物流` | 125 | adopted-candidate | representative-read |
| GRP-D-wiki | vault `wiki/` 财务关键词命中 | 778 | adopted-candidate | program-routed |
| GRP-W1-wechat | 微信·数据分析星球+数据熊 | 435 | adopted-candidate | representative-read |
| GRP-W2-wechat | 微信·客观分析报告+数研复盘狮 | 2 | adopted-candidate | representative-read |
| GRP-W3-wechat | 微信·数据分析不是个事儿+花叔 | 176 | background | program-routed |
| GRP-W4-mumuziyou | 微信·木木自由 | 482 | pending-verification | program-routed |
| GRP-W4-benxiang | 微信·奔向自由的果 | 183 | adopted-candidate | representative-read |
| GRP-W4-chenfan | 微信·宸帆海财会咨询服务 | 179 | pending-verification（重复与通识较多） | program-routed |
| GRP-W4-jiejue | 微信·解决方案研究所 | 2 | adopted-candidate | representative-read |
| GRP-W4-zhanlue | 微信·战略领航家 | 1 | adopted-candidate | representative-read |

## 仓库内已归档来源（另有登记）

| 来源家族 | 归档位置 | 说明 |
|---|---|---|
| 历史会话（ChatGPT/Codex） | `01_conversations/raw/`（不可变） | 见 `06_sources/SOURCE_CATALOG.md` 来源组 A |
| 研究资料 01–05 | `02_research/original/`（不可变） | 来源组 B |
| 公众号文章移交件 | `08_wechat_sources/`（186 正文 + 417 索引） | S00–S20 家族见参考与订正总册 |
| P5 财报样本 | `02_research/original/p5_samples/`（不可变，机器消费） | HKEX 官方披露 + 招股书 |

## 截面与偏差说明

- 基线截面由 [2026-09-12 评估册](../02_research/synthesis/2026-09-12-obsidian-internal-kb-assessment.md)与 [obsidian-scan 明细](../02_research/synthesis/2026-09-12-obsidian-scan/)冻结；
- 截面重建实验（2026-09-12 执行期）：vault 逐篇 mtime 过滤存在 ±2 篇噪声（多机同步刷新 mtime 所致），组级计数与声明值完全一致；故采用组级对账而非逐篇枚举，**不伪造逐篇路径**；
- 截面后新增内容（如宸帆目录截面后新增约 173 篇）不属于本基线，留待未来增量截面。
