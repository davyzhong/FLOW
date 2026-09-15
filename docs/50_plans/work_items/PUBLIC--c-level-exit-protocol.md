---
doc_id: FLOW-WP-PUBLIC-C-EXIT-001
title: 公开财报模块 C 级出口协议与数字级准确率基准（T09）
doc_type: work-item
status: blocked
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: public-analysis
roadmap_phase: 3
decision_refs: [D052, D053]
depends_on: [FLOW-WP-S01-001]
acceptance_refs: [roadmap-unique-invariant]
gates: [R2, R3, R4, S01-closure]
---

# 公开财报模块 C 级出口协议与数字级准确率基准

> 阶段 3 门禁（CURRENT_ROADMAP 第 3 顺位）。前置：S01 关闭（R2/R3/R4 同 SHA
> 全绿）。本工作包把「准确率」从宣称变成可复算的门禁。

## 1. 两级基准合同（B2）

| 层 | 比对对象 | 状态 | 工具 |
|---|---|---|---|
| **L0 入库保真** | 事实库 `statement_line_item` ↔ 已验证抽取 YAML（P5 期完成来源核验） | **可执行，当前 1454/1454 全对（`scripts/accuracy_benchmark.py`）** | `scripts/accuracy_benchmark.py` |
| **L1 抽取准确率** | 抽取值 ↔ PDF 页级 ground truth（`answer_set.source_truth` 列，含页码/坐标） | 待 C 级出口执行期填入；L1 未到料前禁止宣称准确率 | 同脚本 `--level L1`（预留） |

纪律：L0 全对只是管线不丢数不改数；「准确率 X%」必须由 L1 支撑，且答案集
冻结后不得原地修改（修订 = 新版本文件 + supersedes 链）。

## 2. 协议四项（验收 §14.1 的可判定化）

1. **冻结样本**：当期入库报告全集（当前 5 家 14 份）+ 每报告 SHA-256；
2. **company-level holdout**：随机整公司留出（代码与答案集均不得接触），
   留出名单由用户或独立方抽取并签封；
3. **数字级答案集**：`answer_set_v*.yaml`，每条 = `source_pdf + 页码 +
   行名 + 列名 + 期望值`，L1 期由独立 oracle（U4 车道）核验；
4. **独立盲评**：报告渲染输出交未参与实现的第三方按固定 rubric 盲评，
   rubric 与评语入库。

## 3. 退出条件（全部满足才可宣称 C 级）

- [ ] L0 基准进 CI（现有 `accuracy_benchmark.py` 挂入任一 required job）；
- [ ] L1 答案集 ≥ 300 数值点、覆盖全部 14 份报告、oracle 独立核验通过；
- [ ] L1 准确率 ≥ 约定阈值（用户裁决），且 mismatch 逐一归因（抽取/映射/引擎）；
- [ ] holdout 公司全流程独立复算通过；
- [ ] 盲评零「严重事实错误」；
- [ ] 重述 supersedes 链（T10-B4）与溯源定位（T10-B3）在样本上可用。

## 3.5 交付进度（2026-09-15）

- ✅ L0 入库保真：1454/1454 全对（CI 可挂）；
- ✅ L1 页级答案集：1775/1795 值锚定源 PDF（98.9%；strong 972 / weak 803，
  未定位 10 行显式列出不丢弃）；`--level L1` 双向验证锚失效 0、值不一致 0；
- ⬜ 独立盲评与 holdout 抽签：需用户/第三方参与（不可由实现方代行）；
- ⬜ U4 oracle 对 L1 的独立复核：待外部到料。

## 4. 与 T10–T12 的边界

数据点级溯源、重述检测、AI 起草、只读 MCP 见
[PUBLIC--provenance-restatement-mcp.md](PUBLIC--provenance-restatement-mcp.md)；
数据扩张与行业基准见 [PUBLIC--data-expansion-benchmarks.md](PUBLIC--data-expansion-benchmarks.md)；
AI 问数见 [PUBLIC--ai-qa-v1.md](PUBLIC--ai-qa-v1.md)。三者均以本协议为质量
地基，不反向放宽。
