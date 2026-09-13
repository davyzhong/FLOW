# U8-D 干净环境部署验收记录

- 时间：2026-09-13 09:31:24 +0800
- 方式：隔离 compose project（u8accept，全新卷）模拟干净目标环境

INFO  [alembic.runtime.migration] Running upgrade 0023_operations_overview -> 0024_operations_publication, 经营报告发布：修正快照版本键并复用统一 PublicationAttempt。
- 健康检查：api=200 web=200（期望 200/200）
- 干净库空态：statements=0（期望 0）
种子导入: {'metrics': 64, 'mappings': 28, 'subjects': 167, 'standards': 48, 'templates': 32}
最小财报种子+冻结: 1
U8-A 旅程开始 report_id=01a09864-6df2-78bd-99ec-c1a89db6948e
冻结快照 snapshot_id=01a09864-7189-73d5-ad2e-8ac0db175c98
运营发布完成 pub_snapshot=01a09864-73c8-7fb6-8922-e68609eb4845
DOWNLOAD format=html attempt=01a09864-7444-7d2c-9150-0c6961b305a7 sha_match=True
  expect=0100ff77ba31e6a5… actual=0100ff77ba31e6a5…
DOWNLOAD_SUMMARY checked=1 sha_ok=1
失败态 未知尝试 HTTP 404（期望 404）
已从 MinIO 删除对象 raw/01/0100ff77ba31e6a5f3c5be58b8cc5db8ecea736faba387b2a24f51e2be097981
失败态 对象缺失 HTTP 409（期望 409）
U8-A 旅程结束，证据写入 docs/operations/u8a-journey-evidence.jsonl
== 5/5 恢复后校验 ==
恢复后 statement_report 行数：1
备份恢复演练 PASS
## 已知限制
- 自签 TLS 仅用于本地验收（infra/nginx），生产需换真实 CA 证书
- 量价类指标（volume_growth/price_change_rate）依赖 L2 内部数据，绑定如实缺失
