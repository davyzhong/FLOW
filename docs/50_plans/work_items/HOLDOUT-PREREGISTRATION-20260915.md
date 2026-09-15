---
doc_id: FLOW-WP-HOLDOUT-PREREG-20260915
title: 新批次 holdout 抽签规则预注册（签封件）
doc_type: work-item
status: sealed
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
sealed_by: qiming
sealed_at: 2026-09-15
applies_to: public-analysis
---

# 新批次 holdout 抽签规则预注册（签封件）

> 本文件在扩张批次财报到料**之前**签封；到料后不得修改本文件——任何修改
> 即视为预注册失效，需重新签封并废弃当批 holdout 资格。

## 预注册规则（Q8 用户确认）

1. **到料日定义**：10 家扩张公司财报 PDF 首次进入仓库
   `docs/knowledge-base/02_research/original/` 之日；
2. **抽签人**：qiming；
3. **抽签动作**：到料日，qiming 从当批公司名单中随机指定 **1 家**，
   指定结果以本文件追加记录（公司名 + 日期）形式固定；
4. **封存语义**：被指定公司的全部报表作为 holdout——抽取照常执行，
   但其 L1/L0 验证结果**单独成册**，且抽取完成后由独立方（U4 oracle
   车道或外部人）以源 PDF 对账后才可计入证据；
5. **不可变约束**：抽取代码在 holdout 公司验证完成前不得针对该公司做
   任何专项调整（防过拟合）——发现 bug 修管线 = 全局修复，允许。

## 抽签记录（到料后追加）

（无——待到料日填写）
