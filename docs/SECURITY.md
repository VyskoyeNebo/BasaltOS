# BasaltOS M5 安全策略

适用范围：M5 Live 与通过 Calamares 新安装的系统。M1–M4 的桌面、输入法、
LUKS、子卷、Snapper、GRUB 和游戏设置保留；旧安装不会因下载新 ISO 自动获得这些设置。

## 防火墙与本地网络

`/etc/nftables.conf` 使用独立的 `inet basaltos_filter` 表：input 默认 drop，
output 默认 accept。允许 lo、已建立/相关连接、ICMP/ICMPv6、DHCPv4 客户端
67→68 与 DHCPv6 客户端 547→546。ICMPv6 包括邻居发现，避免阻断 IPv6 基础通信。
不添加 forward 链，不开启 IP 转发，不全局清空其他软件的规则。

```bash
sudo nft list ruleset
sudo nft -c -f /etc/nftables.conf
sudo systemctl reload nftables
sudo ss -tulnp
```

规则文件以 `destroy table inet basaltos_filter` 后重建同一张表，整体作为 nft
事务加载；该命令允许表尚不存在。服务补充 `RemainAfterExit=yes`，停止时仅移除自己的表。
NetworkManager Requires/After nftables：规则加载失败时不启动主管网络。
停止 nftables 也会停止 NetworkManager；修复规则后启动两者。
不要为临时改规则重启网络，优先 `systemctl reload nftables`。
参见 [nft 官方手册](https://man.archlinux.org/man/nft.8.en)。

允许正常出站的 DNS、HTTPS、Steam 下载及其回包。新入站连接默认被阻断，
局域网游戏主机、Steam Remote Play、文件共享需要用户按实际端口、接口、来源添加规则。
没有全开放 Steam 端口。mDNS/LLMNR 默认关闭，avahi 服务与 socket 被屏蔽；
`.local` 自动发现、网络打印机/共享发现可能需要明确启用并添加相应防火墙规则。
普通路由器 DNS、DHCP、IP 直连不依赖这些发现协议。

默认审计应在启动 Steam、Lutris 等应用前进行。systemd-resolved 的
127.0.0.53/127.0.0.54:53 是回环 DNS 监听；DHCP 客户端端口属于必要网络服务。
应用后续主动监听不能视为基础系统默认监听。Wayland/X11 的 Unix socket 不算 TCP 服务。

## 软件包信任

构建与安装后的官方源均为清华 Arch 镜像，含 multilib。
`SigLevel = Required DatabaseOptional` 要求软件包签名；DatabaseOptional 仅表示仓库数据库
签名可选，并非包签名可选。`LocalFileSigLevel = Required` 同样拒绝未签名本地包。
保留 `archlinux-keyring`、Live 的 pacman-init 与安装器的持久 keyring 初始化。
不要用关闭签名检查来处理更新故障，应检查时间、keyring 与官方公告。

**构建时例外**：M3 延续的 Calamares 3.4.3 是本机编译的未签名包，不属于 Arch 官方签名链。
仅构建暂存配置的 `basaltos-local` 仓库使用 `Optional TrustAll`；安装后的 pacman.conf
不保留这个仓库。M5 在构建前额外验证主包 SHA-256：
`962127440180c43f8b8752174de190c9e29c364178acbe1bd406003580e40f81`。
这是固定构建输入的完整性检查，不能替代发行者 PGP 签名或上游安全审计。

## 更新、检查与快照

```bash
# 普通用户在安装后的 Konsole 中运行：
sudo basaltos-update --dry-run
sudo basaltos-update
systemctl list-timers basaltos-update-check.timer
sudo systemctl start basaltos-update-check.service
cat /var/lib/basaltos-update-check/result.json
```

`--dry-run` **会真实创建** root 的 pre/post 快照与 `/boot`、已挂载 ESP 的归档，
只用 checkupdates 在隔离数据库检查更新；不安装包、不刷新真实 pacman 同步库。
脚本核对前后 `pacman -Q` 清单。Live 的临时 overlay 无法提供持久 root 快照，
会明确拒绝；应在通过 M3/M5 安装器安装的 btrfs 系统验证。

正常模式先保留 pre 快照、已安装包清单、boot/ESP 归档及 SHA-256，再交互执行完整
`pacman -Syu`，成功后创建配对 post 快照。snap-pac 原有事务钩子继续保留。
脚本只支持 M3 固定 `@` 根子卷和独立 `/boot` 布局，归档或快照失败便中止更新。
准备期间使用 pacman 数据库锁，更新脚本自身还持有独占锁；不要并行运行其他包管理器。
异常中断后应先核实有没有 pacman 在运行，不能直接删除真实系统的 db.lck。

每周 timer 运行 `checkupdates --nocolor`，只更新 `/var/cache/basaltos-update-check/db`
中的临时仓库库，不下载/安装包。服务将系统文件设为只读，仅允许自己的缓存、状态、
临时目录和 GnuPG keyring 必要的锁/信任文件写入。退出码 0 表示有更新，2 表示无更新。
桌面提醒程序只读本地结果，每分钟查看一次，不联网；Live 不运行自动检查。
这些检查仍会访问清华镜像，见 [隐私说明](PRIVACY.md)。
参见 [checkupdates 手册](https://man.archlinux.org/man/checkupdates.8.en) 与
[Arch 系统维护说明](https://wiki.archlinux.org/title/System_maintenance)。

快照和归档默认保留，位置 `/var/lib/basaltos-update/transactions/ID/`，仅 root 可读。
确认系统稳定后可用 `snapper -c root delete PRE POST` 删除相应快照，再删除对应 ID 的归档目录。
留意空间；归档是文件系统内的恢复材料，不是外置备份，磁盘损坏或 LUKS 密钥丢失时无效。
`@home` 有独立 Snapper 配置；软件更新只额外快照 root，不回退用户文档。

## 更新失败后的离线恢复

失败时脚本打印具体 ID：

```bash
sudo basaltos-update --recovery-info 20261102T000000Z-00000000
```

替换为实际 ID。这条命令先核对归档 SHA-256，**只打印**对应 UUID、快照与离线恢复命令。
保存输出到外置介质；重启 Live 后先检查 `lsblk -f`，只解锁、挂载自己的 BasaltOS 测试盘。
不得对飞牛 OS、Windows 或共享 ESP 照抄执行。系统已经无法启动时，可从 Live 挂载当前 `@`，
读取其 `/var/lib/basaltos-update/transactions/ID/manifest.json` 与本脚本。

M3 GRUB 的 `rootflags=subvol=@` 固定指定根子卷；简单 `snapper rollback` 改默认子卷
不会切换启动根，因此这里使用离线创建可写快照并替换 `@` 的方式。
旧根保留为 `@.before-recovery-ID`，保留并移回单独的 `.snapshots` 子卷；
`@home`、`@log`、`@cache` 不动。pre 快照包含脚本准备阶段自己的 db.lck，
恢复时仅在**离线的新根**删除这个历史锁文件。

`/boot` 和 ESP 不在 root 快照内，必须恢复同一事务的归档，避免内核与 `/usr/lib/modules`
不匹配。打印的流程先归档当前 boot/ESP，再用临时目录解包和 rsync 恢复；
涉及 `--delete` 的步骤只用于已核实 UUID 的 M3 专属 boot/ESP 分区。
**共享多系统 ESP 不适用整分区恢复**，应逐项审阅 BasaltOS 自己的 EFI 文件。
EFI 固件 NVRAM 启动项不在归档内，丢失时另行修复。恢复需要用户从 Live 手动执行，
不自动对正在运行的根文件系统回滚。M5 验收范围见 [结果](M5-RESULTS.md)，不要把生成恢复命令
等同于完成断电、磁盘故障或所有回滚情形的测试。

参考 [Snapper 手册](https://man.archlinux.org/man/snapper.8.en)、
[Arch btrfs 子卷说明](https://wiki.archlinux.org/title/Btrfs)。
