# BasaltOS 游戏使用说明

M4 在 M3 KDE、中文输入法和安装器基础上加入 Steam、Lutris、Gamescope、
MangoHud、GameMode，以及 AMD/Intel 的 64 位和 32 位 Mesa/Vulkan 驱动。
同时包含 Wine Staging、Winetricks、vulkan-tools、mesa-utils。

## 登录与首次启动

Live 图形账号为 **gamer / basaltos**。Steam 应在普通用户会话运行。
Live root 密码仍为 `basaltos`，保留控制台维护能力。
`gamer` 在 Live 启动时创建，不写入安装器解包的只读系统镜像；安装后使用自己创建的账号。

从桌面或 KDE“游戏”菜单打开 Steam、Lutris。Steam 首次运行会从 Valve 下载客户端更新和
运行库，需要联网及额外空间；这些动态内容和用户账号不预置到 ISO。
Arch 软件包的 core、extra、multilib 均使用清华源。
Steam 客户端、游戏、Lutris runner 与 GE-Proton 内容使用各自上游分发渠道，并非清华 Arch 软件包镜像。

Live 会话数据在重启后丢失，建议安装到硬盘后再下载大型游戏。
M4 Live 的可写层上限为内存的 50%，按实际写入使用内存；这为 Steam 首次更新预留空间。
QEMU 默认提供 16 GiB 内存，实际硬件也应给客户端和可写数据留下足够内存。
安装仍使用 M3 Calamares 的加密 btrfs、GRUB 与 Snapper 流程，见 [BUILD-M3.md](BUILD-M3.md)。

## Steam、Proton 与游戏安装

1. 启动 Steam，完成客户端更新，再登录自己的账号。
2. 在库中选择游戏并安装；首次启动按提示下载运行库与 Proton。
3. Windows 游戏可在“属性 → 兼容性”中强制选择 Valve Proton 或 Proton Experimental。
   全局兼容性选项随 Steam 客户端版本可能改变名称。
4. 优先保留每个游戏自己的兼容环境，不向 Steam 的 Proton 前缀批量运行 Winetricks。

