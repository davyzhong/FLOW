# 可复用的 Agent 接续提示词

## 从零理解并复述项目

```text
请先完整阅读 docs/knowledge-base/README.md 指定的最短阅读路径，再阅读原始资料索引。不要开始实现。请输出：1）FLOW 的产品定位；2）V1 用户、行业和核心场景；3）已批准架构；4）有效、被取代和未决的关键决定；5）当前下一步；6）你发现的任何矛盾或资料缺口。每个结论请引用对应本地文件。
```

## 从当前节点进入实施计划

```text
请阅读 docs/knowledge-base/00_start_here/AGENT_START_HERE.md、docs/knowledge-base/04_decisions/DECISION_LOG.md 和 docs/superpowers/specs/2026-08-29-flow-v1-design.md。先确认用户已完成正式规格的最终审阅。确认后，基于“端到端窄切片”原则编写详细实施计划；不要扩大 V1 范围，也不要直接写代码。
```

## 修改某个历史决定

```text
我要修改 FLOW 的一个已批准决定。请先在 docs/knowledge-base/04_decisions/DECISION_LOG.md 中定位对应决策 ID，再读取 CHANGE_IMPACT_MAP.md。先说明旧决定、修改原因、受影响的页面/数据/分析/报告/测试和需要更新的文件，得到确认后再修改设计文档。保留历史，不要静默覆盖。
```

## 核查某项设计的原始依据

```text
请不要只依赖总结。根据 docs/knowledge-base/06_sources/SOURCE_CATALOG.md 找到相关原始会话、研究文档和图片，区分“外部参考”“AI 曾经建议”和“用户最终确认”。给出证据链及本地文件引用。
```
