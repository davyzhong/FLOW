# 可复用的 Agent 接续提示词

## 从零理解并复述项目

```text
请先完整阅读 docs/knowledge-base/README.md 指定的最短阅读路径，再阅读原始资料索引。不要开始实现。请输出：1）FLOW 的产品定位；2）V1 用户、行业和核心场景；3）已批准架构；4）有效、被取代和未决的关键决定；5）当前下一步；6）你发现的任何矛盾或资料缺口。每个结论请引用对应本地文件。
```

## 从当前节点继续 Pilot Readiness

```text
请按 docs/knowledge-base/README.md 的最短阅读路径读取当前状态、正式规格、D038/D039 和变更影响图，再读 docs/implementation/2026-09-04-review-repairs.md、docs/operations/authentication.md 与 docs/superpowers/plans/2026-09-03-flow-pilot-readiness-phase-2-security-deployment.md。核对当前代码与迁移头；文档基线是 2026-09-04 的 c1a59d1、0010_frozen_reports。Phase 1–10、数据工作台、报告中心与单用户认证已实现，R1–R9/N1–N3 已修复。继续安全部署剩余工作与真实对象存储补验，保留既有财务口径和不可变历史。明确区分历史门禁、本次验证、存储替身和真实存储证据；不要在真实试点前扩大 V1.1。按仓库 AGENTS.md 完成范围内验证、文档更新、清单哈希再生成、提交并推送。
```

## 核查当前部署与验收缺口

```text
请先读取当前项目状态和 2026-09-04 修复验收，再核对代码与运行环境。重点检查单用户认证的完整配置、0010_frozen_reports 升级兼容、真实 MinIO PutObject 超时、HTTPS/网络边界、备份恢复演练和结构化日志。不要改动业务数据或伪造旧报告 payload；旧快照缺少 payload 时应重新冻结。输出已验证事实、尚未验证的链路和所需补验步骤，历史测试通过不能替代当前生产就绪证据。
```

## 修改某个历史决定

```text
我要修改 FLOW 的一个已批准决定。请先在 docs/knowledge-base/04_decisions/DECISION_LOG.md 中定位对应决策 ID，再读取 CHANGE_IMPACT_MAP.md。先说明旧决定、修改原因、受影响的页面/数据/分析/报告/测试和需要更新的文件，得到确认后再修改设计文档。保留历史，不要静默覆盖。
```

## 核查某项设计的原始依据

```text
请不要只依赖总结。根据 docs/knowledge-base/06_sources/SOURCE_CATALOG.md 找到相关原始会话、研究文档和图片，区分“外部参考”“AI 曾经建议”和“用户最终确认”。给出证据链及本地文件引用。
```
