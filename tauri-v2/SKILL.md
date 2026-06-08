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
   - `references/plugins.md` -- 所有官方插件、注册方式、JS API 和权限
   - `references/security.md` -- Capability 系统、权限标识符、scope 配置
   - `references/configuration.md` -- `tauri.conf.json` 完整键值参考
   - `references/migration-v1.md` -- v1 到 v2 破坏性变更清单

---

## 项目结构

典型的 Tauri v2 项目：

```
my-tauri-app/
├── src/                    # 前端（React/Vue/Svelte 等）
├── src-tauri/              # Rust 后端
│   ├── Cargo.toml          # Rust 依赖（tauri + 插件 + 库）
│   ├── build.rs            # tauri_build::build()
│   ├── tauri.conf.json     # 应用配置（窗口、打包、插件、CSP）
│   ├── capabilities/       # 权限 capability 文件
│   │   └── default.json
│   ├── icons/              # 应用图标（png、ico、icns）
│   └── src/
│       ├── main.rs         # 桌面端入口
│       └── lib.rs          # 共享逻辑（桌面 + 移动端）
├── package.json
└── vite.config.ts
```

### 入口文件

**`main.rs`** -- 极简，仅调用 lib：

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
fn main() {
    app_lib::run();
}
```

**`lib.rs`** -- 包含 builder、插件注册和命令处理器：

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_xxx::init())
        .manage(MyState::default())
        .invoke_handler(tauri::generate_handler![my_command])
        .setup(|app| { /* 构建后初始化 */ Ok(()) })
        .run(tauri::generate_context!())
        .expect("运行 tauri 时出错");
}
```

### 移动端支持的 crate 类型

```toml
[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]
```

---

## 命令 (IPC)

命令是前端调用 Rust 的主要方式。它们是类型安全的、类似 JSON-RPC 的消息。

### 定义命令（Rust）

```rust
// 异步 -- 任何 I/O 或重度计算的首选方式
#[tauri::command]
async fn my_command(state: tauri::State<'_, MyState>, arg: String) -> Result<String, Error> {
    Ok(format!("Hello, {}", arg))
}
```

可以通过添加以下参数来注入系统句柄：
- `tauri::AppHandle` -- 访问应用级 API
- `tauri::WebviewWindow` -- 调用方窗口
- `tauri::State<'_, T>` -- 已管理的状态
- `tauri::ipc::Request` -- 原始 IPC 请求（用于文件上传）
- `tauri::ipc::Channel<T>` -- 向前端流式传输数据

### 注册命令

命令必须在 builder 中显式注册。这是推荐做法——避免了仅靠宏自动发现可能带来的问题：

```rust
.invoke_handler(tauri::generate_handler![
    commands::module::cmd_name,
    another_command,
])
```

### 从前端调用（TypeScript）

```typescript
import { invoke } from "@tauri-apps/api/core";

// 简单调用
const result = await invoke<string>("greet", { name: "World" });

// 使用 Channel 实现流式传输
import { Channel } from "@tauri-apps/api/core";
const onProgress = new Channel<number>();
onProgress.onmessage = (bytes) => console.log(`收到 ${bytes} 字节`);
await invoke("download", { url, onProgress });

// 原始二进制数据
const data = new Uint8Array([1, 2, 3]);
await invoke("upload", data, { headers: { Authorization: "token" } });
```

### 错误处理

使用 `thiserror` + `Serialize` 定义自定义错误类型，向前端提供结构化错误：

```rust
#[derive(Debug, thiserror::Error)]
enum Error {
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error("未找到: {0}")]
    NotFound(String),
}

impl serde::Serialize for Error {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::ser::Serializer {
        serializer.serialize_str(self.to_string().as_ref())
    }
}
```

---

## 插件

Tauri v2 插件将功能从核心中解耦。每个插件包含：
- 一个 **Rust crate**（Cargo.toml 中的 `tauri-plugin-{name}`）
- 一个 **NPM 包**（package.json 中的 `@tauri-apps/plugin-{name}`）
- **权限**自动暴露为 `{plugin}:default` / `{plugin}:allow-*`

### 使用插件

1. 添加到 Cargo.toml：`tauri-plugin-dialog = "2"`
2. 在 lib.rs 中注册：`.plugin(tauri_plugin_dialog::init())`
3. 添加 NPM 包：`pnpm add @tauri-apps/plugin-dialog`
4. 在 capability 中添加权限：`"dialog:default"`

