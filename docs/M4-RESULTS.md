# M4 验收结果

2026-11-01（Asia/Shanghai）：M4 游戏版 ISO 已构建，最终冷启动会话完成 Steam 登录窗口、
OpenGL MangoHud、GameMode active 验收；补测 Lutris、Gamescope、中文输入及安装器启动。
交付标签为 `m4-gaming`。没有登录个人游戏平台账号或安装商业游戏。

## 产物与构建

- ISO：`E:\BasaltOS\out\m4\basaltos-2026.11.01-x86_64.iso`
- 大小：`2347679744` 字节，即 `2.348 GB / 2.186 GiB / 2238.92 MiB`，低于 8 GB。
- SHA-256：`e38cb3847621a6136bed4f582ffa973ea7f4827ba9cd179b8609cd6aa3643535`
- 校验文件：`out/m4/basaltos-2026.11.01-x86_64.iso.sha256`
- ISO9660 卷标实读：`basaltos`；宿主重新计算的 SHA-256 与构建机一致。
- 官方构建工具：archiso `92-1`；最终 profile 源码提交：`e95e32e`。
- 最终构建源快照：`/root/BasaltOS/work/m4-native/m4-source.jTcUOJse`。
- 最终工作目录：`/root/BasaltOS/work/m4-native/linux-build/m4.lR4DPzrC`。
- 构建日志：`out/m4/build.log`、`work/m4/build-vm.log`。

沿用原 VirtualBox 构建机，M4 使用新增的项目内 64 GiB ext4 工作虚拟盘。
core、extra、multilib 均为清华镜像；复用 M3 的自建 Calamares 包。
完整环境准备、构建调用与 QEMU 参数见 [BUILD-M4.md](BUILD-M4.md)。

| 游戏组件 | 最终 ISO 软件包版本 |
| --- | --- |
| Steam / steam-devices | 1.0.0.87-3 |
| Lutris | 0.5.22-3 |
| Gamescope | 3.17.0-1 |
| MangoHud / lib32-mangohud | 0.8.4-1 |
| GameMode | 1.8.2-3 |
| lib32-gamemode | 1.8.2-1 |
| Mesa / lib32-mesa | 1:26.2.6-1 |
| AMD / Intel / software Vulkan，含 32 位 | 1:26.2.6-1 |
| Vulkan loader，含 32 位 | 1.4.363.0-1 |
| Wine Staging | 11.21-1 |
| Winetricks | 20260125-2 |
| python-protobuf | 36.1-1 |

Steam 表内为 Arch 启动包版本，完整客户端在首次启动时从 Valve 更新。
Valve Proton、GE-Proton 和游戏内容不预下载到 ISO；安装方法见 [GAMING.md](GAMING.md)。

## 实际 QEMU 验收

```powershell
& E:\BasaltOS\scripts\start-m4-qemu.ps1 -Accelerator whpx
```

实际验收加 `-Display none`，通过本机 `127.0.0.1:4454` QMP 操作和截图。
UEFI、WHPX（Windows `-accel whpx`）、16 GiB RAM、4 vCPU、virtio 显卡与 NAT 网卡。
**未附加任何硬盘或宿主物理磁盘。** TCG 回退路径保留，本次未使用。
Live 登录为 `gamer / basaltos`，Steam 进程在普通用户会话运行。

| 检查 | 最终结果 |
| --- | --- |
| Steam 默认启动 | 桌面快捷方式启动，完成约 505 MB 客户端更新，出现完整登录窗口；未登录 |
| Live 可写层 | 冷启动自动扩到约 7.9 GiB；19:51 检查时约 7.5 GiB 可用；没有手工 remount |
| MangoHud | `gamemoderun mangohud --dlsym glxgears -geometry 960x640` 显示有效 FPS、毫秒帧时间、曲线与 GameMode ON |
| GameMode 服务 | `UnitFileState=enabled`、`ActiveState=active`、`SubState=running` |
| GameMode 请求 | `gamemoded -s` 为 `gamemode is active`，客户端列表中为实际运行的 `glxgears`（PID 3431） |
| Lutris | 主窗口正常打开，Steam、Wine 等入口可见；protobuf 缺失提示已消除 |
| Gamescope | 实际显示嵌套的 Vkcube X11 窗口；640×480 内容输出到 960×640 窗口 |
| Vulkan / OpenGL 驱动 | 均检测到 llvmpipe（LLVM 23.1.4），属于 CPU 软件渲染 |
| 网络 | enp0s3 为 10.0.2.15/24；清华镜像 HTTPS 返回 HTTP/2 200；Steam 更新成功 |
| 中文环境 | zh_CN.UTF-8、Asia/Shanghai 保留；Fcitx5 进程存在，实际拼音输入“中文”成功 |
| 安装器启动 | 从普通用户桌面授权启动 Calamares 中文欢迎页；无硬盘时正确阻止继续安装 |

