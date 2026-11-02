# BasaltOS

基于 Arch Linux 官方 archiso 的游戏与安全向发行版项目。

[官网](https://vyskoyenebo.github.io/BasaltOS/) ·
[文档](https://vyskoyenebo.github.io/BasaltOS/docs/QUICKSTART.html) ·
[下载 0.1.0](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.0)

**0.1.0 是首个公开版本，复用已经验收的 M6 镜像。** 当前使用测试签名身份，
Secure Boot 尚未启用，硬件与游戏兼容范围见 [发行说明](docs/RELEASE-NOTES-0.1.0.md)。

## 快速开始

1. 从 [Release](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.0) 下载三个 ISO 分片、
   `SHA256SUMS`、`SHA256SUMS.asc`、公钥和 `.sha256` 文件。
2. 核对公钥完整指纹并验证签名清单。用附件中的 `join-iso.py` 或 Linux 二进制拼接重组完整 ISO。
3. 确认完整 ISO 的 SHA-256，再用镜像写盘工具写入空 U 盘。写盘会清空所选 U 盘，先核对盘符与容量。
4. 从 U 盘启动，Live 登录为 `gamer / basaltos`。双击“安装 BasaltOS”，核对目标磁盘，按需选择 LUKS2 加密并创建自己的账号。

Windows（需 Python）重组与校验示例：

```powershell
python .\join-iso.py --release-dir . --version 0.1.0-m6 --output .\basaltos-0.1.0-m6-x86_64.iso
Get-FileHash .\basaltos-0.1.0-m6-x86_64.iso -Algorithm SHA256
```

完整 ISO：2,353,299,456 bytes，SHA-256：

```text
0fd12156f204a6b6535c19aca1ae0f229e8e8b02579772602e68530034a27281
```

完整步骤、签名信任边界和安装注意事项见 [快速开始](docs/QUICKSTART.md)。

## 进度与文档

已完成 M1 命令行 Live ISO 与 M2 KDE Plasma 图形桌面、中文拼音输入。
已完成 M3 Calamares 图形安装器、可选 LUKS2 加密、btrfs 子卷与 Snapper。
M3 ISO 已完成完整 GUI 安装，并通过 UEFI、BIOS 硬盘启动与 KDE 登录验收。
已完成 M4 游戏套件：Steam 登录窗口、OpenGL MangoHud、GameMode active、
Lutris 主界面和 Gamescope 嵌套窗口均通过最终 ISO 的 QEMU 验收。
M5 加入默认拒绝入站的 nftables、严格本地包签名、快照与 boot 备份更新工具，
以及每周只提醒的更新检查和隐私默认设置。最终验收记录见下方 M5 文档。
M6 加入测试 GPG 签名、自建 pacman 仓库、`--check-only` 与离线签名发布附件流程。
自建仓库默认关闭，试用公开源之前请阅读测试密钥与信任范围。
M7 增加个人公开仓库、官网、文档站与 0.1.0 Release，不改动 M6 系统镜像。

- M7 发布状态与链接：[`docs/M7-RESULTS.md`](docs/M7-RESULTS.md)
- 官网与公开发版维护：[`docs/PUBLISHING.md`](docs/PUBLISHING.md)
- 当前 M6 构建、仓库与发版：[`docs/RELEASE.md`](docs/RELEASE.md)
- M6 产物与验证证据：[`docs/M6-RESULTS.md`](docs/M6-RESULTS.md)
- 测试公钥：[`packaging/basaltos-key.asc`](packaging/basaltos-key.asc)
- M5 构建与启动：[`docs/BUILD-M5.md`](docs/BUILD-M5.md)
- M5 产物、截图与验收：[`docs/M5-RESULTS.md`](docs/M5-RESULTS.md)
- 防火墙、更新与恢复：[`docs/SECURITY.md`](docs/SECURITY.md)
- 隐私与第三方联网：[`docs/PRIVACY.md`](docs/PRIVACY.md)
- Secure Boot 自签名路线与限制：[`docs/SECUREBOOT.md`](docs/SECUREBOOT.md)
- M4 构建与启动：[`docs/BUILD-M4.md`](docs/BUILD-M4.md)
- M4 产物、截图与已知限制：[`docs/M4-RESULTS.md`](docs/M4-RESULTS.md)
- 游戏、Proton-GE、叠加层与兼容限制：[`docs/GAMING.md`](docs/GAMING.md)
- M3 构建与安装：[`docs/BUILD-M3.md`](docs/BUILD-M3.md)
- M3 验收结果与限制：[`docs/M3-RESULTS.md`](docs/M3-RESULTS.md)
- M1 构建与启动：[`docs/BUILD.md`](docs/BUILD.md)
- M1 验收结果：[`docs/M1-RESULTS.md`](docs/M1-RESULTS.md)
- M2 构建与启动：[`docs/BUILD-M2.md`](docs/BUILD-M2.md)
- M2 验收结果与校验值：[`docs/M2-RESULTS.md`](docs/M2-RESULTS.md)
- 环境故障与备用路径：[`docs/ENV-NOTES.md`](docs/ENV-NOTES.md)
- 上游 releng 来源：[`docs/UPSTREAM.md`](docs/UPSTREAM.md)
- archiso 配置：`profile/`
- ISO 产物：`out/`，不纳入 Git。

M6 Live 从 SDDM 登录：账号 **gamer**，密码 **basaltos**。进入 Plasma Wayland 桌面，
使用 KDE 官方 Breeze 登录主题、Breeze Light 桌面与 Next 壁纸。
默认语言 `zh_CN.UTF-8`、时区 `Asia/Shanghai`、键盘 `us`，延续 M1 配置。

NetworkManager 主管网络，使用 iwd 无线后端与 systemd-resolved DNS；
保留 `dhcpcd` 备用工具。Fcitx5 默认拼音，**Ctrl+Space** 切换中英文。
包含 Konsole、Dolphin、Ark、nano 和中文字体；本阶段未加入浏览器。
M4 包含 Steam、Lutris、Gamescope、MangoHud、GameMode 与 32 位依赖，
以及 AMD/Intel Vulkan、软件 Vulkan、Wine Staging 和 Winetricks。
Steam 客户端更新、Proton 和游戏内容在联网后按需下载。

Live 桌面保留“安装 BasaltOS”图标。安装器默认中文、btrfs，支持创建普通用户，
可勾选 LUKS2 加密。自动擦除布局保留明文 ESP 与 `/boot`，系统和 home 位于加密卷内；
安装后使用自定义账号登录。根目录与 home 均有独立 Snapper 配置，snap-pac 管理软件包事务快照。

M1 原始 ISO 保留在 `out/`，M2–M6 分别位于 `out/m2/` 至 `out/m6/`，均不纳入 Git。
历史构建文档分别对应 M1 提交 `7e4c075`、`m2-desktop`、`m3-installer`、`m4-gaming`；
当前 profile 使用 M6 构建流程。为保留既有品牌文件，安装器页面仍沿用 M3 文案，
`PRETTY_NAME` 仍为 BasaltOS M4；本次版本由 `m6-release` 标签和 ISO 校验值标识。
Windows QEMU 首次启动 M6 Live ISO 并新建本项目测试盘：

```powershell
Set-Location E:\BasaltOS
.\scripts\start-m6-qemu.ps1 -Boot live -Firmware uefi -Accelerator whpx -CreateDisk
```

已有测试盘时去掉 `-CreateDisk`；安装后正常关机，使用 `-Boot disk` 从硬盘启动。
M6 测试盘位于 `work/m6/`，不附加其他系统盘。M4 启动脚本仍可用于无硬盘游戏验收，
M3 旧测试盘继续保存在 `work/m3/`，历史构建工作盘和测试文件均位于本项目 `work/`。

首次使用可运行 `python scripts/setup-qemu-windows.py` 准备项目内便携 QEMU。
构建仍使用独立 VirtualBox 构建机；与其他虚拟机并列注册在默认管理器，磁盘彼此独立。