### 常用插件

| 插件 | Cargo crate | JS 包 | 用途 |
|--------|------------|------------|---------|
| dialog | `tauri-plugin-dialog` | `@tauri-apps/plugin-dialog` | 文件打开/保存对话框 |
| fs | `tauri-plugin-fs` | `@tauri-apps/plugin-fs` | 文件系统操作 |
| shell | `tauri-plugin-shell` | `@tauri-apps/plugin-shell` | 执行命令、打开 URL/路径 |
| http | `tauri-plugin-http` | `@tauri-apps/plugin-http` | HTTP 客户端（reqwest） |
| notification | `tauri-plugin-notification` | `@tauri-apps/plugin-notification` | 系统通知 |
| updater | `tauri-plugin-updater` | `@tauri-apps/plugin-updater` | 应用内自动更新 |
| store | `tauri-plugin-store` | `@tauri-apps/plugin-store` | 持久化键值存储 |
| sql | `tauri-plugin-sql` | `@tauri-apps/plugin-sql` | SQL 数据库 |
| clipboard | `tauri-plugin-clipboard-manager` | `@tauri-apps/plugin-clipboard-manager` | 剪贴板读写 |
| global-shortcut | `tauri-plugin-global-shortcut` | `@tauri-apps/plugin-global-shortcut` | 全局键盘快捷键 |
| process | `tauri-plugin-process` | `@tauri-apps/plugin-process` | 退出/重启应用 |
| window-state | `tauri-plugin-window-state` | `@tauri-apps/plugin-window-state` | 保存/恢复窗口位置和大小 |
| autostart | `tauri-plugin-autostart` | `@tauri-apps/plugin-autostart` | 系统启动时启动应用 |
| single-instance | `tauri-plugin-single-instance` | （仅 Rust） | 强制单实例 |
| websocket | `tauri-plugin-websocket` | `@tauri-apps/plugin-websocket` | WebSocket 客户端 |
| deep-link | `tauri-plugin-deep-link` | `@tauri-apps/plugin-deep-link` | 自定义 URL scheme 处理 |
| upload | `tauri-plugin-upload` | `@tauri-apps/plugin-upload` | 文件上传工具 |
| log | `tauri-plugin-log` | `@tauri-apps/plugin-log` | 带轮转的日志记录 |
| opener | `tauri-plugin-opener` | `@tauri-apps/plugin-opener` | 用系统默认应用打开 URL/文件/路径 |

详细的插件配置、权限和 JS API 示例，请阅读 `references/plugins.md`。

---

## 安全：Capability 与权限

Tauri v2 用 capability ACL 系统替换了 v1 的 `allowlist`。

### 工作原理

```
Capability 文件 --> 列出权限标识符 --> 控制命令访问 --> 带可选的 scope
```

### Capability 文件（`src-tauri/capabilities/default.json`）

```jsonc
{
  "identifier": "default",
  "description": "主窗口的 capability",
  "windows": ["main"],
  "platforms": ["windows", "linux", "macOS"],
  "permissions": [
    "core:path:default",
    "core:event:default",
    "core:window:default",
    "core:app:default",
    "core:webview:default",
    "dialog:default",
    "fs:default",
    "shell:allow-open",
    // scope 权限示例
    {
      "identifier": "http:default",
      "allow": [{ "url": "https://api.example.com/*" }]
    }
  ]
}
```

### 核心原则

- `:default` 后缀的权限授予标准安全集合
- `:allow-{command}` 授予特定命令（如 `fs:allow-read-file`）
- scope 权限使用数组形式，内含 `allow` 对象
- 远程窗口需要单独带有 `remote` 字段的 capability
- 自定义命令需要在 `build.rs` 中通过 `.commands()` 注册

完整的权限、scope 格式和远程 API 模式说明，请阅读 `references/security.md`。

---

## 窗口管理

### v2 关键变更：`Window` 变为 `WebviewWindow`

| v1 | v2 |
|---|---|
| `tauri::Window` | `tauri::WebviewWindow` |
| `WindowBuilder` | `WebviewWindowBuilder` |
| `Manager::get_window` | `Manager::get_webview_window` |
| `@tauri-apps/api/window` | `@tauri-apps/api/webviewWindow` |

### 从 Rust 创建窗口

