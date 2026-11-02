# M6 发版基础设施验收结果

日期：2026-11-02。M6 本地签名、pacman 仓库、已安装系统验收与发布附件准备完成。
没有 Git remote 或真实 GitHub 仓库地址，未执行 push、上传 Release 或公开部署。
只操作 `E:\BasaltOS` 与其专属虚拟磁盘，没有修改飞牛 OS 或其他项目。

## ISO 与发布附件

| 项目 | 结果 |
| --- | --- |
| ISO | `E:\BasaltOS\out\m6\basaltos-2026.11.02-x86_64.iso` |
| 版本化附件 ISO | `E:\BasaltOS\out\releases\0.1.0-m6\basaltos-0.1.0-m6-x86_64.iso` |
| 大小 | **2,353,299,456 bytes**，约 2.35 GB / 2.192 GiB |
| 两份 ISO 的 SHA-256 | `0fd12156f204a6b6535c19aca1ae0f229e8e8b02579772602e68530034a27281` |
| 卷标 | `basaltos`，构建端与导出后均已检查 |
| archiso | `92-1` |
| 本地仓库 | `E:\BasaltOS\repo\x86_64\`，不纳入 Git |
| 公网仓库占位 | `https://OWNER.github.io/REPOSITORY/x86_64`，尚未部署 |
| 验收 URL | `http://10.0.2.2:8181/repo/x86_64`，仅专属 QEMU/NAT 本地测试 |
| Git 标签 | `m6-release`、版本标签 `0.1.0-m6` |
| Pages 入口 | 本地 `gh-pages` 分支，手动 Actions 发布流程，不提交仓库二进制 |

发布附件位于 `out/releases/0.1.0-m6/`，包括签名校验清单、仓库归档、公钥、
发行说明模板和上传命令。仓库归档 **4,790,744 bytes**，SHA-256：
`d6d39f33f8c8bed90f1e8fb736711557fde9ba25a6decc56469a94846101eabf`。
ISO 和仓库文件不提交 Git，正式上传步骤见 [RELEASE.md](RELEASE.md)。

GitHub Release 单附件必须小于 2 GiB，所以本次完整 ISO 只保留本地，
脚本自动生成可上传的三个分片，并将它们纳入同一份 GPG 签名 SHA256SUMS：

| 分片后缀 | bytes |
| --- | ---: |
| `.iso.part00` | 1,073,741,824 |
| `.iso.part01` | 1,073,741,824 |
| `.iso.part02` | 205,815,808 |

Windows 上实际运行 `scripts/join-iso.py` 重组至 `work/m6/reassembled.iso`，
逐片及完整 ISO 校验通过，散列与上表相同。
首次生成的未分片上传说明已由分片版本替换，旧小附件元数据保留在
`out/releases/0.1.0-m6-initial/`，不要作为最终上传说明使用。

## GPG 与签名仓库

- UID：`BasaltOS TEST Release <basaltos-release@basaltos.local>`，仅测试身份。
- 主钥：`29DAFB5537B451968276DA003941AA503494B8B1`，Ed25519 认证用途。
- 签名子钥：`9D912C7E6F4DF3D23A8B14BB3C1B8918CCCAA8D5`，Ed25519 签名用途。
- 创建于 2026-11-02，主/子钥到期日 2027-05-01。
- 公钥：[packaging/basaltos-key.asc](../packaging/basaltos-key.asc)，ISO 内为 `/usr/share/basaltos/keys/`。

测试私钥只留在专属构建机 `/root/BasaltOS/work/m6-private/gnupg`，
目录权限 700，随机口令文件权限 600，不入 Git、源码传输 tar、软件包、ISO 或 Release 附件。
检查最终构建根目录，没有私钥文件或口令文件；Git 跟踪范围排除 work/out/repo 二进制。
正式私钥离线保存流程、撤销和轮换边界见 [RELEASE.md](RELEASE.md)。

`repo-add --sign` 生成数据库和文件索引及其签名，普通文件形式的别名齐全。
仓库有自建 `basaltos-release-0.1.0_m6-1-any.pkg.tar.zst` 和补签的
`calamares-3.4.3-1-x86_64.pkg.tar.zst`，每个包均有独立 `.sig`。
Calamares 二进制与 M3/M5 固定 SHA-256 相同，只增加外部签名。
M6 构建的本地仓库也使用 Required，未使用此前 M5 构建时的 Optional TrustAll 例外。

构建与验签日志：[m6-repo-build.txt](m6-repo-build.txt)。
Pages 本地验证日志：[m6-pages-verify.txt](m6-pages-verify.txt)。
后者的临时公钥环没有个人 Web of Trust，因此 GPG 会显示 `[unknown]` 身份认证提示；
验证程序只导入一个与源码固定指纹匹配的公钥，签名均有效，未关闭签名验证。
这不等同于第三方认证了测试邮箱的真实组织身份。

## QEMU 已安装系统验收

QEMU 11.1.3、Windows WHPX，UEFI、16 GiB RAM、4 vCPU、virtio/NAT。
新建 `work/m6/installed.qcow2` 48 GiB，唯一目标序列号 `BASALTOS_M6_TARGET`。
从最终 M6 ISO 用原有 Calamares 完成 LUKS2 + btrfs 图形安装，正常关闭 Live、
移除 ISO 后从硬盘启动，解锁并登录 KDE。没有复用或修改 M5 测试盘。

