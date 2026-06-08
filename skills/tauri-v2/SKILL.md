---
name: tauri-v2
description: Tauri v2 桌面/移动端应用开发指南。涵盖项目结构、Rust 命令 (IPC)、插件系统、安全/权限、窗口管理、事件、状态管理、配置及前端集成。当用户询问 Tauri、提及 tauri、src-tauri、tauri.conf.json、Tauri 上下文中的 Cargo.toml、想用 Web 技术 + Rust 构建桌面应用，或询问任何 Tauri v2 API（命令、插件、事件、窗口、托盘、菜单、更新器）时使用此技能。调试 Tauri 构建错误、配置 capabilitiy/权限或从 Tauri v1 迁移时也适用。即使用户未明确提及 Tauri，但描述用 Rust 后端和 Web 前端构建跨平台桌面应用，此技能同样适用。
---

# Tauri v2 开发指南

## 何时使用此技能

此技能为 Tauri v2 提供权威指导。以下场景使用：
- 创建或脚手架搭建 Tauri v2 项目
- 添加 Rust 命令或前端 invoke 调用
- 配置插件、capability 或权限
- 管理窗口、托盘、菜单或事件
- 调试 Tauri 构建/运行时问题
- 从 Tauri v1 迁移代码

## 如何使用此技能

1. **阅读下方相关章节**获取当前任务所需内容 -- 每个章节提供规范的编码模式
2. **按需查阅 `references/` 文件**获取详尽的 API 细节：

| 文件 | 内容 |
|------|------|
| `references/plugins.md` | 所有官方插件、注册方式、JS API 和权限 |
| `references/security.md` | Capability 系统、权限标识符、scope 配置 |
| `references/configuration.md` | `tauri.conf.json` 完整键值参考 |
| `references/migration-v1.md` | v1 到 v2 破坏性变更清单 |

---

## 项目结构

```
my-tauri-app/
├── src/                    # 前端（React/Vue/Svelte 等）
├── src-tauri/              # Rust 后端
│   ├── Cargo.toml
│   ├── build.rs            # tauri_build::build()
│   ├── tauri.conf.json     # 应用配置
│   ├── capabilities/       # 权限 capability 文件
│   │   └── default.json
│   ├── icons/
│   └── src/
│       ├── main.rs         # 桌面端入口，仅调用 lib
│       └── lib.rs          # 共享逻辑（桌面 + 移动端）
├── package.json
└── vite.config.ts
```

**`main.rs`** 仅调用 lib：
```rust
fn main() { app_lib::run(); }
```

**`lib.rs`** 包含 builder、插件注册和命令处理器：
```rust
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_xxx::init())
        .manage(MyState::default())
        .invoke_handler(tauri::generate_handler![my_command])
        .setup(|app| { Ok(()) })
        .run(tauri::generate_context!())
        .expect("运行 tauri 时出错");
}
```

---

## 命令 (IPC)

命令是类型安全的 JSON-RPC 风格调用。前端用 `invoke` 调用，Rust 端用 `#[tauri::command]` 定义。

```rust
#[tauri::command]
async fn my_command(state: tauri::State<'_, MyState>, arg: String) -> Result<String, Error> {
    Ok(format!("Hello, {}", arg))
}
```

命令参数可注入：`AppHandle`、`WebviewWindow`、`State<T>`、`ipc::Request`、`ipc::Channel<T>`。

**注册：** 命令必须在 builder 中显式注册：
```rust
.invoke_handler(tauri::generate_handler![cmd_name, commands::module::cmd])
```

**前端调用：**
```typescript
import { invoke } from "@tauri-apps/api/core";
const result = await invoke<string>("greet", { name: "World" });
```

**错误处理：** 使用 `thiserror` + `Serialize` 定义结构化错误类型，将 `Error` 作为命令返回值。完整示例见 `references/plugins.md`。

---

## 插件

每个 Tauri v2 插件包含一个 Rust crate (`tauri-plugin-{name}`) 和一个 NPM 包 (`@tauri-apps/plugin-{name}`)。安装步骤：

1. Cargo.toml：`cargo add tauri-plugin-{name}`
2. lib.rs：`.plugin(tauri_plugin_{name}::init())`
3. NPM：`pnpm add @tauri-apps/plugin-{name}`
4. Capability 中添加权限：`"{name}:default"`

完整插件列表、JS API 和权限说明见 `references/plugins.md`。

---

## 安全：Capability 与权限

Tauri v2 用 capability ACL 替代了 v1 的 `allowlist`。Capability 文件位于 `src-tauri/capabilities/`：

```jsonc
{
  "identifier": "default",
  "description": "主窗口的 capability",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "dialog:default",
    "fs:default",
    { "identifier": "http:default", "allow": [{ "url": "https://api.example.com/*" }] }
  ]
}
```