```rust
use tauri::{WebviewUrl, WebviewWindowBuilder};

let window = WebviewWindowBuilder::new(app, "my-window", WebviewUrl::App("index.html".into()))
    .title("我的窗口")
    .inner_size(800.0, 600.0)
    .resizable(true)
    .decorations(true)
    .build()?;
```

### 从配置创建窗口（`tauri.conf.json`）

```json
{
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "My App",
        "width": 800,
        "height": 600,
        "center": true
      }
    ]
  }
}
```

### 前端窗口 API

```typescript
import { getCurrentWindow } from "@tauri-apps/api/window";
const win = getCurrentWindow();

win.minimize();
win.toggleMaximize();
win.close();
win.setTitle("新标题");
win.startDragging(); // 自定义标题栏的程序化拖拽

// 从前端创建新窗口
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";
const w = new WebviewWindow("settings", { url: "/settings" });
```

### 自定义标题栏模式

1. 在窗口配置中设置 `"decorations": false`
2. 添加带有 `data-tauri-drag-region` 属性的固定标题栏 div
3. 将最小化/最大化/关闭按钮连接到窗口 API 方法

---

## 事件系统

事件是 Rust 和前端之间的"即发即弃"消息。

### 从 Rust 发送

```rust
use tauri::{AppHandle, Emitter, EventTarget};

// 广播给所有监听器
app.emit("event-name", &payload)?;

// 发送给特定窗口
app.emit_to("main", "event-name", &payload)?;

// 过滤发送
app.emit_filter("event-name", &payload, |target| match target {
    EventTarget::WebviewWindow { label } => label == "main",
    _ => false,
})?;
```

### 前端监听（TypeScript）

```typescript
import { listen, once, emit } from "@tauri-apps/api/event";

// 监听（返回取消监听函数）
const unlisten = await listen<PayloadType>("event-name", (event) => {
    console.log(event.payload);
});
unlisten(); // 完成后清理

// 一次性监听
await once("ready", (event) => { /* ... */ });

// 从前端发送
emit("frontend-event", { data: "value" });
```

### Rust 端监听

```rust
use tauri::Listener;

app.listen("event-name", |event| {
    let payload = serde_json::from_str::<T>(event.payload())?;
});
```

---

## 状态管理

### 管理状态

```rust
use std::sync::Mutex;

#[derive(Default)]
struct AppState {
    counter: u32,
    user: Option<UserInfo>,
}

// 在 builder 中：
.manage(Mutex::new(AppState::default()))
// 或在 setup() 中：
.setup(|app| {
    app.manage(Mutex::new(AppState::default()));
    Ok(())
})
```

### 访问状态

```rust
// 在命令中 -- Tauri 通过参数注入
#[tauri::command]
fn get_count(state: tauri::State<'_, Mutex<AppState>>) -> u32 {
    state.lock().unwrap().counter
}

// 在命令外部（如事件处理器） -- 通过 AppHandle 访问
app.state::<Mutex<AppState>>().lock().unwrap().counter += 1;
```

### 关键规则

- 优先使用 `std::sync::Mutex` -- 它在同步和异步上下文中都能工作
- 不要用 `Arc` 包装状态 -- Tauri 会自动处理
- 使用类型别名避免类型不匹配的 panic：`type AppState = Mutex<AppStateInner>;`

---

## 配置（`tauri.conf.json`）

### 顶层结构

```jsonc
{
  "productName": "MyApp",        // 原 "package > productName"
  "version": "1.0.0",
  "identifier": "com.example.app",
  "build": {
    "beforeDevCommand": "pnpm dev",
    "devUrl": "http://localhost:1420",
    "beforeBuildCommand": "pnpm build",
    "frontendDist": "../dist"    // 原 "distDir"
  },
  "app": {                        // 原 "tauri"
    "withGlobalTauri": true,
    "windows": [ /* ... */ ],
    "security": {
      "csp": "default-src 'self'; connect-src ipc: http://ipc.localhost",
      "assetProtocol": { "enable": true, "scope": ["**"] }
    }
  },
  "bundle": {                     // 原 "tauri > bundle"
    "active": true,
    "icon": ["icons/icon.png"],
    "targets": ["nsis", "dmg", "appimage"],
    "createUpdaterArtifacts": true
  },
  "plugins": {
    "updater": { /* ... */ },
    "sql": { "preload": { "db": "sqlite:data.db" } }
  }
}
```

