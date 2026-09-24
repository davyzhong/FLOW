---
doc_id: FLOW-DESIGN-PROVENANCE-LINK-20260924
title: Statement 溯源真实来源链接——设计输入（半页）
doc_type: design
status: draft
version: 0.1
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
applies_to: web-frontend
decision_refs: [D042, D043]
knowledge_release: flow-knowledge-2026-09-12.1
---

# Statement 溯源真实来源链接——设计输入

> 背景：T10-B3 已完成数据点级溯源（page_number + page_anchor，0029/0030）。
> 现状缺口：前端只展示"第 N 页"，用户无法一键跳到**公开披露原文**。
> 本文档为半页设计输入，评审后再实现。

## 1. 数据模型（不动迁移，复用现有列）

- 复用 `statement_line_item.page_number` / `page_anchor`（0029/0030 已含四种锚定模式）；
- 报告级新增信息**只在 YAML source_ref 与 seed 元数据**：`source_url`（公开披露原始 URL）
  与 `source_mirror_url`（镜像 URL，若有）。不入新列——URL 属报告级静态属性，
  走 `statement_report.source_ref` 的同源扩展字段；
- 归档铁律不变：URL 只是指针，法律级证据仍是本地不可变档案 + SHA-256
  （D042）；URL 失效不影响档案效力。

## 2. 前端联动（ProvenanceBadge）

- 报表数字 hover → 现有 Badge 展开为三层：**值 + 页码 + 锚定模式**（strong/weak/
  sign-flip/visual-verified 各有图标与文案，visual-verified 附证据图缩略）；
- Badge 第二行新增「查看原文」链接：`source_url#page=N`（PDF page fragment），
  新窗口打开；镜像 URL 作为降级小字链接；
- 港交所/巨潮 URL 可能失效：链接旁标注归档 SHA 前 8 位，点击失败时引导至
  「本地档案已冻结」说明文案——把失效暴露出来，不做静默兜底。

## 3. 验收口径

- 每份已入库报告必须有 source_url（seed 时必填校验）；
- 前端八页面报表数字 hover 可见 Badge + 原文链接；链接与页码逐点可核；
- 不新增迁移、不改抽取器；纯 API 序列化扩展 + 前端 Badge 增强。
