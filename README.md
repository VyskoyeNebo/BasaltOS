# BasaltOS

基于 Arch Linux 官方 archiso 的游戏与安全向发行版项目。
已完成 M1 命令行 Live ISO 与 M2 KDE Plasma 图形桌面、中文拼音输入。
已完成 M3 Calamares 图形安装器、可选 LUKS2 加密、btrfs 子卷与 Snapper。
已用最终 ISO 完成完整 GUI 安装，并通过 UEFI、BIOS 硬盘启动与 KDE 登录验收。

- 当前 M3 构建与安装：[`docs/BUILD-M3.md`](docs/BUILD-M3.md)
- M3 验收结果与限制：[`docs/M3-RESULTS.md`](docs/M3-RESULTS.md)
- M1 构建与启动：[`docs/BUILD.md`](docs/BUILD.md)
- M1 验收结果：[`docs/M1-RESULTS.md`](docs/M1-RESULTS.md)
- M2 构建与启动：[`docs/BUILD-M2.md`](docs/BUILD-M2.md)
- M2 验收结果与校验值：[`docs/M2-RESULTS.md`](docs/M2-RESULTS.md)
- 环境故障与备用路径：[`docs/ENV-NOTES.md`](docs/ENV-NOTES.md)
- 上游 releng 来源：[`docs/UPSTREAM.md`](docs/UPSTREAM.md)
- archiso 配置：`profile/`
- ISO 产物：`out/`，不纳入 Git。

Live 从 SDDM 登录：账号 **root**，密码 **basaltos**。进入 Plasma Wayland 桌面，
使用 KDE 官方 Breeze 登录主题、Breeze Light 桌面与 Next 壁纸。
默认语言 `zh_CN.UTF-8`、时区 `Asia/Shanghai`、键盘 `us`，延续 M1 配置。

NetworkManager 主管网络，使用 iwd 无线后端与 systemd-resolved DNS；
保留 `dhcpcd` 备用工具。Fcitx5 默认拼音，**Ctrl+Space** 切换中英文。
包含 Konsole、Dolphin、Ark、nano 和中文字体；本阶段未加入浏览器。

M3 Live 桌面有“安装 BasaltOS”图标。安装器默认中文、btrfs，支持创建普通用户，
可勾选 LUKS2 加密。自动擦除布局保留明文 ESP 与 `/boot`，系统和 home 位于加密卷内；
安装后使用自定义账号登录。根目录与 home 均有独立 Snapper 配置，snap-pac 管理软件包事务快照。

M1 原始 ISO 保留在 `out/`，M2 位于 `out/m2/`，M3 位于 `out/m3/`，均不纳入 Git。
历史 M1/M2 构建文档分别对应 M1 提交 `7e4c075` 与标签 `m2-desktop`，当前 profile 使用 M3 构建流程。
Windows QEMU 启动新空白测试盘与 Live ISO：

```powershell
Set-Location E:\BasaltOS
.\scripts\start-m3-qemu.ps1 -Boot live -Firmware uefi -Accelerator whpx -CreateDisk
```

`-CreateDisk` 拒绝覆盖已有磁盘。安装并关机后，执行
`.\scripts\start-m3-qemu.ps1 -Boot disk -Firmware uefi -Accelerator whpx`，从硬盘启动。
所有测试磁盘限制在本项目 `work/m3/`，不会连接宿主物理磁盘。

首次使用可运行 `python scripts/setup-qemu-windows.py` 准备项目内便携 QEMU。
构建仍使用独立 VirtualBox 构建机；与其他虚拟机并列注册在默认管理器，磁盘彼此独立。
