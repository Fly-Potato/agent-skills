---
name: coordinating-codex-subagents
description: Use when one task spans two or more repositories or independently built or deployed projects with distinct ownership and requires active Codex-to-Codex consultation about implementation, business semantics, integration contracts, or joint debugging. Do not use for same-repository parallel work, unrelated multi-repo tasks, independent top-level threads, or explicit Orca orchestration and handoffs.
---

# 协调 Codex 子代理

## 核心原则

把跨项目协作组织成由 root coordinator 管理的 session tree。为每个项目指定唯一写入所有者，用完成任务所需的最少 Agent 协作；跨项目结论必须有当前代码、测试、schema 或运行结果作为证据，并由 root 复核后再对用户确认。

## 判断是否适用

同时满足以下条件才使用：

- 涉及至少两个 Git 仓库，或具有独立构建、测试、发布边界的项目；
- 每个项目需要明确且不重叠的所有者；
- 项目间存在实现咨询、业务语义、参数契约或联调依赖，需要 Agent 间主动问答。

多个仓库中的任务彼此独立、同一仓库内普通并行，或只需一次性读取另一项目时，不使用本 Skill。用户明确要求 Orca、独立顶级 Thread 或完整所有权移交时，改用对应的 `orchestration` 或 `orca-cli` Skill。

## 判断创建授权

先检查当前会话是否提供原生 sub-agent 工具，确认所有项目目录都在允许访问范围内，并记录各项目初始 Git ref 与工作树状态。

- 用户已经明确要求“创建”“启动”或“并行运行”sub-agent，且项目、职责和读写范围足够明确：视为已经授权，直接按范围执行，不重复确认。
- 用户仅调用本 Skill、要求分析或要求先给方案：不视为创建授权。先展示下表并询问是否创建。
- 执行中新增项目、扩大写入范围、改变所有权或产生新的外部副作用：重新确认变化部分。

| Owner | 项目根 | 读写所有权 | 依赖与提问方向 | 预期产出与验证 |
| --- | --- | --- | --- | --- |

调用本 Skill 本身不等于授权创建。未获得明确授权时，不得调用 `spawn_agent`，也不得用角色扮演声称已经创建 Agent。

## 协调流程

1. 先确定唯一所有者和最少 Agent 数量。root 可以直接负责一个项目；不要为了形式上的“一项目一子代理”重复分派。
2. 为每个 sub-agent 写清项目绝对路径、只读或读写范围、任务目标、验收标准、基准 Git 状态，以及禁止暂存或提交等授权边界。
3. 告知 worker：所有 Agent 共享文件系统，所有权是协作约束而不是 sandbox；单个文件只能有一个写入者，不得撤销或覆盖他人改动，也不得越界处理另一个项目。
4. 向用户报告每个 sub-agent 的 canonical name 或 Agent ID、项目所有权和状态。
5. 跨项目问题默认由 root 转发，避免不可见的点对点协商。用 `send_message` 向运行中的 Agent 提问；Agent 空闲且需要继续工作时用 `followup_task`；用 `list_agents` 核对状态并用 `wait_agent` 等待结果，避免忙轮询。
6. 用户取消、替换任务或旧任务已失效时，先用 `interrupt_agent` 中断仍在运行的 Agent，再继续新任务。中断不会回滚文件；随后检查每个项目的工作树并报告残留改动，不得静默忽略或擅自撤销。
7. 要求回答包含 Git ref 与工作树状态、文件路径或符号、测试/schema 依据、确定结论和未确定项。sub-agent 的摘要只是待核实输入，root 必须复核关键 diff、契约和验证原始结果。
8. root 负责识别契约冲突、组织 provider 到 consumer 的联调顺序，并只在证据闭环后汇总最终结论。

跨项目询问使用以下最小结构：

```text
目标项目/Agent：
调用方与提供方：
模块或符号：
问题：
需要确认：参数、返回、错误、兼容性、重试、幂等或时序
证据要求：Git ref、当前代码、测试、生成 schema 或运行结果
```

如果接口文档或 schema 不清楚，让负责该项目的 Agent 明确指出缺口；不要由调用方 Agent 自行推断。不同项目结论冲突时，保持为未决问题并继续追问，不能选择性采信一方。

## 收尾与回退

root 最终检查各项目的 Git ref、工作树差异、相关测试或 schema 输出，再汇总证据位置、受影响项目、已确认契约、未决问题和联调结果。只有任务授权包含文档修改时，才把结论写入版本化契约。

如果工具不可用，明确说明无法创建原生 sub-agent，并建议独立 Thread 加共享交接文档；如果目录不可访问，请用户调整 workspace 或权限，不要自行扩大访问范围。

## 常见错误

- 看到“可以并行”就创建 Agent：必须存在跨项目契约、咨询或联调依赖。
- 用户已明确要求创建仍重复确认：明确授权且范围清楚时直接执行。
- 调用 Skill 后立即创建：只调用或只要求方案不等于创建授权。
- 每个项目机械创建一个子代理：root 可以拥有一个项目，应使用最少 Agent。
- 让 Agent 直接协商后只交摘要：跨项目问答经 root 路由，关键结论由 root 复核。
- 把 `send_message` 当作恢复空闲 Agent：需要新回合时使用 `followup_task`。
- 中断 Agent 后假设没有残留：`interrupt_agent` 不回滚工作树，必须检查并披露改动。
- 把独立顶级 Thread 当成 sub-agent：它们不属于同一个协调 session tree。
