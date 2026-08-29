# 会话档案索引

## 1. 历史 ChatGPT 完整会话

- 文件：[Finance_Intelligence_OS_完整会话归档.md](raw/chatgpt/Finance_Intelligence_OS_完整会话归档.md)
- 原始位置：`/Users/qiming/workspace/FLOW/Finance_Intelligence_OS_完整会话归档.md`
- 内容：早期 Finance Intelligence OS 产品讨论、五篇资料补充、产品抽象、分析层级、Driver Model、对象模型和 MVP 思路。
- 用途：理解最初为什么从“财务驾驶舱”上升到“AI 原生财务经营分析平台”。

相关 ChatGPT 标识：

- 对话引用：`chatgpt-conversation://6a91167c-5538-83ec-b1e1-59884f96982c`
- 分享链接：`https://chatgpt.com/share/6a913133-66a8-83ec-939d-a88cfa12734b`

## 2. 当前 Codex 会话原始记录

目录：[raw/codex](raw/codex)

保存了与当前项目任务相关的 Codex JSONL 会话快照：

- `rollout-2026-08-28T14-41-27-01a0471a-1689-7270-8dc5-f2bf084e4db9.jsonl`
- `rollout-2026-08-29T14-00-01-01a0471a-1689-7270-8dc5-f2bf084e4db9_01a04c1a-86bd-7960-9db5-80ae486d1bd4.jsonl`

这些文件包含机器级事件、消息、工具调用和阶段性上下文，适合审计或最大程度恢复当时环境。它们可能包含系统元数据、重复上下文和压缩记录，因此不适合作为首读材料。

## 3. 当前 Codex 会话可读转录

目录：[readable](readable)

可读转录由 JSONL 机械提取，仅保留 user 和 assistant 消息，未改写内容。它用于快速阅读，但以下信息可能只存在于原始 JSONL：

- 工具调用参数和完整输出；
- 系统与开发者上下文；
- 图片的二进制或附件元数据；
- 部分压缩、恢复和会话状态事件。

## 4. 阅读建议

如果目标是理解产品，不要从原始 JSONL 开始。推荐顺序：

1. 当前项目状态；
2. 决策日志；
3. 正式设计规格；
4. 当前 Codex 可读转录；
5. 历史 ChatGPT 完整会话；
6. 只有在需要核查遗漏或原话时再读取 JSONL。

## 5. 重复与时间边界说明

Codex 在上下文压缩、续接或客户端恢复时可能生成多个 rollout 文件，因此内容可能部分重叠。知识库不删除重复内容，以避免损失原始上下文。决策日志已经按实际决策顺序归并。

