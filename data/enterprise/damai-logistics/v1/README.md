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

`build` 将当前大麦业务 fixture 拷贝到发行目录、校验组织引用并重算清单；`verify` 检查 synthetic 标记、组织/岗位/用户引用、邮箱保留域、文件哈希和行数。构建可重复执行。

## 数据约定

- 企业标识固定为 `DAMAI_LOGISTICS`，所有跨模块关联使用稳定 code，而非数据库生成 ID。
- JSONL 每行一个 UTF-8 JSON 对象，字段名使用英文 snake_case；金额和单位遵从业务源文件约定。
- 所有组织、岗位和用户记录必须有 `synthetic: true`。邮箱使用 `.example.invalid` 保留域；不生成电话、政府身份证号、密码、token 或密钥。
- 组织用户映射到 FLOW 当前已有六类系统角色之一。若系统授权矩阵改变，应重建权限快照并重新审阅，不得借数据包增加系统未批准的权限。
- `identity_kind` 用于标明 human、AI 或 service 类型；模拟身份本身不创建认证凭据。

## 初始化状态

当前交付包含完整文件发行包、组织样本、业务源副本、权限快照和内容校验器。数据库组织表、单企业业务数据清理/重建 SQL、事务化装载入口及数据库集成验收尚未交付；这些依赖单独批准的组织 schema 迁移以及对现有业务数据依赖链的实现。不能把本文件包构建命令当作数据库初始化命令使用。
