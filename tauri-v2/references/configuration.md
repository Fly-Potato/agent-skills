# Tauri v2 配置参考

`tauri.conf.json` 结构完整参考。

## 目录
- [顶级键](#顶级键)
- [build](#build)
- [app](#app)
- [app > windows](#app--windows)
- [app > security](#app--security)
- [app > trayIcon](#app--trayicon)
- [bundle](#bundle)
- [bundle > windows（NSIS/MSI）](#bundle--windows-nsimsi)
- [bundle > macOS（DMG）](#bundle--macos-dmg)
- [bundle > linux（deb/AppImage）](#bundle--linux-debappimage)
- [plugins](#plugins)
- [平台特定配置](#平台特定配置)
- [Schema](#schema)

---

## 顶级键

```jsonc
{
  // 唯一标识符（反向域名风格）
  "identifier": "com.example.myapp",

  // 显示名称（v1 中为 "package > productName"）
  "productName": "MyApp",

  // 版本字符串（语义化版本）
  "version": "1.0.0",

  // 适用于包含多个二进制文件的应用
  "mainBinaryName": "my-app",

  "build": { /* ... */ },
  "app": { /* ... */ },
  "bundle": { /* ... */ },
  "plugins": { /* ... */ }
}
```

### v1 关键变更对照

| v1 位置 | v2 位置 |
|---|---|
| `package > productName` | 顶级键 `productName` |
| `package > version` | 顶级键 `version` |
| `tauri` | `app` |
| `tauri > bundle` | 顶级键 `bundle` |
| `build > distDir` | `build > frontendDist` |
| `build > devPath` | `build > devUrl` |
| `build > withGlobalTauri` | `app > withGlobalTauri` |
| `tauri > allowlist` | **已移除**（使用 capabilities） |
| `tauri > windows` | `app > windows` |
| `tauri > systemTray` | `app > trayIcon` |

---

## build

控制开发期间前端如何构建和提供开发服务：

```jsonc
{
  "build": {
    // 启动前端开发服务器的命令
    "beforeDevCommand": "pnpm dev",

    // 开发期间 Tauri 连接的前端 URL
    "devUrl": "http://localhost:1420",

    // 为生产环境构建前端的命令
    "beforeBuildCommand": "pnpm build",

    // 已构建前端产物的路径（相对于 src-tauri/）
    "frontendDist": "../dist",

    // 可选：覆盖命令的参数
    "beforeDevCommandArgs": [],
    "beforeBuildCommandArgs": []
  }
}
```

---

## app

核心应用配置：

```jsonc
{
  "app": {
    // 将 Tauri API 暴露为 window.__TAURI__ 或 window.__TAURI_INTERNALS__
    "withGlobalTauri": true,

    // 窗口配置（数组，支持多个窗口）
    "windows": [ /* ... */ ],

    // 安全配置
    "security": { /* ... */ },

    // 系统托盘配置
    "trayIcon": { /* ... */ }
  }
}
```

---

## app > windows

定义应用窗口（静态配置）：

```jsonc
{
  "windows": [
    {
      // 唯一窗口标识符（用于 capabilities、事件、JS API）
      "label": "main",

      // 窗口标题
      "title": "My Application",

      // 初始尺寸（逻辑像素）
      "width": 800,
      "height": 600,

      // 最小尺寸
      "minWidth": 400,
      "minHeight": 300,

      // 最大尺寸
      "maxWidth": null,
      "maxHeight": null,

      // 位置
      "x": null,
      "y": null,
      "center": true,

      // 行为标志
      "resizable": true,
      "minimizable": true,
      "maximizable": true,
      "closable": true,
      "fullscreen": false,
      "focus": true,
      "transparent": false,
      "decorations": true,        // 操作系统标题栏
      "visible": true,            // 立即显示
      "alwaysOnTop": false,
      "skipTaskbar": false,

      // 窗口 URL（相对于前端产物目录的路径，或绝对 URL）
      "url": "index.html",

      // 拖放
      "dragDropEnabled": true,    // v1 中为 "fileDropEnabled"

      // 阴影（macOS/Windows）
      "shadow": true,

      // 覆盖 WebView 的浏览器参数（Linux）
      "browserExtensionsEnabled": false,

      // 父窗口标签（用于创建子窗口）
      "parent": null,

      // <title> 标签模板（使用 {{title}} 作为占位符）
      "titleBarStyle": "visible", // "visible" | "transparent" | "overlay"
    }
  ]
}
```

---

## app > security

```jsonc
{
  "security": {
    // 显式启用特定的 capability 文件
    "capabilities": ["main-capability", "additional-capability"],

    // 内容安全策略
    "csp": {
      "default-src": "'self'",
      "connect-src": "ipc: http://ipc.localhost",
      "img-src": "'self' asset: http://asset.localhost blob: data:",
      "media-src": "'self' asset: http://asset.localhost blob: data:",
      "style-src": "'unsafe-inline' 'self' asset: http://asset.localhost blob: data:"
    },

    // 用于加载本地文件的资源协议
    "assetProtocol": {
      "enable": true,
      "scope": ["**"]  // 可访问文件的 glob 模式
    },

    // 冻结 Object.prototype（安全加固，默认启用）
    "freezePrototype": true,

    // 为 IPC 源使用 HTTPS 协议（默认: false，使用 http://tauri.localhost）
    "useHttpsScheme": false,
    
    // ISOLATED 模式：在使用隔离 iframe 时设置为 true
    "pattern": { "use": "isolation" }
  }
}
```

---

## app > trayIcon

```jsonc
{
  "trayIcon": {
    // 托盘图标路径（相对于 src-tauri/icons/）
    "iconPath": "icons/icon.png",

    // 托盘图标提示文字
    "tooltip": "My App",

    // 菜单项（与 Menu 相同格式）
    "menuOnLeftClick": false,

    "id": "main-tray",

    // 在 macOS 菜单栏中显示图标
    "showMenuOnLeftClick": false,

    // macOS 自定义图标模板
    "iconAsTemplate": true
  }
}
```

---

## bundle

打包与分发配置：

```jsonc
{
  "bundle": {
    // 启用打包
    "active": true,

    // 打包目标："nsis"/"msi"（Windows），"dmg"/"app"（macOS），"deb"/"rpm"/"appimage"（Linux）
    "targets": ["nsis"],

    // 图标路径（多种尺寸/格式）
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],

    // 版权声明字符串
    "copyright": "2024 My Company",

    // 包含的许可协议文件
    "licenseFile": "LICENSE",

    // 分类（应用商店分类）
    "category": "DeveloperTool",

    // 需要打包的外部二进制文件（"bin" 或 sidecar 名称）
    "externalBin": ["./sidecars/my-sidecar"],

    // 需要打包的额外资源文件
    "resources": ["./addon", "./config/config.json"],

    // 简短描述
    "shortDescription": "My desktop application",

    // 详细描述
    "longDescription": "A detailed description of the application...",

    // Windows 特定打包配置
    "windows": { /* ... */ },

    // macOS 特定打包配置
    "macOS": { /* ... */ },

    // Linux 特定打包配置
    "linux": { /* ... */ },

    // 更新器产物生成
    "createUpdaterArtifacts": true,  // 或 "v1Compatible"

    // 最低 WebView2 版本（Windows）
    "windows": {
      "webviewInstallMode": {
        "type": "downloadBootstrapper"  // 或 "embedBootstrapper"、"offlineInstaller"
      },
      "wix": null,
      "nsis": { /* ... */ }
    }
  }
}
```

---

## bundle > windows（NSIS/MSI）

### NSIS 安装程序

```jsonc
{
  "nsis": {
    // 安装程序模板："app" | "framework" | "sidecar"
    "template": "app",

    // 安装模式
    "installMode": "perUser",  // "perUser" | "perMachine" | "both"

    // 开始菜单快捷方式名称
    "displayLanguageSelector": true,

    // 添加到 PATH
    "registerFileExtensions": [],

    // 额外安装参数
    "installerIcon": "icons/icon.ico",
    "installerHeaderIcon": "icons/icon.ico"
  }
}
```

---

## bundle > macOS（DMG）

```jsonc
{
  "macOS": {
    // 最低 macOS 版本
    "minimumSystemVersion": "10.15",

    // 权限声明（代码签名）
    "entitlements": "Entitlements.plist",

    // DMG 配置
    "dmg": {
      "appPosition": { "x": 180, "y": 170 },
      "applicationFolderPosition": { "x": 480, "y": 170 },
      "windowSize": { "width": 660, "height": 400 }
    },

    // Apple 公证
    "signingIdentity": null
  }
}
```

---

## bundle > linux（deb/AppImage）

```jsonc
{
  "linux": {
    // DEB 包
    "deb": {
      "depends": ["libwebkit2gtk-4.1-0", "libgtk-3-0"],
      "desktopTemplate": null
    },

    // AppImage
    "appimage": {
      "bundleMediaFramework": false
    }
  }
}
```

---

## plugins

插件特定配置：

```jsonc
{
  "plugins": {
    "updater": {
      "pubkey": "dW50...",
      "endpoints": [
        "https://releases.example.com/{{target}}/{{arch}}/{{current_version}}"
      ]
    },
    "deep-link": {
      "desktop": { "schemes": ["myapp"] },
      "mobile": [{ "host": "example.com", "pathPrefix": ["/open"] }]
    },
    "sql": {
      "preload": {
        "db": "sqlite:data.db"
      }
    },
    "cli": {
      "description": "My CLI app",
      "args": [
        { "name": "config", "short": "c", "description": "Config file path" }
      ]
    }
  }
}
```

---

## 平台特定配置

Tauri 支持合并平台特定的配置文件：

```
src-tauri/
├── tauri.conf.json                # 基础配置
├── tauri.windows.conf.json        # Windows 覆盖配置
├── tauri.macos.conf.json          # macOS 覆盖配置
├── tauri.linux.conf.json          # Linux 覆盖配置
├── tauri.android.conf.json        # Android 覆盖配置
└── tauri.ios.conf.json            # iOS 覆盖配置
```

这些文件通过 JSON Merge Patch（RFC 7396）进行合并。平台特定文件会覆盖基础配置中的值。

### 通过 CLI 覆盖

```bash
pnpm tauri build --config src-tauri/tauri.beta.conf.json
```

---

## Schema

引用自动生成的 schema 以进行验证：

```json
{
  "$schema": "../node_modules/@tauri-apps/cli/config.schema.json"
}
```

这将在编辑 `tauri.conf.json` 时启用 IDE 自动补全和验证功能。