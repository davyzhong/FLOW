---
doc_id: FLOW-WI-ORG-LEDGER-001
title: 企业组织建制与经营账套初始化包
doc_type: work-item
status: active
version: 1.0
created_at: 2026-09-27
updated_at: 2026-09-27
owner: FLOW
depends_on: [FLOW-WI-DAMAI-FULL-YEAR-001, FLOW-SPEC-SECURITY-V1]
acceptance_refs: [enterprise-package-v1]
applies_to: repository
supersedes: []
superseded_by: null
---

# 企业组织建制与经营账套初始化包

## 目标与已批准行为

把大麦物流的合成组织和经营数据整理成可移植、可校验、可重建的企业数据包，
作为未来其他企业按相同格式转换数据的模板。包分为两个独立模块：

1. **组织建制**：企业部门、岗位、角色、权限布局、模拟用户账号和模拟身份资料；
2. **业务数据**：财务事实、经营事实、预算、应收回款、财报、导入/分析快照、
   Finding、冻结报告及所需来源文件。

两个模块共享企业标识和稳定业务键。组织建制与业务数据可分别管理。完整初始化
自动把组织建制同步到发行包状态并重建业务数据；业务重置保留现有组织建制，只
重建业务数据。初始化只作用于发行包指定企业。数据覆盖由独立备份流程负责，
初始化流程不弹出版本/人员选择，也不自动备份。

系统级企业空间、登录认证集成、全局科目/准则/指标字典、数据库结构和全局路由
权限仍由目标系统预先创建或迁移，不由企业数据包覆盖。所有身份均标记为合成；
不得生成可用于真实登录的密码或密钥。组织包可包含展示身份和 actor 稳定键，
登录凭据仍由系统认证配置管理。

## 当前结构缺口与边界

- 现有大麦发行包位于 `fixtures/damai/`，包括 canonical JSONL、财报、运营侧车、
  预算工作簿和 manifest；一键 seed 位于 `scripts/seed_damai_demo.py`，通过
  `flow_api.fixtures.damai.loader` 走领域服务。
- 当前 `enterprise` 只有企业 code/name；`role_binding` 只有 actor_id、角色、
  enterprise_id 与启停状态。`dim_organization` 是财务/经营数据维度，不是完整
  人员目录；没有部门/岗位/用户个人资料及权限模板表。
- `RoleBinding` actor_id 必须服从已批准 RBAC 规格，种子身份不能通过请求体或
  fixture 伪造认证 Principal。审计事件是追加式，不得作为可重置业务数据清除。
- 对象存储按内容寻址且可被其他企业共享；只能删除确认专属于目标企业且无其他
  引用的对象。全局 `stored_object` 元数据不得随单企业重置级联删除。
- 项目现行范围仍不承诺公共多租户 SaaS。此工作交付企业范围明确的数据包与单企业
  重置边界，不声称完成 SaaS 级认证、租户路由或数据库隔离。

## 建议发行目录

```text
data/enterprise/damai-logistics/v1/
├── manifest.yaml                 # 企业、包/模块版本、合成标记、依赖、校验和
├── organization/
│   ├── departments.jsonl         # 稳定 code、树关系、名称、状态
│   ├── positions.jsonl           # 岗位与部门关系
│   ├── roles.jsonl               # 企业角色模板及系统角色映射
│   ├── permissions.jsonl         # 角色到已存在 Action 的显式授权映射
│   └── users.jsonl               # 合成 actor_id、姓名、岗位、部门、状态
├── business/
│   ├── canonical/                # 现有 flow.excel.v1 规范事实和维度
│   ├── statements/               # FY2025/FY2026 合成财报
│   ├── operations/               # 运营与分部序列
│   ├── forecast/                 # 明确标记 static-only 的预测侧车
│   └── sources/                  # 初始化需引用的原始工作簿/文件
├── sql/
│   ├── 00_preflight.sql          # 检查 PostgreSQL、schema 版本、目标企业
│   ├── 10_organization.sql       # 组织表就绪后生成的幂等企业组织 seed
│   ├── 20_business.sql           # 仅针对 manifest enterprise 的事务性业务重置/seed
│   └── 90_verify.sql             # 行数、引用完整性、哈希和业务不变量检查
└── initialize.sh                 # 一个命令：preflight → full 或 business-only → verify
```

