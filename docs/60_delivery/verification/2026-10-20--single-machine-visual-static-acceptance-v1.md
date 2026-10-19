---
doc_id: FLOW-VERIFY-SINGLE-MACHINE-STATIC-20261020-001
title: 单机视觉静态运行验收记录
doc_type: verification
status: draft
version: 1.0
created_at: 2026-10-20
updated_at: 2026-10-20
owner: FLOW
applies_to: verification
code_sha: 9ec0611562569b33bc3dac28c16445aa9470b150
commit_refs: "9ec0611562569b33bc3dac28c16445aa9470b150;433f5a7b7b04b29f499594f06f3f991f71f4a904"
evidence_refs: "[isolated-sqlite-cold-start,damai-demo-verify-19-of-19,offline-html-zero-network,desktop-mobile-screenshots,sqlite-local-restore-stage2,github-actions-39284568713]"
---

# 单机视觉静态运行验收记录

## 结论

本机阶段 7 的运行、数据和视觉验收通过；准确 SHA 的 GitHub CI 尚未完成，因此不把整个工作包标记为完成。环境使用一次性隔离数据目录 `/tmp/flow-stage7-20261020`，没有连接常驻用户数据。

## 环境与运行

- 代码基线：`9ec0611562569b33bc3dac28c16445aa9470b150`。
- 本机 production build：`make flow-bootstrap` 成功；之后用 `make flow-init` 和 `make flow` 完成冷启动。
- 运行时：SQLite Alembic `sqlite0001`–`sqlite0004` 成功；API `127.0.0.1:8000` 和 Web `127.0.0.1:3000` 均返回 HTTP 200。普通启动路径没有 Docker/PostgreSQL/Redis/MinIO 依赖。
- 生成大麦演示批次后，`scripts/verify_damai_demo.py --check-storage` 输出 `ok=true`、`total=19`、`failed=[]`。数据为合成演示数据，不是真实阿里巴巴、菜鸟或客户经营披露。
- 发行包 manifest SHA-256：`6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`；批次 ID：`01a154ea-455d-79fb-8521-072795629bec`。

## 页面和离线静态快照

总览页面实际显示营业收入、营业利润、毛利率、经营现金流、订单数量、趋势图、现金流桥、杜邦拆解、费用结构、行动项和来源口径。过期数据状态有提示；金额按两位小数、订单数按整数显示。

`node scripts/export_cockpit_snapshot.mjs --url http://127.0.0.1:3000 --output docs/assets/screenshots/cockpit-single-machine/offline-preview.html` 生成自包含 HTML 与 PNG。通过 Playwright 用 `file://` 打开离线页，检查到标题和图像加载成功、8 个 KPI、内嵌业务 API JSON 和 stale 状态均存在；外部网络请求 0、页面错误 0。离线文件适合阅读快照，动态筛选与页面跳转仍需本地应用。

真实浏览器截图记录在[截图索引](../../assets/screenshots/README.md)：桌面总览 1440×2350、移动总览 390×4282、盈利分析 1440×1777。移动页面无水平溢出，截图时页面与控制台错误均为 0。

## 备份恢复证据

SQLite 与内容寻址文件目录备份恢复到新隔离目录、逐文件哈希检查、来源字节/FactTrace/报告和快照哈希及驾驶舱结果一致的既有证据，见[单机架构收敛验收记录](2026-10-18--single-machine-runtime-convergence-v1.md)。本轮没有对现有数据库做恢复或覆盖。

## CI 状态与剩余事项

准确 SHA `433f5a7b7b04b29f499594f06f3f991f71f4a904` 的 GitHub Actions run `39284568713` 为 `failure`。`static-python` 的 M6 因本验收记录未包含必填 `commit_refs` 和 `evidence_refs` 而失败，现已补齐并在本地 M6 验证通过。`user-closure-e2e` 的前三项通过；标准 Excel 上传旅程在等待“确认映射并校验”按钮 60 秒后失败，当前已知现象是该按钮未出现在页面，尚未获得根因证据。其他作业及 5 个数据契约 shard 成功。本地修正不能替代新的准确 SHA CI，也不能把该 E2E 失败归为纯环境故障；需继续诊断并在新 SHA 上复验。