Gamescope 命令：

```bash
timeout 45s gamescope -w 640 -h 480 -W 960 -H 640 -- vkcube
```

已观察并截图实际嵌套窗口，随后由设定的 45 秒时限结束，返回 124 是 `timeout` 的预期结果。
本次 M4 没有重新执行硬盘安装；M3 的完整加密安装验收保留在 [M3-RESULTS.md](M3-RESULTS.md)。

实际检查脚本为 `scripts/check-m4-session.sh`。最终会话日志：

- `work/m4/session-check.log`：`M4_SESSION_BASELINE_PASSED`，含包版本、可写层、服务、驱动与网络。
- `work/m4/gamemode-check.log`：`M4_GAMEMODE_ACTIVE_PASSED`，含实际 OpenGL 客户端。
- `work/m4/final-steam-console.log`：最终 ISO 的 Steam 更新和客户端启动日志。
- `work/m4/final-m4-glxgears.log`、`work/m4/final-m4-gamescope-final.log`、`work/m4/final-m4-lutris.log`。
- `work/m4/final-boot-units.log`：保留未隐藏的启动单元状态。

## 截图

均来自最终 ISO 的真实 QMP `screendump`，没有合成叠加层或后期编辑画面。

- [Steam 登录窗口](m4-steam.png)
- [MangoHud OpenGL 叠加层](m4-mangohud.png)
- [GameMode enabled / active 与真实客户端](m4-gamemode.png)
- [游戏版桌面](m4-desktop.png)、[SDDM](m4-sddm.png)
- [Lutris 主界面](m4-lutris.png)、[Gamescope 嵌套窗口](m4-gamescope.png)
- [中文输入](m4-ime.png)、[安装器启动检查（无硬盘）](m4-installer.png)

## 修复与已知限制

- 首次候选的 releng Live 可写层只有 256 MiB，Steam 因剩余空间不足 250 MB 而退出。
  M4 启动准备服务现仅在 Live 中将该 tmpfs 上限设为内存的 50%，按写入使用内存。
  最终 ISO 冷启动已验证修复，硬盘安装不使用这项 Live remount。
- 已修正 Lutris 官方图标名称，并加入官方包的可选 protobuf 依赖。
- 本机 QEMU 软件 Vulkan 路径的 MangoHud 曾持续显示 FPS=0、帧时间=inf；
  OpenGL 路径显示正常，因此正式 B 项使用用户允许的 glxgears 路径。
  未验证物理 GPU 是否出现同样现象，也未将其声明为已修复。
- QEMU 不提供真实 GPU 直通、完整 CPU 调频/缓存拓扑或温度传感器。
  GameMode 日志有缺少 cpufreq、缓存、绑核及请求包装进程的提示；active 不等于已验证性能提升。
  HUD 的 CPU 温度 0°C、缺少 GPU 温度不是实际硬件温度。
- Gamescope 已显示窗口，但日志仍有缺少 CAP_SYS_NICE、部分 DRM 扩展等虚拟环境提示。
  未测试物理 GPU、HDR、VRR、NVIDIA 专有驱动或真实游戏帧率。
- 启动时光驱自动映像探测 `systemd-loop@...sr0.service` 报 `No suitable partitions found`，
  最终单元列表中仍有该失败记录；未阻止读取 Live ISO、KDE 和游戏套件验收。
  没有为隐藏此提示修改 M3 的启动配置。
- Live 数据重启后不保留。Steam、Lutris runner、Proton 和游戏内容需要各自上游网络渠道。
  未登录账号、未测试商业游戏或反作弊对局。反作弊限制清单按官方资料核实，见游戏说明。
- Calamares 保留 M3 配置与品牌版本号。本次只检查启动；没有附加磁盘，欢迎页的空间/分区提示为预期。

## M1–M3 保留情况

`scripts/check-m4-baseline.py` 对照来自 `m3-installer` 的清单，校验 28 个文件/链接：
hostname、locale、时区、keymap、启动菜单、Calamares 分区/挂载/品牌配置，以及
负责加密、GRUB、btrfs、Snapper 的目标配置脚本均保持一致。
pacman 配置的有意变化仅为增加清华 `[multilib]`。
M1、M2、M3 三份历史 ISO 已复核 SHA-256 不变。

M4 构建盘和测试文件均位于 `E:\BasaltOS\work\`；飞牛虚拟机与其他项目未改动。
构建机、QEMU 测试机在收尾时正常关闭。