目录是交付格式目标；实现时应复用现有 canonical/工作簿/财报文件，避免形成第二
份可手改真相。manifest 固定 schema/contract/module 版本、稳定企业 code、合成
标记、系统级依赖版本、组织业务引用关系、每文件 SHA-256/行数与验证规则。

## 初始化语义

- `initialize.sh full`：检查系统迁移头及全局字典依赖；确认 manifest 企业存在；
  同步组织包；在单个数据库事务中仅删除并重建该企业的业务记录；装载源文件；
  走现有 Intake、Statement Review、Snapshot、Analysis、Freeze 服务路径；校验后
  提交。任一步失败则回滚该企业业务数据库变更。
- `initialize.sh business`：组织记录不变；清理并重建 manifest 企业拥有的业务
  记录；要求包中所有组织引用能解析到现存稳定 code；不可解析作为包完整性错误。
- 对不再出现于完整组织发行包的模拟用户或组织主体，撤销访问绑定并停用主体，
  不删除会被审计或历史引用的主体行。
- 全局指标、科目、准则与审计事件不在企业重置清单中；不能使用无范围的
  `TRUNCATE`、`DROP SCHEMA` 或全库删除语句。
- PostgreSQL SQL 文件提供可审阅的初始化/数据变更入口；应用服务仍负责需要质量
  审核、血缘、发布和对象存储的业务链。SQL 与应用 seed 必须由同一 manifest
  生成/校验，避免两套数据漂移。

## 实施顺序与验收

1. 固定目录、manifest schema、稳定 code 与组织/业务引用合同；用现有大麦数据构建
   完整 v1 发行包并校验文件覆盖和哈希。
2. 实现纯文件 preflight/校验器：拒绝非 synthetic 标记、重复 code、缺少依赖、
   跨企业引用、错误版本、缺文件、SHA/行数不符与非法组织引用。
3. 为组织数据补齐持久化模型和受约束服务；仅创建组织用户、岗位、部门、角色映射
   所必需的 schema。**此步之前必须取得用户对具体迁移表与数据生命周期的明确批准**；
   未批准时只完成不落库的数据包与校验器。
4. 为企业边界登记所有被重置的业务表及 lineage；按依赖顺序执行事务性删除/重建，
   保留系统配置、共享对象和追加审计；确认失败回滚无部分写入。
5. 生成可审阅 SQL 和单一入口命令；支持 `full` 与 `business` 两个稳定动作，不提供
   互动式人员/口径选择。
6. 在隔离 PostgreSQL + 对象存储栈做首次初始化、重复初始化、仅业务重置、坏包拒绝、
   事务失败回滚、跨企业不受影响、组织保留/同步及恢复后 verify；运行全库规定门禁。
7. 更新数据包 README、项目状态和路线图验收证据；只把本任务文件纳入提交，CI 全绿后
   将工作包标为 completed。

### 完成条件

- 一个命令能初始化完整大麦企业包；业务重置保留组织数据；完整初始化自动同步组织
  并重建业务数据；两条路径都幂等且只改变 manifest 指定企业。
- 包内有完整组织模块与业务模块、SQL、标准目录文档、manifest、版本/依赖、哈希、
  来源说明及合成数据声明；其他企业可以按同一合同替换数据。
- 至少验证多部门/岗位/人类与 AI 服务角色样本、权限映射、账套引用和现有页面流程；
  旧的大麦验收 19/19 与 9/9 不回退。
- 没有真实凭据、真实个人信息或无范围数据库语句；保留其他企业、全局配置、追加审计
  和被共享的对象。

## 权限与顺序门禁

本工作包已获准创建合成企业数据包、SQL 文件和初始化入口。已知的组织目录/岗位/人员
数据库 schema 尚不存在；根据项目 AGENTS 规则，只有在写出具体迁移 DDL、表关系、
约束和数据保留方式后，才单独请求批准数据库 schema 变更。取得批准前不执行迁移，
也不在共享开发库执行任何清理/初始化。
