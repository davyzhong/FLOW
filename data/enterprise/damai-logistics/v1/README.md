---
doc_id: FLOW-DATA-DAMAI-PACKAGE-README-001
title: 大麦物流企业数据包说明
doc_type: navigation
status: current
version: 1.1
created_at: 2026-09-27
updated_at: 2026-09-27
owner: FLOW
applies_to: repository
---

# 大麦物流企业数据包 v1

本目录是大麦物流的可移植合成数据包，分为组织建制和经营业务两部分。所有人员、组织身份均为虚构演示数据，不包含可登录凭据。它旨在成为后续转换其他企业数据时遵循的目录与数据格式样板。

## 目录

```text
v1/
├── manifest.json                 # 包版本、合成声明、依赖来源、文件 SHA-256 与 JSONL 行数
├── organization/
│   ├── departments.jsonl         # 集团、事业部与职能部门
│   ├── positions.jsonl           # 岗位及归属部门
│   ├── roles.jsonl               # 用户身份与现有系统角色映射
│   ├── permissions.jsonl         # 现有 RBAC Action allow 集合的校验快照
│   └── users.jsonl               # 合成 actor、岗位、部门及角色
├── sql/                         # 预检、企业范围业务重置和结果核验 SQL
└── business/
    ├── canonical/                # 财务、经营、预算、客户、期间及维度事实
    ├── statements/               # 合成财务报表
    ├── operations/               # 经营指标与分部序列
    ├── forecast/                 # 静态预测侧车数据
    └── workbooks/                # 初始化来源工作簿
```

经营数据从仓库既有 `fixtures/damai/` 生成，不在本目录维护第二份人工编辑源。`manifest.json` 记录每个发行文件的 SHA-256 和 JSONL 行数；`organization/permissions.jsonl` 由系统 RBAC 当前 allow 集合生成，仅用于一致性校验，不作为动态授权输入。

## 构建与校验

在仓库根目录执行：

```bash
uv run --project services/api python scripts/build_enterprise_data_package.py build
uv run --project services/api python scripts/build_enterprise_data_package.py verify
```

`build` 将当前大麦业务 fixture 拷贝到发行目录、生成组织 SQL、校验组织引用并重算清单；`verify` 检查 synthetic 标记、组织/岗位/用户引用、企业命名空间、邮箱保留域、现有 RBAC Role/Action 快照、业务组织引用、路径边界、文件覆盖、SHA/字节数/JSONL 行数，以及组织 SQL 是否与 JSONL 源一致。构建可重复执行。

## 数据约定

- 企业标识固定为 `damai-logistics`（系统内需先存在此企业空间；初始化不会创建或改写企业空间），所有跨模块关联使用稳定 code，而非数据库生成 ID。
- JSONL 每行一个 UTF-8 JSON 对象，字段名使用英文 snake_case；金额和单位遵从业务源文件约定。
- 所有组织、岗位和用户记录必须有 `synthetic: true`。邮箱使用 `.example.invalid` 保留域；不生成电话、政府身份证号、密码、token 或密钥。
- 组织用户映射到 FLOW 当前已有六类系统角色之一。若系统授权矩阵改变，应重建权限快照并重新审阅，不得借数据包增加系统未批准的权限。
- `identity_kind` 用于标明 human、AI 或 service 类型；模拟身份本身不创建认证凭据。

## 初始化

先在目标系统完成平台自身部署和系统数据初始化（包含当前 Alembic head、企业空间、全局财务字典与指标定义）。然后在仓库根目录执行一次：

```bash
# 同步部门、岗位、合成用户与角色；重置并重建大麦业务数据
./data/enterprise/damai-logistics/v1/initialize.sh full

# 仅重置并重建业务数据，要求现有组织建制与包内业务引用一致
./data/enterprise/damai-logistics/v1/initialize.sh business
```

两种模式都在一个数据库事务内运行；出错时数据库变更回滚。`full` 会按稳定 code 同步组织包，停用发行包中已移除的组织/岗位/成员，并撤销其活动角色绑定。`business` 不写组织表或角色绑定，只检查业务引用并重建业务批次。两者只清理 `damai-demo-v1` 且关联到 `damai-logistics` 企业周期的数据。全局科目/准则/指标定义、企业空间、分析周期身份、追加式审计、公开财报发布历史和共享对象存储元数据均保留。

`sql/00_preflight.sql` 与 `sql/90_verify.sql` 是可单独审阅执行的只读检查；`sql/20_business_reset.sql` 是一键入口在事务内调用的企业范围清理 SQL。平台 schema 由 Alembic 部署，企业初始化脚本不会擅自升级数据库结构。不得单独执行重置 SQL 后跳过数据重建。
