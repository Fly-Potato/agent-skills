# Tauri v1 到 v2 迁移指南

从 Tauri v1 升级到 v2 时的破坏性变更清单。

## 目录
- [自动迁移](#自动迁移)
- [Rust API 变更](#rust-api-变更)
- [JavaScript API 变更](#javascript-api-变更)
- [配置变更](#配置变更)
- [事件系统变更](#事件系统变更)
- [权限变更](#权限变更)
- [构建系统变更](#构建系统变更)
- [移动端支持](#移动端支持)

---

## 自动迁移

```bash
# 先更新 CLI
pnpm update @tauri-apps/cli@latest

# 运行自动迁移
pnpm tauri migrate
```

`migrate` 命令会：
- 将 `tauri.conf.json` 从 v1 格式更新为 v2 格式
- 从旧的 allowlist 生成 capability 文件
- 报告仍需手动处理的变更

请仔细检查输出 -- 部分内容需要手动干预。

---

## Rust API 变更

### Window API

| v1 | v2 |
|---|---|
| `tauri::Window` | `tauri::WebviewWindow` |
| `tauri::WindowBuilder` | `tauri::WebviewWindowBuilder` |
| `tauri::WindowUrl` | `tauri::WebviewUrl` |
| `Manager::get_window("label")` | `Manager::get_webview_window("label")` |
| `Window::emit(event, payload)` | 使用 `Emitter` trait：`app.emit(event, payload)` |

### Menu API

| v1 | v2 |
|---|---|
| `tauri::Menu` | `tauri::menu::MenuBuilder` |
| `tauri::Submenu` | `tauri::menu::SubmenuBuilder` |
| `tauri::CustomMenuItem` | `tauri::menu::MenuItemBuilder` |
| `tauri::SystemTrayMenu` | 不再需要 -- 使用 `MenuBuilder` |
| `tauri::MenuItem::About(...)` | `tauri::menu::PredefinedMenuItem::about(...)` |

### Tray API

| v1 | v2 |
|---|---|
| `tauri::SystemTray` | `tauri::tray::TrayIconBuilder` |
| `SystemTray::new()` | `TrayIconBuilder::new().build(app)` |
| `builder.system_tray(tray)` | `builder.plugin(...)` 然后在 setup 中构建 |
| `SystemTrayEvent` | `TrayIconEvent` |

### 插件 API

| v1（内置） | v2（独立插件） |
|---|---|
| `tauri::api::dialog` | 插件：`tauri-plugin-dialog` |
| `tauri::api::http` | 插件：`tauri-plugin-http` |
| `tauri::api::path` | 通过 `Manager` trait 的 `app.path()` |
| `tauri::api::process` | 插件：`tauri-plugin-process` |
| `tauri::api::shell` | 插件：`tauri-plugin-shell` |
| `app.clipboard_manager()` | 插件：`tauri-plugin-clipboard-manager` |
| `app.global_shortcut_manager()` | 插件：`tauri-plugin-global-shortcut` |

### 状态管理

| v1 | v2（相同，但注意） |
|---|---|
| `State<'_, T>` | 相同，但建议使用 `std::sync::Mutex` 而非 Tokio 的 |
| `app.manage(state)` | 相同 |
| `.setup()` | 相同 |

### 入口模式

```rust
// v1
fn main() {
    tauri::Builder::default()
        // ...
        .run(tauri::generate_context!())
        .expect("error");
}

// v2
// main.rs -- 精简入口
fn main() {
    app_lib::run();
}

// lib.rs -- 主要逻辑
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // ...
        .run(tauri::generate_context!())
        .expect("error");
}
```

---

## JavaScript API 变更

### 导入路径

| v1 | v2 |
|---|---|
| `@tauri-apps/api/tauri` | `@tauri-apps/api/core` |
| `@tauri-apps/api/window` | `@tauri-apps/api/window`（仍然存在，但注意 WebviewWindow） |
| `@tauri-apps/api/fs` | `@tauri-apps/plugin-fs`（独立包） |
| `@tauri-apps/api/dialog` | `@tauri-apps/plugin-dialog` |
| `@tauri-apps/api/http` | `@tauri-apps/plugin-http` |
| `@tauri-apps/api/shell` | `@tauri-apps/plugin-shell` |
| `@tauri-apps/api/clipboard` | `@tauri-apps/plugin-clipboard-manager` |
| `@tauri-apps/api/notification` | `@tauri-apps/plugin-notification` |
| `@tauri-apps/api/globalShortcut` | `@tauri-apps/plugin-global-shortcut` |
| `@tauri-apps/api/updater` | `@tauri-apps/plugin-updater` |
| `@tauri-apps/api/os` | `@tauri-apps/plugin-os` |
| `@tauri-apps/api/process` | `@tauri-apps/plugin-process` |
| `@tauri-apps/api/cli` | `@tauri-apps/plugin-cli` |
| `@tauri-apps/api/path` | `@tauri-apps/api/path`（仍是同一个包） |

### Window/Webview

| v1 | v2 |
|---|---|
| `appWindow` 来自 `@tauri-apps/api/window` | 同一个包，但注意 `WebviewWindow` 是 Rust 类型 |
| `new WebviewWindow(...)` | 来自 `@tauri-apps/api/webviewWindow` |

### 事件系统

| v1 | v2 |
|---|---|
| `listen()` | 相同 -- 现在监听**所有**事件 |
| `listenGlobal()` | `listenAny()` |
| `emit("event", payload)` | 相同 -- 现在广播到**所有**监听者 |
| 无 `emitTo` | `emitTo("window-label", "event", payload)` |

---

## 配置变更

### `tauri.conf.json` 结构

| v1 | v2 |
|---|---|
| `"package": { "productName": "..." }` | `"productName": "..."`
| `"tauri": { ... }` | `"app": { ... }` |
| `"tauri": { "allowlist": { ... } }` | **已移除** -- 使用 capabilities |
| `"tauri": { "bundle": { ... } }` | `"bundle": { ... }`（顶层） |
| `"tauri": { "windows": [...] }` | `"app": { "windows": [...] }` |
| `"tauri": { "systemTray": { ... } }` | `"app": { "trayIcon": { ... } }` |
| `"build": { "devPath": "..." }` | `"build": { "devUrl": "..." }` |
| `"build": { "distDir": "..." }` | `"build": { "frontendDist": "..." }` |
| `"build": { "withGlobalTauri": true }` | `"app": { "withGlobalTauri": true }` |
| `"tauri": { "window": { "fileDropEnabled": true } }` | `"app": { "windows": [{ "dragDropEnabled": true }] }` |

### CSP 变更

| v1 | v2 |
|---|---|
| `connect-src https://tauri.localhost` | `connect-src http://tauri.localhost`（或使用 `useHttpsScheme` 时为 `https://`） |

---

## 事件系统变更

### 行为变更

- 在 v1 中，`emit()` 使用基于来源的路由 -- 仅投递到同一窗口中的监听者
- 在 v2 中，`emit()` 会投递到**所有**全局监听者
- 使用 `emit_to()` 进行窗口特定的事件投递

### API 变更

| v1 | v2 |
|---|---|
| `app.emit_all("event", payload)` | `app.emit("event", payload)` |
| `window.emit("event", payload)` | `app.emit_to("label", "event", payload)` |
| `listen_global` | `listen_any` |

### 迁移方式

如果依赖了 `emit()` 的窗口范围行为：
```rust
// v1（窗口范围）
window.emit("my-event", payload);

// v2（显式指定目标）
app.emit_to(window.label(), "my-event", payload);
```

如果依赖了 `emit_all()`：
```rust
// v1
app.emit_all("my-event", payload);

// v2（相同 -- 广播到所有）
app.emit("my-event", payload);
```

---

## 权限变更

### v1 allowlist（已移除）

在 v2 中，`tauri.conf.json` 中的 allowlist 已完全移除。改用 capabilities 系统：

```bash
# 自动迁移
pnpm tauri migrate
```

这会从旧的 allowlist 生成 `capabilities/migrated-*.json` 文件。

### 为插件添加权限

每个插件现在都需要显式的权限。添加插件后：
1. 在 Rust 中注册：`.plugin(tauri_plugin_dialog::init())`
2. 在 capability 文件中添加权限：`"dialog:default"`

### 自定义命令权限

在 v1 中，自定义命令始终被允许。在 v2 中：
1. 在 `build.rs` 中注册命令
2. 定义权限标识符
3. 在 capability 文件中引用

详细说明请参见 `references/security.md`。

---

## 构建系统变更

### `Cargo.toml` 变更

```toml
# v1
[dependencies]
tauri = { version = "1", features = ["shell-open"] }

# v2
[dependencies]
tauri = "2"
tauri-plugin-shell = "2"

[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]  # 用于移动端支持
```

### 环境变量

| v1 | v2 |
|---|---|
| `TAURI_PRIVATE_KEY` | `TAURI_SIGNING_PRIVATE_KEY` |
| `TAURI_KEY_PASSWORD` | `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` |

### Features

| v1 feature | v2 等效 |
|---|---|
| `shell-open` | 改用 `tauri-plugin-shell` |
| `system-tray` | `tauri` crate 的 `tray-icon` feature |
| `custom-protocol` | `tauri` crate 的 `protocol-asset` feature |
| `devtools` | 相同的 feature 名称，仍然可用 |

---

## 移动端支持

要添加移动端支持（v2 新增）：

1. 使用 lib.rs + main.rs 模式重构 Rust 代码（见上文）
2. 添加 staticlib/cdylib 的 crate 类型
3. 在 `pub fn run()` 上添加 `#[cfg_attr(mobile, tauri::mobile_entry_point)]`
4. 使用 `#[cfg(desktop)]` 选择性包含仅桌面端的插件

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init());

    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_global_shortcut::init());
    }

    builder.run(tauri::generate_context!()).expect("error");
}
```

---

## 常见迁移问题

### 找不到 `tauri::Window`
替换为 `tauri::WebviewWindow`。更新所有引用：
- `Window::emit` -> `app.emit_to(label, ...)` 或使用 `Emitter` trait
- `WindowBuilder` -> `WebviewWindowBuilder`
- `WindowUrl` -> `WebviewUrl`

### 找不到 `App::clipboard_manager`
安装并注册 `tauri-plugin-clipboard-manager`：
```rust
// Cargo.toml
tauri-plugin-clipboard-manager = "2"
// lib.rs
.plugin(tauri_plugin_clipboard_manager::init())
// capabilities/default.json
"clipboard-manager:default"
```
```typescript
// package.json
"@tauri-apps/plugin-clipboard-manager": "^2"
// 使用
import { readText } from "@tauri-apps/plugin-clipboard-manager";
```

### `distDir` 不被识别
在 v2 配置中已重命名为 `frontendDist`。

### 事件无法在其他窗口中接收
`emit()` 现在是全局广播。使用 `emit_to()` 进行窗口特定的投递。
