# 🍅 Pomo

极简 macOS 顶部任务栏（状态栏）番茄钟，基于 Python + `rumps` 构建，支持 `uv tool install` 一键全局安装。

## ✨ 特性

- **极简专注**：纯单次 25 分钟专注倒计时，无繁琐配置与休息周期负担，结束后手动开启下一个。
- **低干扰显示**：
  - 空闲时：顶部任务栏仅显示 `🍅`
  - 专注中：显示 `🍅 25m`（按分钟跳动，避免秒数跳动带来的焦虑）
  - 暂停时：显示 `⏸ 25m`
- **原生通知与音效**：25 分钟到点自动弹出 macOS 原生通知横幅，并播放系统清脆的 `Glass` 提示音。
- **今日统计**：下拉菜单内实时展示 `今日完成: X 🍅`（数据保存在 `~/.pomo/stats.json`，跨天自动归零）。
- **无 Dock 图标**：以 macOS `Accessory` 模式运行，仅驻留顶部状态栏，不占用程序坞（Dock）。
- **公司电脑友好**：通过 `uv tool install` 运行，另提供 `pomo install-app` 生成本地免签名脚本包 `~/Applications/Pomo.app`，不会触发企业环境 Gatekeeper 拦截。

---

## 📦 安装

确保已安装 [uv](https://docs.astral.sh/uv/)：

### 从 GitHub 直接安装

```bash
uv tool install git+https://github.com/codescv/pomo.git
```

### 从本地源码安装

```bash
git clone https://github.com/codescv/pomo.git
cd pomo
uv tool install .
```

> 开发调试时可使用可编辑模式安装：`uv tool install --editable .`

---

## 🚀 使用方法

安装后，在终端任意位置输入 `pomo` 即可在后台启动顶部任务栏图标并立即释放终端：

```bash
# 默认在后台启动顶部任务栏番茄钟（立即释放终端）
pomo

# 查看当前运行状态与今日完成的番茄数
pomo status

# 停止后台运行的番茄钟
pomo stop

# 在前台运行（适合调试）
pomo fg
```

### 可选：生成 macOS 应用程序（Spotlight / 开机自启）

如果你希望通过 Spotlight（聚焦搜索 `Pomo`）启动或添加到 macOS「系统设置 → 通用 → 登录项」开机自启：

```bash
pomo install-app
```

该命令会在 `~/Applications/Pomo.app` 生成一个轻量级启动器，直接复用本地 `uv` 工具环境，不含外部未签名 Mach-O 二进制，**不会触发公司电脑的 Gatekeeper 拦截**。

如需移除：

```bash
pomo uninstall-app
```

---

## 🛠️ 本地开发

```bash
# 同步依赖并直接运行
uv run pomo fg
```

## 📄 License

[MIT](./LICENSE)
