# BasaltOS

基于 Arch Linux 官方 archiso 的游戏与安全向发行版项目。
已完成 M1 命令行 Live ISO 与 M2 KDE Plasma 图形桌面、中文拼音输入。
BIOS 启动已经实测；保留 UEFI 启动配置，尚未单独验收 UEFI。

- 构建与启动：[`docs/BUILD.md`](docs/BUILD.md)
- M1 验收结果：[`docs/M1-RESULTS.md`](docs/M1-RESULTS.md)
- M2 构建与启动：[`docs/BUILD-M2.md`](docs/BUILD-M2.md)
- M2 验收结果与校验值：[`docs/M2-RESULTS.md`](docs/M2-RESULTS.md)
- 环境故障与备用路径：[`docs/ENV-NOTES.md`](docs/ENV-NOTES.md)
- 上游 releng 来源：[`docs/UPSTREAM.md`](docs/UPSTREAM.md)
- archiso 配置：`profile/`
- ISO 产物：`out/`，不纳入 Git。

M2 从 SDDM 登录：账号 **root**，密码 **basaltos**。进入 Plasma Wayland 桌面，
使用 KDE 官方 Breeze 登录主题、Breeze Light 桌面与 Next 壁纸。
默认语言 `zh_CN.UTF-8`、时区 `Asia/Shanghai`、键盘 `us`，延续 M1 配置。

NetworkManager 主管网络，使用 iwd 无线后端与 systemd-resolved DNS；
保留 `dhcpcd` 备用工具。Fcitx5 默认拼音，**Ctrl+Space** 切换中英文。
包含 Konsole、Dolphin、Ark、nano 和中文字体；本阶段未加入浏览器。

M1 原始 ISO 保留在 `out/`，M2 位于 `out/m2/`，均不纳入 Git。
Windows QEMU 启动命令：

```powershell
Set-Location E:\BasaltOS
.\scripts\start-m2-qemu.ps1 -Accelerator whpx
```

首次使用可运行 `python scripts/setup-qemu-windows.py` 准备项目内便携 QEMU。
构建仍使用独立 VirtualBox 构建机；与其他虚拟机并列注册在默认管理器，磁盘彼此独立。
