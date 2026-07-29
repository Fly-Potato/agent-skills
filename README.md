# agent-skills

面向 Codex、OpenCode 等 AI 编程助手的技能仓库，为特定技术栈和工作流提供结构化知识。

## 技能列表

| 技能 | 描述 |
|------|------|
| [tauri-v2](skills/tauri-v2/) | Tauri v2 桌面与移动应用开发完整指南 |
| [coordinating-codex-subagents](skills/coordinating-codex-subagents/) | 跨仓库或独立项目的 Codex 子代理协调、契约问答与联调验证 |
| [curating-repository-knowledge](skills/curating-repository-knowledge/) | 仓库内稳定、可复用知识的检索、核实、沉淀与维护 |

## 目录结构

```
skills/
├── <skill-name>/
│   ├── SKILL.md          # 技能主文档
│   ├── README.md         # 可选的补充说明或接入片段
│   ├── agents/           # 可选的 Codex UI 元数据
│   ├── references/       # 可选的参考资料（配置、安全、迁移等）
│   └── evals/            # 可选的评估测试用例
└── ...
```

## 使用方式

本仓库遵循 [skills.sh](https://skills.sh) 规范，配置为 OpenCode 或其他兼容工具的技能源，按需自动加载对应技能的参考知识。

```bash
# 安装全部
npx skills add Fly-Potato/agent-skills

# 安装指定技能
npx skills add Fly-Potato/agent-skills --skill tauri-v2
```

## 贡献

1. 添加新技能：在 `skills/` 下创建 `<skill-name>/SKILL.md`，参考现有技能结构
2. 更新技能：修改对应 `SKILL.md` 或 `references/` 下的文档
3. 如需分组展示，在 `skills.sh.json` 中注册对应技能