`{plugin}:default` 授予标准安全集合，`{plugin}:allow-{cmd}` 授予特定命令。完整说明见 `references/security.md`。

---

## 窗口管理

Tauri v2 将 `Window` 重命名为 `WebviewWindow`：

| v1 | v2 |
|---|---|
| `tauri::Window` | `tauri::WebviewWindow` |
| `WindowBuilder` | `WebviewWindowBuilder` |
| `@tauri-apps/api/window` | `@tauri-apps/api/webviewWindow` |

**Rust 创建窗口：**
```rust
let window = WebviewWindowBuilder::new(app, "my-window", WebviewUrl::App("index.html".into()))
    .title("我的窗口").inner_size(800.0, 600.0).build()?;
```

**前端窗口 API：**
```typescript
import { getCurrentWindow } from "@tauri-apps/api/window";
const win = getCurrentWindow();
win.minimize(); win.toggleMaximize(); win.close(); win.startDragging();
```

自定义标题栏：窗口配置设置 `"decorations": false`，HTML 中添加 `data-tauri-drag-region` 属性。

---

## 事件系统

事件是 Rust 和前端之间的"即发即弃"消息。

**Rust 发送：**
```rust
app.emit("event-name", &payload)?;           // 广播
app.emit_to("main", "event-name", &payload)?; // 发往特定窗口
```

**前端监听：**
```typescript
import { listen, once, emit } from "@tauri-apps/api/event";
const unlisten = await listen<PayloadType>("event-name", (event) => { /* ... */ });
await once("ready", (event) => { /* ... */ });
emit("frontend-event", { data: "value" });
```

**Rust 监听：**
```rust
app.listen("event-name", |event| {
    let payload = serde_json::from_str::<T>(event.payload())?;
});
```

---

## 状态管理

使用 `Mutex` 包裹 Rust 结构体，通过 `app.manage()` 注入：

```rust
use std::sync::Mutex;
struct AppState { counter: u32 }
app.manage(Mutex::new(AppState { counter: 0 }));
```

在命令中通过 `State<T>` 参数注入访问：
```rust
#[tauri::command]
fn get_count(state: tauri::State<'_, Mutex<AppState>>) -> u32 {
    state.lock().unwrap().counter
}
```

使用 `std::sync::Mutex`（同步和异步上下文均适用），不要用 `Arc` 包装状态，Tauri 会自动处理。

---

## 配置（`tauri.conf.json`）

主要变更：原 `tauri` 嵌套字段移至顶层 `app`，`distDir` 改为 `build.frontendDist`。

完整键值参考见 `references/configuration.md`。

---

## 托盘与菜单

```rust
use tauri::tray::{TrayIconBuilder, MouseButton, MouseButtonState, TrayIconEvent};
use tauri::menu::{MenuBuilder, MenuItemBuilder};

let menu = MenuBuilder::new(app)
    .item(&MenuItemBuilder::with_id("show", "显示").build(app)?)
    .separator()
    .item(&MenuItemBuilder::with_id("quit", "退出").build(app)?)
    .build()?;

TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .menu(&menu)
    .on_menu_event(|app, event| {
        match event.id().as_ref() {
            "show" => { /* 显示窗口 */ }
            "quit" => app.exit(0),
            _ => {}
        }
    })
    .build(app)?;
```

所需 capability：`["core:tray:default", "core:menu:default"]`

---

## 平台特定代码

使用条件编译实现平台差异逻辑：

```rust
#[cfg(target_os = "windows")]
fn do_windows_thing() { /* 原生 Windows 实现 */ }

#[cfg(not(target_os = "windows"))]
fn do_windows_thing() { /* 桩函数 */ }
```

---

## 快速参考：常见任务

### 添加新命令
1. 编写 `#[tauri::command] async fn`
2. 在 `generate_handler![...]` 中注册
3. 前端调用：`await invoke("command_name", { args })`

### 添加新插件
1. `cargo add tauri-plugin-{name}`
2. `.plugin(tauri_plugin_{name}::init())`
3. `pnpm add @tauri-apps/plugin-{name}`
4. 在 capability 中添加 `"{name}:default"`

### 添加新窗口
1. 在 `tauri.conf.json` 的 `app.windows[]` 中定义
2. 或动态创建：`WebviewWindowBuilder::new(app, label, url).build()?`
3. 确保窗口 label 在 capability 文件中

### 调试 IPC 问题
- 检查命令是否在 `generate_handler![]` 中注册
- 检查权限是否在 `capabilities/default.json` 中
- 验证命令没有被 `deny` 权限排除
- 使用 `tauri-plugin-log` 记录 Rust 端结构化日志
