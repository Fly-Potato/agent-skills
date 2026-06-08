# Tauri v2 插件参考

所有 Tauri v2 官方插件的完整参考：Rust 注册、JS API、配置及权限。

## 目录
- [dialog](#dialog)
- [fs](#fs)
- [shell](#shell)
- [http](#http)
- [notification](#notification)
- [updater](#updater)
- [store](#store)
- [sql](#sql)
- [clipboard-manager](#clipboard-manager)
- [global-shortcut](#global-shortcut)
- [process](#process)
- [window-state](#window-state)
- [autostart](#autostart)
- [single-instance](#single-instance)
- [websocket](#websocket)
- [deep-link](#deep-link)
- [upload](#upload)
- [log](#log)
- [opener](#opener)

---

## dialog

文件打开/保存对话框。

**Rust crate：** `tauri-plugin-dialog = "2"`
**JS 包：** `@tauri-apps/plugin-dialog`
**权限：** `"dialog:default"`、`"dialog:allow-open"`、`"dialog:allow-save"`、`"dialog:allow-message"`、`"dialog:allow-ask"`、`"dialog:allow-confirm"`

### JS API

```typescript
import { open, save, message, ask, confirm } from "@tauri-apps/plugin-dialog";

// 打开文件对话框
const file = await open({
  multiple: false,
  filters: [{ name: "Images", extensions: ["png", "jpg"] }],
});
console.log(file); // null 或文件路径字符串

// 保存对话框
const path = await save({
  defaultPath: "document.txt",
  filters: [{ name: "Text", extensions: ["txt"] }],
});

// 消息提示
await message("Operation complete", { title: "Success", kind: "info" });
// kind: "info" | "warning" | "error"

// 确认对话框
const yes = await confirm("Are you sure?", { title: "Confirm", kind: "warning" });
```

---

## fs

文件系统访问。

**Rust crate：** `tauri-plugin-fs = "2"`
**JS 包：** `@tauri-apps/plugin-fs`
**权限：** `"fs:default"`、`"fs:allow-read-file"`、`"fs:allow-write-file"`、`"fs:allow-read-text-file"`、`"fs:allow-write-text-file"`、`"fs:allow-exists"`、`"fs:allow-mkdir"`、`"fs:allow-remove"`、`"fs:allow-rename"`、`"fs:allow-copy-file"`、`"fs:scope"`

### 作用域配置

```json
{
  "identifier": "fs:scope",
  "allow": [{ "path": "$APPDATA/*" }, { "path": "$HOME/**" }]
}
```

作用域变量：`$APPDATA`、`$APPDATA$`、`$HOME`、`$TEMP`、`$RESOURCE`、`$CACHE`、`$CONFIG`、`$LOCALDATA`、`$DESKTOP`、`$DOCUMENT`、`$DOWNLOAD`、`$PICTURE`、`$VIDEO`、`$AUDIO`、`$PUBLIC`

### JS API

```typescript
import { readTextFile, writeTextFile, readFile, writeFile, exists, mkdir, remove, rename, BaseDirectory } from "@tauri-apps/plugin-fs";

const text = await readTextFile("config.json", { baseDir: BaseDirectory.AppData });
await writeTextFile("config.json", JSON.stringify(data), { baseDir: BaseDirectory.AppData });
const binary = await readFile("image.png");
await writeFile("output.png", new Uint8Array([...]));
const fileExists = await exists("data.db");
await mkdir("new-folder");
```

---

## shell

执行命令及打开 URL/文件。

**Rust crate：** `tauri-plugin-shell = "2"`
**JS 包：** `@tauri-apps/plugin-shell`
**权限：** `"shell:default"`、`"shell:allow-open"`、`"shell:allow-spawn"`、`"shell:allow-execute"`、`"shell:allow-stdin-write"`、`"shell:allow-kill"`

### 作用域配置

```json
// 允许通过 URL 作用域打开链接
{ "identifier": "shell:allow-open", "allow": [{ "url": "https://*" }] }

// 允许执行 sidecar
{
  "identifier": "shell:allow-execute",
  "allow": [{ "name": "my-sidecar", "cmd": "./sidecars/my-sidecar", "sidecar": true }]
}

// 允许带参数 spawn
{
  "identifier": "shell:allow-spawn",
  "allow": [{ "name": "node", "cmd": "node", "args": true }]
}
```

### JS API

```typescript
import { open } from "@tauri-apps/plugin-shell";
await open("https://example.com");
await open("/path/to/file.pdf");

import { Command } from "@tauri-apps/plugin-shell";
const cmd = Command.create("echo", ["hello"]);
const output = await cmd.execute(); // { code: 0, stdout: "hello\n", stderr: "", signal: null }

// 长时间运行的命令
const cmd = Command.create("sidecar-name");
cmd.on("close", (data) => console.log("exit code:", data.code));
cmd.on("error", (error) => console.error(error));
cmd.stdout.on("data", (line) => console.log("stdout:", line));
cmd.stderr.on("data", (line) => console.error("stderr:", line));
const child = await cmd.spawn();
child.write("stdin data");
child.kill();
```

---

## http

基于 reqwest 的 HTTP 客户端。

**Rust crate：** `tauri-plugin-http = "2"`（功能特性：`multipart`、`json`、`blocking`、`stream`、`rustls-tls`）
**JS 包：** `@tauri-apps/plugin-http`
**权限：** `"http:default"`、`"http:allow-fetch"`、`"http:allow-fetch-cancel"`、`"http:allow-fetch-read-body"`、`"http:allow-fetch-send"`

### 作用域配置

```json
{
  "identifier": "http:default",
  "allow": [
    { "url": "https://api.example.com/*" },
    { "url": "http://127.0.0.1:*/*" }
  ]
}
```

### JS API

```typescript
import { fetch } from "@tauri-apps/plugin-http";

const response = await fetch("https://api.example.com/data", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ key: "value" }),
});
const json: ResponseType = await response.json();

// 通过 multipart 上传文件
const form = new FormData();
form.append("file", fileData);
const response = await fetch("https://api.example.com/upload", {
  method: "POST",
  body: form,
});
```

### Rust（reqwest 重导出）

```rust
use tauri_plugin_http::reqwest;
let client = reqwest::Client::new();
// 使用与插件相同的 reqwest crate
```

---

## notification

系统通知支持。

**Rust crate：** `tauri-plugin-notification = "2"`
**JS 包：** `@tauri-apps/plugin-notification`
**权限：** `"notification:default"`、`"notification:allow-notify"`、`"notification:allow-is-permission-granted"`、`"notification:allow-request-permission"`、`"notification:allow-register-action-types"`

### JS API

```typescript
import { sendNotification, isPermissionGranted, requestPermission } from "@tauri-apps/plugin-notification";

let permissionGranted = await isPermissionGranted();
if (!permissionGranted) {
  const permission = await requestPermission();
  permissionGranted = permission === "granted";
}
if (permissionGranted) {
  sendNotification({ title: "Tauri", body: "Hello from Tauri!" });
}
```

---

## updater

应用内更新机制。

**Rust crate：** `tauri-plugin-updater = "2"`
**JS 包：** `@tauri-apps/plugin-updater`
**权限：** `"updater:default"`、`"updater:allow-check"`、`"updater:allow-download-and-install"`、`"updater:allow-download"`、`"updater:allow-install"`

### tauri.conf.json 中的插件配置

```json
{
  "plugins": {
    "updater": {
      "pubkey": "<pubkey>",
      "endpoints": ["https://releases.example.com/{{target}}/{{arch}}/{{current_version}}"],
      "windows": { "installMode": "passive" }
    }
  }
}
```

### JS API

```typescript
import { check } from "@tauri-apps/plugin-updater";

const update = await check();
if (update) {
  console.log(`Update available: ${update.version}`);
  await update.downloadAndInstall((event) => {
    switch (event.event) {
      case "Started": break;
      case "Progress": console.log(`Downloading: ${event.data.chunkLength}`); break;
      case "Finished": break;
    }
  });
  // 安装后应用将重新启动
}
```

### 更新器环境变量

- `TAURI_SIGNING_PRIVATE_KEY` -- 用于签名的私钥（在构建环境中设置）
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` -- 可选密码

---

## store

基于文件的持久化键值存储。

**Rust crate：** `tauri-plugin-store = "2"`
**JS 包：** `@tauri-apps/plugin-store`
**权限：** `"store:default"`、`"store:allow-set"`、`"store:allow-get"`、`"store:allow-delete"`、`"store:allow-save"`、`"store:allow-load"`、`"store:allow-keys"`、`"store:allow-values"`、`"store:allow-entries"`、`"store:allow-length"`、`"store:allow-has"`、`"store:allow-clear"`、`"store:allow-reset"`

### JS API

```typescript
import { Store } from "@tauri-apps/plugin-store";

// 存储文件位置：app_data_dir/<filename>
const store = await Store.load("settings.json");
await store.set("theme", { mode: "dark" });
const theme = await store.get<{ mode: string }>("theme");
await store.delete("key");
await store.save(); // 持久化到磁盘（也支持自动保存）
const hasKey = await store.has("key");
```

---

## sql

通过 SQLite/MySQL/PostgreSQL 访问 SQL 数据库。

**Rust crate：** `tauri-plugin-sql = "2"`（功能特性：`sqlite`、`mysql`、`postgres`）
**JS 包：** `@tauri-apps/plugin-sql`
**权限：** `"sql:default"`、`"sql:allow-load"`、`"sql:allow-execute"`、`"sql:allow-select"`、`"sql:allow-close"`

### 带迁移的插件配置

```json
{
  "plugins": {
    "sql": {
      "preload": {
        "db": "sqlite:data.db"
      }
    }
  }
}
```

### JS API

```typescript
import Database from "@tauri-apps/plugin-sql";

const db = await Database.load("sqlite:data.db");
const rows = await db.select<Array<{ id: number; name: string }>>("SELECT * FROM users WHERE id = $1", [1]);
await db.execute("INSERT INTO users (name) VALUES ($1)", ["Alice"]);
```

### SQLite 迁移（Rust）

```rust
use tauri_plugin_sql::{Migration, MigrationKind};

tauri_plugin_sql::Builder::default()
    .add_migrations("sqlite:data.db", vec![
        Migration {
            version: 1,
            description: "create initial tables",
            sql: "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
            kind: MigrationKind::Up,
        },
    ])
    .build()
```

---

## clipboard-manager

读写剪贴板内容。

**Rust crate：** `tauri-plugin-clipboard-manager = "2"`
**JS 包：** `@tauri-apps/plugin-clipboard-manager`
**权限：** `"clipboard-manager:default"`、`"clipboard-manager:allow-read-text"`、`"clipboard-manager:allow-write-text"`、`"clipboard-manager:allow-read-image"`、`"clipboard-manager:allow-write-image"`、`"clipboard-manager:allow-write-html"`、`"clipboard-manager:allow-clear"`

### JS API

```typescript
import { readText, writeText, readImage, writeImage } from "@tauri-apps/plugin-clipboard-manager";

await writeText("copied text");
const text = await readText();

const image = await readImage(); // 返回 Uint8Array（PNG 字节）
await writeImage(new Uint8Array([...]));
```

---

## global-shortcut

全局键盘快捷键（仅桌面端）。

**Rust crate：** `tauri-plugin-global-shortcut = "2"`（仅桌面端：`#[cfg(not(android/ios))]`）
**JS 包：** `@tauri-apps/plugin-global-shortcut`
**权限：** `"global-shortcut:default"`、`"global-shortcut:allow-register"`、`"global-shortcut:allow-unregister"`、`"global-shortcut:allow-unregister-all"`、`"global-shortcut:allow-is-registered"`

### JS API

```typescript
import { register, unregister, isRegistered } from "@tauri-apps/plugin-global-shortcut";

await register("CommandOrControl+Shift+K", (event) => {
  if (event.state === "Pressed") {
    console.log("Shortcut triggered!");
  }
});
if (await isRegistered("CommandOrControl+Shift+K")) {
  await unregister("CommandOrControl+Shift+K");
}
```

---

## process

应用退出/重启控制。

**Rust crate：** `tauri-plugin-process = "2"`
**JS 包：** `@tauri-apps/plugin-process`
**权限：** `"process:default"`、`"process:allow-exit"`、`"process:allow-restart"`

### JS API

```typescript
import { exit, relaunch } from "@tauri-apps/plugin-process";

await relaunch();
await exit(0); // 退出码 0 表示成功
```

---

## window-state

保存和恢复窗口位置、大小及状态。

**Rust crate：** `tauri-plugin-window-state = "2"`
**JS 包：** `@tauri-apps/plugin-window-state`
**权限：**（使用核心权限，无需显式插件权限）

### Rust 注册

```rust
.plugin(
    tauri_plugin_window_state::Builder::default()
        .with_denylist(&["transient-window", "settings"])
        .build()
)
```

无需 JS API —— 它会自动保存和恢复窗口状态。

---

## autostart

系统启动时自动启动应用（仅桌面端）。

**Rust crate：** `tauri-plugin-autostart = "2"`（仅桌面端）
**JS 包：** `@tauri-apps/plugin-autostart`
**权限：** `"autostart:default"`、`"autostart:allow-enable"`、`"autostart:allow-disable"`、`"autostart:allow-is-enabled"`

### JS API

```typescript
import { enable, disable, isEnabled } from "@tauri-apps/plugin-autostart";

await enable();
if (await isEnabled()) {
  await disable();
}
```

---

## single-instance

强制应用单实例运行（仅 Rust，无 JS 包）。

**Rust crate：** `tauri-plugin-single-instance = "2"`
**权限：**（使用核心权限）

### Rust 注册

```rust
.plugin(tauri_plugin_single_instance::init(|app, argv, cwd| {
    // 第二个实例启动时 —— 显示已有窗口
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}))
```

---

## websocket

WebSocket 客户端。

**Rust crate：** `tauri-plugin-websocket = "2"`
**JS 包：** `@tauri-apps/plugin-websocket`
**权限：** `"websocket:default"`、`"websocket:allow-connect"`、`"websocket:allow-send"`

### JS API

```typescript
import WebSocket from "@tauri-apps/plugin-websocket";

const ws = await WebSocket.connect("wss://example.com/ws");
ws.addListener((message) => {
  if (message.type === "Text") console.log(message.data);
  else if (message.type === "Binary") { /* Uint8Array */ }
  else if (message.type === "Close") { /* 连接已关闭 */ }
});
await ws.send("Hello");
await ws.send(new Uint8Array([1, 2, 3]));
await ws.disconnect();
```

---

## deep-link

处理自定义 URL scheme / 深度链接（如 ett://、myapp://）注册。

**Rust crate：** `tauri-plugin-deep-link = "2"`
**JS 包：** `@tauri-apps/plugin-deep-link`
**权限：** `"deep-link:default"`、`"deep-link:allow-register"`、`"deep-link:allow-unregister"`、`"deep-link:allow-is-registered"`

### tauri.conf.json 中的插件配置

```json
{
  "plugins": {
    "deep-link": {
      "desktop": { "schemes": ["myapp", "my-app"] },
      "mobile": [{ "host": "example.com", "pathPrefix": ["/open"] }]
    }
  }
}
```

### JS API

```typescript
import { onOpenUrl } from "@tauri-apps/plugin-deep-link";

await onOpenUrl((urls) => {
  for (const url of urls) {
    console.log("Deep link:", url);
  }
});
```

---

## upload

用于 Tauri IPC 的文件上传辅助工具。

**Rust crate：** `tauri-plugin-upload = "2"`
**JS 包：** `@tauri-apps/plugin-upload`
**权限：** `"upload:default"`、`"upload:allow-upload"`

### JS API

```typescript
import { upload } from "@tauri-apps/plugin-upload";

await upload(
  "https://api.example.com/upload",
  "/path/to/file.png",
  (progress, total) => console.log(`Uploaded ${progress}/${total} bytes`),
  { "Authorization": "Bearer token" }
);
```

---

## log

结构化日志，支持文件轮转及 webview 控制台输出。

**Rust crate：** `tauri-plugin-log = "2"`
**JS 包：** `@tauri-apps/plugin-log`
**权限：** `"log:default"`

### Rust 注册

```rust
tauri_plugin_log::Builder::new()
    .level(log::LevelFilter::Info)
    .targets([
        LogTarget::Stdout,
        LogTarget::Webview,
        LogTarget::LogDir,
    ])
    .rotation_strategy(RotationStrategy::KeepAll)
    .max_file_size(50_000) // 50KB
    .timezone_strategy(TimezoneStrategy::UseLocal)
    .build()
```

### JS API

```typescript
import { trace, info, warn, error } from "@tauri-apps/plugin-log";

info("User logged in");
warn("Rate limit approaching");
error("Connection failed: timeout");
```

---

## opener

使用操作系统默认应用打开文件、URL 和路径。

**Rust crate：** `tauri-plugin-opener = "2"`
**JS 包：** `@tauri-apps/plugin-opener`
**权限：** `"opener:default"`、`"opener:allow-open-url"`、`"opener:allow-open-path"`、`"opener:allow-open-path-in-explorer"`、`"opener:allow-reveal-item-in-dir"`

### JS API

```typescript
import { openUrl, openPath, revealItemInDir } from "@tauri-apps/plugin-opener";

await openUrl("https://example.com");
await openPath("/path/to/file.pdf");
await revealItemInDir("/path/to/file.pdf"); // 在文件资源管理器中打开并选中该文件
```

### Rust API

```rust
app.opener().open_path("/path/to/logs", None::<&str>)?;
app.opener().open_url("https://example.com", None::<&str>)?;
```