测试用户名 `basalt`，测试登录/root/LUKS 口令 `Basalt-M6-2026`，
仅属于这个可丢弃测试盘，不是 ISO 安装的固定默认密码。
Live 账号仍为 `gamer / basaltos`。

| 验收 | 实际结果 |
| --- | --- |
| A：仓库生成/签名 | 两个包、basaltos.db 与 basaltos.files 的签名生成并验证成功，见签名日志 |
| 公钥自动初始化 | 安装后首次启动服务 enabled、active(exited)，21:03:31 成功完成；公钥为 full 信任 |
| B：pacman -Syu | 启用本地 `[basaltos]` 后，`pacman -Syu --noconfirm basaltos-release` 完成真实下载、keyring/integrity 检查与安装 |
| 严格签名 | PackageRequired / PackageTrustedOnly / DatabaseRequired / DatabaseTrustedOnly；独立数据库验签为 Good signature [full] |
| C：check-only | 正确查询 core、extra、multilib、basaltos；0 项更新；真实 pacman/keyring 文件散列和 root/home 快照列表前后相同 |
| 篡改拒绝 | 临时命名空间指向被篡改但保留原签名的数据库，按 invalid PGP signature 失败；主系统仓库配置没有改变 |
| M5 dry-run | 真实创建 root 2/3 号配对快照及 boot/ESP 备份；不安装包 |
| snap-pac | 演示包安装产生 root 4/5 号 pre/post，原有钩子正常 |
| 正常更新路径 | `basaltos-update` 先生成 root pre=6 和 boot 备份，再执行包含四个仓库的 pacman -Syu，成功后 post=7，Result: updated |
| M1/M3 配置 | hostname basaltos、zh_CN.UTF-8、Asia/Shanghai、us；LUKS、btrfs 子卷与独立 boot/ESP 保留 |
| M5 网络安全 | nftables/NetworkManager active；input drop/output accept；仅回环 DNS 监听，无 5353/5355 |

正常更新那次没有新包可升级；实际新增包仅为演示包，不声称已验证跨版本内核升级。
对应正常事务 ID：`20261102T130921Z-b67d014c`，boot 备份 SHA-256：
`159a45fbc20fcb80b0ddca33f5782233a481c818e74907a2a71b8960f719d19c`。

真实 QMP 截图，均已查看：

- [m6-repo.png](m6-repo.png)：四个仓库同步、严格验签属性、已安装演示包与可信数据库签名。
- [m6-check-only.png](m6-check-only.png)：查询成功且不安装包、不创建快照，保留既有 1–5 号快照列表。

完整安装后验证日志：[m6-installed.txt](m6-installed.txt)。
正常更新路径日志：[m6-normal-update.txt](m6-normal-update.txt)。
Calamares 现场日志在 `work/m6/calamares-session.log`，大运行文件不提交 Git。

启动命令：

```powershell
Set-Location E:\BasaltOS
.\scripts\start-m6-qemu.ps1 -Boot live -Firmware uefi -Accelerator whpx
# 启动已安装测试盘：
.\scripts\start-m6-qemu.ps1 -Boot disk -Firmware uefi -Accelerator whpx
```

验收后已关闭测试盘上的临时 HTTP 仓库，恢复只启用官方仓库；演示包仍已安装。
避免临时传输服务停止后，测试 URL 阻断以后更新。真实 HTTPS 地址就绪后通过
`basaltos-repo enable URL` 明确启用。ISO 自带模板始终默认关闭。

## 发布流程验证与边界

本地执行与 Pages 工作流相同的 `prepare-pages.py`，检查固定公钥、签名 SHA256SUMS、
仓库归档散列、每个包/数据库签名及别名一致性，确认归档只有普通文件/目录。
生成的 Pages 站点不含 ISO。工作流仅从 gh-pages 分支手动触发，私钥不进入 GitHub。
实际 GitHub Release/Pages 部署与 DNS/TLS 尚未验收，仓库地址是占位符。

首次 bootstrap 将脚本放在 chroot 的临时目录，因 arch-chroot 的 `/tmp` 挂载隔离不可见，
改为项目 work 中的真实路径后成功。首次发布说明未考虑 GitHub 的 2 GiB 单附件限制，
已经加入分片、签名清单与实际重组测试；最终上传命令只包含分片。
这些修正没有重建或改变已经验收的 ISO payload。

这是测试签名身份；口令和私钥同机保存只适用于实验，正式离线密钥管理尚需部署与演练。
没有执行密钥泄漏/轮换、跨版本内核升级、离线回滚或 Secure Boot 实机验收。
恢复仍按 [SECURITY.md](SECURITY.md)，不能直接用 snapper rollback 切换固定 `@` 根。

Arch 滚动源未固定快照，本流程提供完整构建步骤，未验证逐字节可重复构建。
构建工作盘收尾时剩余约 3.9 GB，下一次全新构建前需整理本项目旧工作目录或扩容。
本轮 BIOS 沿用原配置，仅重新验收 UEFI。安装器 M3、PRETTY_NAME M4 等既有品牌文字继续保留。

107 个 M5 受保护 profile 文件/链接校验通过，M5 正常更新与恢复路径保持原样，
没有修改桌面、输入法、游戏、加密、Snapper、GRUB 或防火墙配置。
验收后 QEMU、专属构建机及临时传输服务均停止。停在 M6，不继续后续里程碑。
