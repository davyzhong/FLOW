---
doc_id: FLOW-VERIFY-PUBLIC-SAMPLE-FREEZE-20260929-001
title: 公开财报 C 级样本冻结与独立验证审计
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-09-29
updated_at: 2026-09-29
owner: FLOW
commit_refs: "[eb2b7f3c, 727c3d94]"
evidence_refs: "[sample-freeze-14-reports, source-pdf-and-yaml-sha256, l0-1532, l1-1776-located, oracle-audit-5-files, historical-holdout-199-not-comparable, new-holdout-no-run-artifact, c-level-no-go]"
applies_to: public-analysis
supersedes: []
superseded_by: null
---

# 公开财报 C 级样本冻结与独立验证审计

## 结论

14 份报告样本、活动抽取 YAML、原始 PDF、报告身份映射、行身份修订表、L1 v5、登记清单及实现提交已形成可确定性重建的版本化冻结文件：
[`c-level-freeze-2026-09-29-v1.yaml`](../../../validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml)。冻结内容包括每份 PDF 与活动 YAML 的 SHA-256、报告身份和分项计数；代码身份为 `eb2b7f3cbadec0c36eb4b36473c6321d69aa4fff`，其准确 SHA CI run `36478301484` 为 17/17 success。

**本次审计结论为 C 级 No-Go（证据门槛未满足），不是数据准确率判定失败。** L0 可复算覆盖键 1532 项，L1 页锚 1776/1776；页锚覆盖仅证明条目可定位，不等于独立 oracle 对照，也不等于 100% 准确率。以下缺口仍在：

- 冻结的 14 份目标报告没有任何一份登记了逐份完整独立行项目 oracle（0/14）；当前 L1 v5 是被测答案集，不能反过来充当独立 oracle。
- 已登记的 5 份 oracle 属于其他 holdout 样本，仅为关键项目与补充行的人工转录，不是完整财报 oracle；其 SHA 当前均已核实匹配。
- 2026-09-24 三份旧 holdout 首跑合计 199 行，抽取 0 行、199 行不可比较。它是保留的失败首跑证据，不可计为通过。
- 2026-09-25 抽签的小米 2026H1 与阿里 FY2027Q1 已有报告与 oracle，但仓库没有发现两者的首跑 diff artifact；因此本次不宣称 holdout 已运行或通过。首跑须在路线图 U04 适配后、未调参状态下执行。
- 已有 11 份材料、1530 格 AI 交叉评是抽取证据材料评审，不是本工作包要求的完整数字 oracle，也不是报告渲染输出的盲评 rubric 验收。

## 冻结范围与可复验方式

冻结文件记录 14 份报告的 PDF SHA、活动 YAML SHA，以及：

- `answer_set_sources.yaml`：报告身份映射 SHA-256 `760eecf6d4beb485307ea6e451b860b8d2d7ad39fdd53ba2908d96da6e5f6ec1`；
- `answer_set_l1_v5.yaml`：SHA-256 `788f2d004fd8b9c9f9a9b6006df3f9f2b419d3458465aa414319fae2b3b49c23`；
- `public-row-identity-map-v1.csv`：SHA-256 `76410a8886940e2e11b26485ef3d2a276439fc0c1f5a7dd75df6cf47c49a4753`；
- 财报登记 `manifest.yaml`：SHA-256 记录在冻结文件中；本轮同时修复了登记 YAML 中 `NYSE:` 未加引号导致无法解析的问题。

重建命令（从仓库根目录；输出临时文件即可对比，不会写数据库）：

```bash
cd services/api
uv run python ../../scripts/build_public_financial_sample_freeze.py --out /tmp/flow-c-level-freeze-repro.yaml
cmp ../../validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml /tmp/flow-c-level-freeze-repro.yaml
```

生成器会 fail-closed 检查恰为 14 份报告、身份映射一一对应、PDF 与 YAML 存在、L0/L1 汇总符合 1532/1776/1776/0，并复核登记 oracle 当前 SHA。

## Oracle 登记哈希审计

5 份 holdout oracle 的当前声明 SHA 均与文件字节一致。小米与阿里 FY2027Q1 的原历史声明不匹配，已在 `manifest.yaml` 追加 `oracle_sha256_previous_claim` 保留旧声明，并将当前 `oracle_sha256` 改为实测完整 SHA；审计生成器在冻结清单中同时保留当前 SHA、旧声明与历史差异：

| 样本 | 历史声明 SHA | 当前实测/登记 SHA | 当前一致 |
|---|---|---|---|
| 小米 2026H1 | `facdd5e711bb7a86a8a88ddf1e6dc9053f4d0f64` | `104f1eebdae0b5f7579408b1830b5a8537447bc559f2edad26aa43fec9931d36` | 是 |
| 阿里 FY2027Q1 | `6a3120f72806938581e2dad8d28105f4a633f299` | `1b6fb5e2cef2804fcd53a037b5c65c64ee012368a924be4f6d5417139800ace9` | 是 |

其余三份 Tencent FY2025、SF 2026H1、ZTO 2026Q1 的登记哈希与当前文件也一致。没有改写 oracle 数值或原始报告。

## 独立验证材料边界

现有独立交叉评结果的自身统计为：1530 格总清单、42 格确认异常、109 格口径/列义存疑、200 格初始不可完整核对。后续对原件的逐格裁决与 JDL 英文版复核已另行归档；但这不改变评审当时的材料边界，也不能替代 14 份完整独立逐行 oracle 或报告成品盲评。

抽取器首跑及新 holdout 状态以冻结文件的 `independent_validation` 为机器可读审计结果。小米/阿里新留出没有发现首跑 artifact 时，生成器仅报告“未发现仓库记录”，不推断为已运行或从未运行。

## 验收状态与下一步

本步骤交付：确定性冻结生成器、14 份样本冻结清单、manifest/oracle YAML 解析与哈希回归、独立证据审计。实现与本轮新增代码经过 6 项定向测试；本次文件变更的全量脚本测试、文档门禁和同 SHA CI 结果在提交后补记。

当前 C 级 No-Go 的原因是独立证据缺口，而非 L0/L1 锚覆盖缺失。路线图下一项按顺序为 U04：修复版式适配、保留三份旧失败首跑，再对小米与阿里两个冻结候选执行未调参首次运行并保存完整机器结果。不得先看输出调参后再称其为 holdout；若适配接触候选则依协议降级并重新启用候选。完成 U04 后再做 L1 独立 oracle 对照与最终 Go/No-Go。盲评如仍无法由不参与实现的不同模型独立执行，记录不满足及重启条件，不伪造独立性。

本轮只读和本地生成，没有连接常驻数据库；未修改原始 PDF 或历史 P5 YAML。