Proton 由 Steam 按需下载，不等同于系统的 Wine Staging。
[Valve Proton 文档](https://partner.steamgames.com/doc/steamhardware/proton)
说明了兼容层及反作弊的支持条件。

Lutris 可通过“+”添加游戏或安装脚本，并在游戏配置中选择 runner。
Windows 非 Steam 游戏可选系统 Wine；按游戏需要下载 Lutris 管理的 runner。
新版本 Lutris 的 GE-Proton runner 可通过 umu 工作，参见
[GE-Proton 上游说明](https://github.com/GloriousEggroll/proton-ge-custom)。

## MangoHud 与 GameMode

Steam 游戏的“属性 → 启动选项”可填写：

```text
mangohud %command%
```

同时启用 GameMode：

```text
gamemoderun mangohud %command%
```

默认 MangoHud 配置位于 `~/.config/MangoHud/MangoHud.conf`，来自
`/etc/skel/.config/MangoHud/MangoHud.conf`，显示 FPS、帧时间曲线、CPU/GPU 使用率、
温度和内存。右 Shift+F12 切换显示。部分虚拟机或硬件没有温度传感器，相关值可能不显示。
设置项依据 [MangoHud 上游配置](https://github.com/flightlessmango/MangoHud/blob/master/data/MangoHud.conf)。

GameMode 用户服务已全局启用，在登录时启动。普通用户在登录前加入 `gamemode` 组，
以使用官方包允许的 CPU/GPU 优化助手；没有配置超频。
在 Konsole 检查：

```bash
systemctl --user status gamemoded --no-pager
gamemoderun mangohud vkcube
# 在另一个终端、上面的程序仍运行时：
gamemoded -s
```

`gamemoded -s` 的 active 表示当前有程序请求 GameMode；没有请求时显示 inactive 是正常状态，
与守护进程服务是否正在运行不同。参见 [GameMode 上游](https://github.com/FeralInteractive/gamemode)。
OpenGL 程序若普通包装未能注入，可尝试 `mangohud --dlsym glxgears`。
本次 QEMU 的软件 Vulkan 路径出现过 MangoHud FPS 为 0、帧时间为 inf 的异常；
正式叠加层验收使用 `gamemoderun mangohud --dlsym glxgears`，数值显示正常。
这是本机虚拟环境的实测边界，未验证物理 GPU 是否出现同样现象。

## 安装 Proton-GE

M4 未预装 ProtonUp-Qt；清华同步的 Arch 官方仓库中未查询到该包。
可选用 [ProtonUp-Qt 上游](https://github.com/DavidoTek/ProtonUp-Qt)，也可直接手动安装：

1. 先运行一次原生 Steam 完成初始化，然后完全退出 Steam。
2. 从 [GE-Proton 官方 Releases](https://github.com/GloriousEggroll/proton-ge-custom/releases)
   下载 **x86_64** 发行归档，按发行页提供的校验信息核验。不要下载 GitHub 自动生成的 Source code。
3. 在普通用户终端执行，`archive` 改为实际下载文件路径：

```bash
archive="$HOME/Downloads/GE-Proton11-11-x86_64.tar.gz"
steam_dir="$HOME/.steam/steam"
test -d "$steam_dir" || { echo '请先运行一次 Steam'; exit 1; }
mkdir -p "$steam_dir/compatibilitytools.d"
tar -xf "$archive" -C "$steam_dir/compatibilitytools.d"
```

4. 重新启动 Steam，在游戏“属性 → 兼容性”中选择新出现的 GE-Proton。

示例版本来自 2026-11-01 查询到的发行页；后续以下载文件的真实名称和版本为准。
安装位置与步骤依据 [GE-Proton Native 安装说明](https://github.com/GloriousEggroll/proton-ge-custom#native)。
本说明针对系统原生 Steam，Flatpak Steam 的目录和扩展安装方式不同。

## Gamescope

可在支持相应 Vulkan 能力的硬件上用窗口模式测试：

```bash
gamescope -w 1280 -h 720 -W 1920 -H 1080 -- vkcube
```

确认单独运行正常后，再按游戏需要在 Steam 启动项中使用 `gamescope -- %command%`。
QEMU 的软件渲染不能代表真实 GPU 性能，也不能保证 Gamescope 所需的所有 Vulkan 扩展。
NVIDIA 专有驱动未预装，实际 NVIDIA 硬件需安装匹配内核的驱动及对应 32 位用户库。

## 反作弊与兼容限制

以下是 **2026-11-01 核实的官方限制示例**，不是穷尽清单，也不是本项目逐个登录游戏实测的结果。
厂商可随更新改变支持状态，购买或下载前应再次查看官方公告。

| 游戏 | 当前限制与官方来源 |
| --- | --- |
| VALORANT | 官方 PC 要求为 Windows，且不支持虚拟机；BasaltOS 不提供其 Vanguard 运行环境。[Riot 要求](https://support.riotgames.com/en-us/valorant/support-tools/minimum-recommended-pc-specs) |
| Destiny 2 | 官方明确不兼容 Proton；绕过 SteamOS/Proton 限制可能导致封禁。[Bungie 政策](https://help.bungie.net/hc/en-us/articles/360049517431-Destiny-Account-Restrictions-and-Banning-Policies) |
| Apex Legends | EA 官方宣布阻止 Linux 访问，包含使用 Linux 的 Steam Deck。[EA 公告](https://forums.ea.com/blog/apex-legends-game-info-hub-en/dev-team-update-linux--anti-cheat/9468053) |
| Fortnite | 官方当前表示 Linux 尚不可用，并称正在重建 EAC、与发行版维护者适配安全要求；未来支持不能视为当前可玩。[Epic 支持](https://www.epicgames.com/help/c-34254770/c-Trending_0/can-i-play-fortnite-on-linux-a22610900) |

不能把所有使用 EAC 或 BattlEye 的游戏都归为不支持：Valve 文档说明，Proton 支持这些中间件，
但每个游戏仍需开发者启用或配置。Windows 内核级反作弊并不会因为安装 Proton-GE 就自动兼容。
[Valve 反作弊支持说明](https://partner.steamgames.com/doc/steamhardware/proton#1)

本阶段验收范围是客户端启动、图形叠加层和 GameMode 工作状态；没有登录个人 Steam 账号，
也没有把 QEMU 软件渲染结果当作实际游戏帧率或反作弊兼容证明。
