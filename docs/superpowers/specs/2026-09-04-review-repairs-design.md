# 审查九项修复设计

依据：用户批准先三项 P1 后六项 P2；复审 R1–R9。保留 D028/D033/D037/D039，不扩展财务口径。

## P1

- ReportSnapshot 增加可空 frozen_view JSONB，冻结完整 ReportView（含 run、时间、结论、证据 IDs）后不可修改。新报告重试只反序列化 frozen_view；旧报告没有 payload 时拒绝重新渲染，已有产物下载保留。相同冻结内容幂等复用，内容变化生成递增版本；同一 MetricSnapshot 行锁序列化版本分配。显式 run 必须 published 且绑定所选指标快照。
- Evidence 降级为 rejected 时，若 Finding 已 approved，原子追加 returned 审计并退回 in_review。Finding 决策、证据决策、结论编辑和冻结资格检查共享 Finding 行锁，冻结再次校验全部证据 verified 和四项结论完整，空证据不可签发。
- Intake confirm/validate 从 mapping_spec 恢复已持久化 proposal，核对 hash、source ID/SHA 与 batch，使用人工修正后的列提取，不重建自动映射冒充确认版本。

## P2

- 前端 override 传真实 source SHA；显示质量问题、原因输入和逐条 warning 确认，确认后刷新导入状态，阻断问题可返回修正映射。
- Copilot 成功请求提交审计；大纲在指定 batch/published 范围内选 run。
- PPT 正文使用有效边界、字号和分页；下载代理保留受控 Content-Disposition，按格式回退文件名。

## 验证与兼容

先写失败回归，再修复；使用独立 PostgreSQL，禁止清空用户库。覆盖冻结后更改状态、新 run、新报告版本、显式跨快照 run、旧无payload报告、证据降级审计、手工映射端到端、warning UI、独立Session审计读取、双batch、大纲/PPT布局与文件名。
新增鉴权/CI三项 N1–N3 单独跟踪；必要契约生成会如实记录其对既有漂移的影响，不声称安全部署完成。
