# BasaltOS 隐私与联网说明

**BasaltOS 项目不收集任何遥测数据。** 项目没有遥测服务器、设备标识上报、使用行为
统计或崩溃上传服务，M5 新增更新工具也不向项目方发送数据。

这项承诺针对 BasaltOS 自己的组件，不能代表预装的第三方应用。Steam、游戏、Lutris、
Wine/Proton 辅助组件连接各自服务，其账号、商店、下载、硬件信息及崩溃处理受各自政策约束。
M4 实测曾出现 Steam 自带的崩溃上传行为，因此不能声称“整套第三方软件绝不联网或上传”。
项目不预登录任何账号，不代理游戏账号数据；不需要这些功能时可以不启动或卸载应用。

## 默认状态与关闭方式

| 组件 | 用途与默认状态 | 控制方式 |
| --- | --- | --- |
| NetworkManager / iwd | DHCP、Wi-Fi、网络连接 | KDE 网络面板关闭网络，或 `sudo systemctl stop NetworkManager`；会断网 |
| systemd-resolved | DNS 解析，只绑定本地 stub；LLMNR/mDNS 关闭 | 配置 `/etc/systemd/resolved.conf.d/zz-basaltos-security.conf`；停服务会影响域名解析 |
| avahi | 服务与 socket 已 mask，未做局域网发现 | 保持屏蔽；有需要再明确解除并配置防火墙 |
| systemd-timesyncd | 联网校时，保证 TLS/包签名时间正常 | `sudo timedatectl set-ntp false`；注意手动校时 |
| NetworkManager 连通性探测 | 关闭，不自动访问探测页面 | `/etc/NetworkManager/conf.d/90-basaltos-privacy.conf` |
| KDE KUserFeedback | 系统范围默认 `Enabled=false` | `/etc/xdg/KDE/UserFeedback.conf`；用户自定义配置可能覆盖系统默认，应另行检查 |
| basaltos-update-check.timer | 每周访问清华镜像检查版本，仅本地保存结果 | `sudo systemctl disable --now basaltos-update-check.timer` |
| BasaltOS 桌面更新提醒 | 每分钟读取本地结果，不联网 | 在 KDE 自动启动中禁用“BasaltOS 更新提醒”，或创建同名用户 autostart 文件并设 `Hidden=true` |
| pacman / archlinux-keyring WKD | 手动更新包、按上游机制更新公钥/校验 | 审阅 `systemctl list-timers`；可停 `archlinux-keyring-wkd-sync.timer`，但需自行维护可信 keyring |
| Steam | 启动后访问 Valve 登录/CDN，可产生崩溃上传与局域网功能 | 退出 Steam、关闭其开机启动，或卸载 `steam`；离线模式不等同于普遍隐私保证 |
| Lutris / Winetricks / Proton | 用户启动后查询元数据、下载 runner/依赖/游戏 | 不启用对应功能，退出或卸载；安装脚本由用户审阅 |
| GameMode / MangoHud | 本地性能调节、叠加显示 | 无需项目网络服务；退出游戏或用户服务即可停止 |

KUserFeedback 的上游实现读取全局 `KDE/UserFeedback` 设置中的 `[UserFeedback] Enabled`；
M5 通过 Qt 系统配置回退提供关闭默认值，不依赖不存在的环境变量。
依据 [KDE 实现](https://raw.githubusercontent.com/KDE/kuserfeedback/master/src/provider/core/provider.cpp)
及 [Qt 配置回退机制](https://doc.qt.io/qt-6/qsettings.html#fallback-mechanism)。
NetworkManager 探测开关见 [官方配置文档](https://www.networkmanager.dev/docs/api/latest/NetworkManager.conf.html)。

## 自行审计

```bash
systemctl --type=service --state=running
systemctl --user --type=service --state=running
systemctl list-timers --all
ss -tulnp
ps -ef | grep -Ei 'telemetry|feedback|report|crash'
cat /etc/xdg/KDE/UserFeedback.conf
```

M5 在新安装、未启动第三方游戏应用的桌面检查默认服务与监听；服务名称检索是辅助检查，
不能单独证明第三方 SDK 没有联网。持续网络行为还需抓包或按应用审计。
DNS、时间同步、软件镜像会看到客户端 IP 与必要请求；它们不是 BasaltOS 遥测服务器。
日志保存在本机，提交故障报告前请自行检查用户名、路径、IP 等信息。
