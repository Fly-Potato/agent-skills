# agent-skills

AI 编程助手（如 OpenCode）的技能仓库，为特定技术栈提供结构化知识参考。

## 技能列表

| 技能 | 描述 |
|------|------|
| [tauri-v2](/skills/tauri-v2) | Tauri v2 桌面与移动应用开发完整指南 |

## 目录结构

```
skills/
├── <skill-name>/
│   ├── SKILL.md          # 技能主文档
│   ├── references/        # 参考资料（配置、安全、迁移等）
│   └── evals/             # 评估测试用例
└── ...
```

## 使用方式

本仓库遵循 [skills.sh](https://skills.sh) 规范，配置为 OpenCode 或其他兼容工具的技能源，按需自动加载对应技能的参考知识。

```bash
# 安装全部
skills add Fly-Potato/agent-skills

# 安装指定技能
skills add Fly-Potato/agent-skills --skill tauri-v2
```

## 贡献

1. 添加新技能：在 `skills/` 下创建 `<skill-name>/SKILL.md`，参考现有技能结构
2. 更新技能：修改对应 `SKILL.md` 或 `references/` 下的文档
3. 在 `skills.sh.json` 中注册新技能分组
