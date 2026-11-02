# M5 安全加固验收结果

日期：2026-11-02。最终 ISO 经 QEMU/WHPX 启动、完整 Calamares 图形加密安装，
正常关闭 Live、移除 ISO 后从新硬盘启动并登录 KDE；M5 验收通过。
本次仅操作 `E:\BasaltOS` 与其专属虚拟磁盘，没有操作飞牛 OS 或其他项目的磁盘。

## 最终产物

| 项目 | 结果 |
| --- | --- |
| ISO | `E:\BasaltOS\out\m5\basaltos-2026.11.02-x86_64.iso` |
| 大小 | **2,353,299,456 bytes**，约 2.35 GB / 2.192 GiB，低于 8 GB |
| SHA-256 | `f7801b6c2d6d5633fa7087ee267557d39381bae59e1c02d6ba6413929768fd67` |
| 校验文件 | 同目录 `basaltos-2026.11.02-x86_64.iso.sha256` |
| ISO9660 卷标 | `basaltos`，构建机与 Windows 导出后均已检查 |
| archiso | `92-1` |
| 系统源 | core / extra / multilib，清华 HTTPS 镜像 |
| Git 版本 | `m5-security` |

构建命令与传输流程见 [BUILD-M5.md](BUILD-M5.md)。最终构建原生日志保留在
`out/m5/build.log`、`work/m5/build-vm.log`，这些大文件/运行日志不提交 Git。

## QEMU 与安装

Windows 便携 QEMU 11.1.3，**`-accel whpx` 成功**，没有回退 TCG；
UEFI、16 GiB RAM、4 vCPU、virtio 设备、NAT，唯一硬盘为 48 GiB qcow2，
序列号 `BASALTOS_M5_TARGET`。本次用 `-Display none` 配合 QMP 操作真实图形界面和截图。

```powershell
Set-Location E:\BasaltOS
# 已有本次测试盘，启动最终 Live ISO：
.\scripts\start-m5-qemu.ps1 -Boot live -Firmware uefi -Accelerator whpx
# 或直接启动已完成验收的加密安装系统：
.\scripts\start-m5-qemu.ps1 -Boot disk -Firmware uefi -Accelerator whpx
```

启动脚本默认 SDL，可见窗口便于手动操作；首次创建另一个测试盘的方法见构建文档。
本次测试盘：`E:\BasaltOS\work\m5\installed.qcow2`，独立 UEFI vars 同目录。
测试用户名 `basalt`，测试登录/root/LUKS 口令 **`Basalt-M5-2026`**，
仅用于这个可丢弃测试盘，不是 ISO 安装后的固定默认密码。
Live 仍为 M4 的 `gamer / basaltos`。

安装使用原有 M3 Calamares 配置，选择 LUKS2 + btrfs：ESP 512 MiB、
BIOS boot 8 MiB、独立 ext4 `/boot` 1536 MiB、LUKS2 内的 btrfs 剩余空间。
解锁后可见 `@`、`@home`、`@log`、`@cache`，root/home 两份 Snapper 初始快照均存在。
hostname=basaltos、zh_CN.UTF-8、Asia/Shanghai、us 均通过运行时检查。

## 安全验收

| 验收项 | 实际结果 |
| --- | --- |
| 默认防火墙 | nftables enabled、active；input policy drop，output policy accept；lo、连接回包、ICMP/ICMPv6、DHCP 客户端规则存在 |
| 无全局清空 | 临时创建无关 nft 表，reload 后仍存在；随后删除测试表 |
| 入站实际阻断 | 临时 HTTP 服务在来宾回环可访问；主机经 QEMU NAT 转发请求超时；临时允许端口后 HTTP 200；reload 恢复默认规则后再次超时 |
| 测试清理 | 临时服务退出；最终 drop 计数 7 packets / 308 bytes；没有保留放行规则 |
| 默认 TCP/UDP 监听 | 只看到 systemd-resolved 的 127.0.0.53/127.0.0.54:53；没有 5353/5355 或其他对外监听 |
| 出站联网 | DHCP 地址 10.0.2.15/24，获得 IPv6 地址；ping 清华域名 3/3，HTTPS 请求 HTTP/2 200 |
| Avahi/发现协议 | avahi-daemon.service/socket masked；最终配置 LLMNR=no、MulticastDNS=no |
| 包签名 | PackageRequired / TrustedOnly，LocalFileSigLevel Required；构造有效但无签名的测试包，安装被“软件包缺失签名”拒绝，确认未安装 |
| dry-run | 两次成功，root pre/post 分别为 2/3、4/5；真实创建快照、boot/ESP 备份，更新检查 0 项，没有安装软件，前后包清单一致 |
| 每周检查 | timer enabled/active；手动执行服务成功，结果 current、updates=[]、error 为空；下一周期 2026-11-09，随机延迟最多 30 分钟 |
| 默认隐私 | KDE 全局 UserFeedback Enabled=false，NetworkManager 探测关闭；系统/用户进程与默认服务检查未发现遥测服务 |

