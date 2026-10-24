---
doc_id: FLOW-VISUAL-LANGUAGE-README-20261024-001
title: FLOW 可移植视觉语言包
doc_type: product
status: canonical
version: "1.0"
created_at: 2026-10-24
updated_at: 2026-10-24
owner: FLOW
decision_refs: [D055]
applies_to: product-visual-language
---

# FLOW 可移植视觉语言包

本目录保存 FLOW A+C 视觉语言中与技术栈无关的语义 token、Web token 导出与表达范式。它是一个可复制的设计资产，不是 npm 包，不在运行时发请求，也不包含任何业务数据。

## 目录约定

- `tokens.json`：颜色、字体、间距、形状、层次和图表色的唯一取值源。
- `tokens.css`：由 `scripts/build_flow_visual_language.py` 生成；不要手工编辑。
- `patterns.md`：可复用的页面和图表结构、语义边界、响应式与可访问性规则。
- `specimen.html`：离线样式样例，只有占位标签和布局示意，不含经营数字或产品状态。

## 复制到其他项目

CSS 项目可直接复制 `tokens.css` 并通过 `var(--flow-...)` 取值；将 `tokens.json` 与 `patterns.md` 一并保留，可映射至 SwiftUI、原生 Android、文档或其他设计系统。修改 token 后在 FLOW 中运行：

```bash
python3 scripts/build_flow_visual_language.py
python3 scripts/build_flow_visual_language.py --check
```

生成的消费映射位于 `apps/web/lib/visual-tokens.generated.ts` 和 `services/api/src/flow_api/visual_tokens.py`。外部项目无需引入 FLOW 运行时或发布依赖。

## 原则

视觉样例不是真实财务事实；数据颜色不能取代正负/缺失文字标识；不能为了匹配示意构图而填补缺失数据。字体使用可回退的本地字体栈，不依赖外网下载。
