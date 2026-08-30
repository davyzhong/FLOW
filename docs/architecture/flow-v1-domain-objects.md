# FLOW V1 领域对象

## 标识与版本

聚合实体使用 UUIDv7，以兼顾全局唯一和写入时序。稳定业务定义（例如指标）另有不可变业务代码，并以 `(code, version)` 标识定义版本。金额与比率使用 PostgreSQL `NUMERIC` 和 Python `Decimal`，不允许浮点数进入财务计算。

## 数据聚合

| 聚合 | 主要对象 | 生命周期所有者 |
|---|---|---|
| 数据接入 | Analysis Batch、Stored Object、Source File、Mapping Version、Import Version | Intake |
| 质量与血缘 | Quality Issue、Reconciliation Result、Transformation Event、Source Record | Intake / Quality |
| 标准数据 | 8 个公共维度、4 个财务经营事实 | Canonical Data |
| 指标 | Metric Definition、Metric Snapshot、Metric Value | Metric Engine |
| 分析调查 | Finding、Driver Contribution、Evidence、Review Event、Conclusion | Investigation |
| 报告发布 | Report Snapshot、Report Snapshot Item、Publication Attempt | Publishing |

Analysis Batch 可以产生多个 Import Version，但每个批次最多只有一个正式发布版本。每条标准事实保留 `import_version_id` 与 `source_record_id`，Source Record 可定位到源文件、工作表、行、列和标准字段。

## 不可变边界

- Stored Object 以 `raw/{sha256前两位}/{sha256}` 寻址，相同字节只保留一个对象身份；
- 已发布 Import Version 不被覆盖，映射或规则变化产生新版本；
- Metric Snapshot 冻结一个批次的确定性计算结果；
- Review Event 只追加，不修改历史；
- Report Snapshot 固定引用一个 Metric Snapshot，多次导出通过 Publication Attempt 留痕；
- 页面、AI 和导出器不能跨过上述边界直接读取原始 Excel。