网络测试中的域名解析地址为本机网络返回的 `198.18.0.64`；没有把该 ping 延迟作为
公网直连清华服务器的证据。另行完成了实际 HTTPS 请求与更新元数据检查。
入站对照实验覆盖 IPv4 TCP；IPv6 规则存在，但没有另做 IPv6 入站探针。

验收使用 `scripts/accept-m5.sh`、`scripts/probe-m5-inbound.sh` 和
`scripts/test-m5-inbound.py`。完整现场日志在 `work/m5/installed-acceptance.log`、
`work/m5/inbound-host-test.json`、`work/m5/inbound-probe.log`、
`work/m5/calamares-session.log`，未纳入 Git。

截图取自最终 ISO 安装后的真实 KDE/Konsole，均通过查看检查：

- [m5-firewall.png](m5-firewall.png)：服务启用/运行状态，完整 input drop / output accept 规则。
- [m5-ports.png](m5-ports.png)：IP、TCP/UDP 本地 DNS 监听、Avahi masked、反馈开关。
- [m5-update.png](m5-update.png)：第二次 dry-run 成功，pre=4 / post=5、boot 归档散列及快照列表。

第二次更新事务：`20261102T020912Z-993775c4`，状态 `dry-run-complete`。
清单保存在测试盘 `/var/lib/basaltos-update/transactions/`，并导出
`work/m5/update-manifest.json` 供核对；其中：

```text
boot.tar SHA256 80ba0795b8ea67f726fe80e32447ee1d671397b2672ba5591101e7a1663637f5
esp.tar  SHA256 0b4734f1872efd4e8731a8b508bfe9338f06619d8162ae6354ed260a3d23ff70
```

安装后的已验证版本：nftables `1:1.1.7-3`、archlinux-keyring `20260909-1`、
pacman-contrib `1.13.1-1`、snapper `0.13.2-1`、snap-pac `3.0.1-3`。

## 修复经过与限制

首个候选版发现 mDNS 的配置排序问题：`90-basaltos-security.conf` 排在继承的
`archiso.conf` 前，后者又设 MulticastDNS=yes。改为 `zz-basaltos-security.conf`，
保持旧文件不动，新增排序检查与 5353/5355 运行时断言；重新构建后用全新测试盘完整安装复验通过。
首个候选 ISO 和磁盘分别保留在 `out/m5-candidate-01/`、`work/m5/candidate-01/`，不要当作最终产物。

QMP 注入确认早于 Qt 处理完成，连续切换表单曾出现漏字；工具补充短等待，重新填写、核对后才确认安装。
限时入站探针曾在对照请求时到期，改成同一宿主脚本连续测试后通过；没有遗留监听或放行规则。

首次安装的真实 pacman 同步库为空，`pacman -Q` 会显示缺库警告。
dry-run/每周检查使用隔离数据库，因此不会消除该警告；两次检查均成功，包清单未变。
不要为消除警告单独运行 `pacman -Sy`；首次正常完整 `basaltos-update` 会执行 `pacman -Syu`。

本次没有执行实际软件包升级或离线替换根子卷，验证的是快照/归档创建、完整性检查、
恢复命令生成和只读更新检查路径。[SECURITY.md](SECURITY.md) 说明固定 `@` 布局的离线恢复步骤，
不能直接照搬 `snapper rollback`。快照不是外置备份，boot/ESP 和固件 NVRAM 的覆盖范围不同。

Secure Boot 当前未启用；sbctl、UKI 与 NVIDIA 模块签名仅有文档，未注册固件密钥或做硬件验证。
Calamares 仍是构建时本地未签名包的明确例外，固定 SHA-256 不等于官方 PGP 签名。
运行时 pacman.conf 不含本地例外仓库，详见 [SECURITY.md](SECURITY.md)。

无遥测声明针对 BasaltOS 自身；Steam 等第三方行为、可选云拼音、KDE 用户配置覆盖等边界见
[PRIVACY.md](PRIVACY.md)。未进行全量第三方应用网络抓包或模拟有更新时的通知弹窗。

M4 的 90 个受保护 profile 文件/链接、全部原有包清单保留检查通过，
M3 的 28 项安装/语言/引导保护检查也通过。保留既有品牌文案，安装器仍显示 M3，
PRETTY_NAME 仍为 BasaltOS M4；M5 由 Git 标签和本页最终 ISO 散列标识。
M1–M4 ISO 散列与历史记录一致。BIOS 兼容沿用 M3 已验证配置，本次 M5 只重测 UEFI。

验收后 QEMU 与 BasaltOS 专属 VirtualBox 构建机均正常关机；本项目临时文件传输服务停止。
只完成 M5，没有继续后续里程碑。