完整参考：`references/configuration.md`

---

## 托盘与菜单

### 构建系统托盘

```rust
use tauri::tray::{TrayIconBuilder, MouseButton, MouseButtonState, TrayIconEvent};
use tauri::menu::{MenuBuilder, MenuItemBuilder};

let menu = MenuBuilder::new(app)
    .item(&MenuItemBuilder::with_id("show", "显示").build(app)?)
    .separator()
    .item(&MenuItemBuilder::with_id("quit", "退出").build(app)?)
    .build()?;

let tray = TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .menu(&menu)
    .tooltip("我的应用")
    .on_menu_event(|app, event| {
        match event.id().as_ref() {
            "show" => { /* 显示窗口 */ }
            "quit" => app.exit(0),
            _ => {}
        }
    })
    .on_tray_icon_event(|tray, event| {
        if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
            // 左键点击显示窗口
        }
    })
    .build(app)?;
```

### 所需 capability

托盘需要以下权限：
```json
["core:tray:default", "core:menu:default"]
```

---

## 前端依赖模式

### Tauri JS 包与 Rust 插件对应关系

| Rust 依赖 | NPM 包 | 导入来源 |
|----------------|-------------|------------|
| `tauri` | `@tauri-apps/api`（core） | `@tauri-apps/api/core`、`@tauri-apps/api/event`、`@tauri-apps/api/window` |
| `tauri-plugin-dialog` | `@tauri-apps/plugin-dialog` | `@tauri-apps/plugin-dialog` |
| `tauri-plugin-fs` | `@tauri-apps/plugin-fs` | `@tauri-apps/plugin-fs` |
| `tauri-plugin-http` | `@tauri-apps/plugin-http` | `@tauri-apps/plugin-http` |
| `tauri-plugin-store` | `@tauri-apps/plugin-store` | `@tauri-apps/plugin-store` |
| `tauri-plugin-sql` | `@tauri-apps/plugin-sql` | `@tauri-apps/plugin-sql` |
| `tauri-plugin-notification` | `@tauri-apps/plugin-notification` | `@tauri-apps/plugin-notification` |

每个 NPM 包都提供与 Rust 插件暴露操作相对应的类型化 API。始终同时安装 Cargo 依赖和匹配的 NPM 包。

---

## 平台特定代码

使用条件编译实现操作系统特定逻辑：

```rust
// 在 Cargo.toml 中
[target.'cfg(windows)'.dependencies]
windows = "0.58"

[target.'cfg(not(any(target_os = "android", target_os = "ios")))'.dependencies]
tauri-plugin-global-shortcut = "2"

// 在 Rust 代码中
#[cfg(target_os = "windows")]
fn do_windows_thing() { /* ... */ }

#[cfg(not(target_os = "windows"))]
fn do_windows_thing() { /* 桩函数或 panic */ }

// 桌面端专用代码的功能标记
#[cfg(desktop)]
.modify_menu(|app, menu| { /* ... */ })
```

### 常见模式：非 Windows 平台的桩文件

当某个功能仅限 Windows 时，提供具有匹配函数签名的桩文件：
```
src/
├── notifications.rs        # Windows 实现
└── notifications_stub.rs   # 非 Windows 桩
```

---

## 快速参考：常见任务

### 添加新命令
1. 在 `src-tauri/src/` 中编写 `#[tauri::command] async fn`
2. 在 lib.rs 的 `generate_handler![...]` 中注册
3. 从前端调用：`await invoke("command_name", { args })`

### 添加新插件
1. `cargo add tauri-plugin-{name}`（在 src-tauri 中）
2. 在 lib.rs 中 `.plugin(tauri_plugin_{name}::init())`
3. `pnpm add @tauri-apps/plugin-{name}`（在根目录）
4. 在 capabilities/default.json 权限中添加 `"{name}:default"`

### 添加新窗口
1. 在 `tauri.conf.json` 的 `app.windows[]` 中定义
2. 或动态创建：`WebviewWindowBuilder::new(app, label, url).build()?`
3. 确保窗口 label 在 capability 文件中

### 调试 IPC 问题
- 检查命令是否在 `generate_handler![]` 中注册
- 检查权限是否在 `capabilities/default.json` 中
- 验证命令没有被 `deny` 权限排除
- 使用 `tauri-plugin-log` 记录 Rust 端结构化日志
