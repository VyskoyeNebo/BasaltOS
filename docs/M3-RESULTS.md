# M3 验收结果

2026-11-01（Asia/Shanghai）：最终 ISO 已完成完整 Calamares GUI 安装、UEFI 与 BIOS
硬盘启动验收，并在新用户 KDE 会话中完成系统检查。交付标签为 `m3-installer`。

## 产物

- ISO：`E:\BasaltOS\out\m3\basaltos-2026.11.01-x86_64.iso`
- 大小：`1943601152` 字节，即 `1.944 GB / 1.810 GiB / 1853.56 MiB`，低于 4 GB。
- SHA-256：`bfa823faf5ea22bbe77b0e1a93da7801e47043a7a350bf4084c4bb8c476ed24b`
- 校验文件：`out/m3/basaltos-2026.11.01-x86_64.iso.sha256`
- ISO9660 卷标实读：`basaltos`。
- 构建工具：官方 archiso `92-1`；日志：`out/m3/build.log`。
- 最终 profile 源码提交：`dfe6d5f`。

Calamares 不在 Arch 官方仓库，本次使用清华 Debian 镜像中的上游 3.4.3 orig 源码，
通过本仓库 PKGBUILD 在 Arch 构建机内生成 Arch 包，未使用 Debian 二进制包。
源码归档与自建包哈希、完整准备流程见 [BUILD-M3.md](BUILD-M3.md)。
自建主包 SHA-256：`962127440180c43f8b8752174de190c9e29c364178acbe1bd406003580e40f81`。

| 组件 | 最终 ISO 版本 |
| --- | --- |
| Calamares | 3.4.3-1 |
| GRUB | 2:2.16-1 |
| efibootmgr | 18-4 |
| btrfs-progs | 7.3-1 |
| cryptsetup | 2.8.8-1 |
| Snapper | 0.13.2-1 |
| snap-pac | 3.0.1-3 |
| Linux | 7.2.11.arch1-1 |
| plasma-desktop | 6.8.2-1 |
| Fcitx5 | 5.1.23-1 |

## 实际构建

沿用 `BasaltOS-M1-builder`、现有 ext4 构建盘与默认 VirtualBox 管理器。
从官方 Arch Live root shell 执行 `scripts/build-m3-vm.sh`；实际调用为：

```bash
arch-chroot /mnt env \
  BASALT_MILESTONE=m3 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/out/m3 \
  BASALT_LOCAL_REPO=/root/BasaltOS/work/calamares-package \
  bash /root/BasaltOS/work/m3-source.y9o13bRA/scripts/build.sh
```

最终工作目录：`/root/BasaltOS/work/linux-build/m3.Zpqf9kla`。
构建前通过 shell/YAML 检查与同版本 Calamares 的 10 个模块 schema 校验。
上游 partition schema 遗漏的两个布局参数按源码支持范围补充校验，细节见构建文档。

## 正式安装验收方式

**使用最终 ISO 完成完整 Calamares GUI 安装，未采用脚本安装替代，也未手动修复正式安装盘。**
QMP 鼠标与键盘事件操作真实 GUI，完成欢迎、位置、键盘、分区、用户、摘要及安装。
16:19:13 安装器记录 `completion: succeeded`；日志确认执行：

```text
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=BasaltOS --force
grub-install --target=i386-pc --recheck --force /dev/vda
```

原始安装日志保留在 `work/m3/final-calamares.log`。
早期候选盘及其诊断修复不计入正式验收；它们独立存放于 `work/m3/candidate.*`
与 `work/m3/diagnostic-timeout.*`。正式盘为修正版 ISO 再次新建的空盘。

正式测试盘：`E:\BasaltOS\work\m3\installed.qcow2`，虚拟容量 48 GiB，
序列号 `BASALTOS_M3_TARGET`。未附加宿主物理磁盘。

| 分区 | 用途 | 文件系统／加密 |
| --- | --- | --- |
| vda1 | `/boot/efi`，512 MiB | FAT32，明文 |
| vda2 | BIOS boot，8 MiB | GRUB 嵌入区 |
| vda3 | `/boot`，1536 MiB | ext4，明文 |
| vda4 | 其余空间，系统与 home | LUKS2 内的 btrfs |

子卷为 `@`、`@home`、`@log`、`@cache`；Snapper 创建根目录与 home 的快照子卷。
内核使用 `sd-encrypt`，crypttab 与 initramfs 不保存解锁口令，每次启动需要输入口令。

仅此测试盘的验收凭据：用户 **basalt**（显示名 Basalt Test），
登录密码与 LUKS 口令均为 **Basalt-M3-2026**；root 管理密码复用测试用户密码。
这些账号由安装 GUI 创建，不预置在 ISO 内。实际安装可自行设置用户名和密码。
Live 环境仍为 `root / basaltos`。

## 硬盘启动与系统检查

Windows QEMU `11.1.3`，WHPX、q35、4 vCPU、8 GiB RAM、virtio 显卡／网卡／磁盘。
正式安装从 UEFI Live 启动；安装后启动命令均**不挂载 ISO**：

```powershell
Set-Location E:\BasaltOS
.\scripts\start-m3-qemu.ps1 -Boot disk -Firmware uefi -Accelerator whpx
.\scripts\start-m3-qemu.ps1 -Boot disk -Firmware bios -Accelerator whpx
```

两条命令应先后运行，不能同时写入同一磁盘。验收时加 `-Display none`，
默认不加时打开 SDL 窗口。Live 镜像启动与新空盘创建命令见 [BUILD-M3.md](BUILD-M3.md)。

| 检查 | 正式结果 |
| --- | --- |
| 桌面安装图标 | 双击直接打开中文 Calamares |
| 分区页 | 默认 btrfs，可勾选“加密系统”，布局显示 LUKS2 |
| GUI 安装 | 成功完成全部流程，用户可自定义 |
| UEFI 硬盘启动 | 输入 LUKS 口令后进入新用户 SDDM，登录 KDE |
| BIOS 硬盘启动 | 同一安装盘解锁后进入 SDDM，登录 KDE，快照持久保留 |
| hostname | `hostnamectl --static` 为 `basaltos` |
| 加密卷 | vda4 为 `crypto_LUKS`，解锁映射为 btrfs |
| 子卷挂载 | `/` 的 FSROOT 为 `/@`，`/home` 为 `/@home` |
| root Snapper | #1 安装初始快照，#2 pre、#3 post 事务快照 |
| home Snapper | #1 安装初始快照 |
| 自动快照 | snapper-timeline 与 snapper-cleanup timers 均 enabled |
| snap-pac | 实际重装 nano，pre/post hooks 分别生成 #2、#3 |
| KDE / Fcitx5 | 桌面可用，Fcitx5 进程存在，实际输入“中文”成功 |
| IPv4 / HTTPS / ping | enp0s3 为 10.0.2.15/24；清华镜像 HTTP/2 200；ping 3/3 成功 |
| locale / 时区 | zh_CN.UTF-8 / Asia/Shanghai |

完整检查脚本为 `scripts/check-m3-installed.sh`；正式结果日志为
`work/m3/installed-final-uefi.log`，包含 `M3_INSTALLED_CHECKS_PASSED`。
BIOS 复核日志为 `work/m3/installed-final-bios.log`，包含
`M3_BIOS_PERSISTENCE_CHECK_PASSED`；等待参数与桌面目录检查记录在
`work/m3/fixed-boot-check.log`，包含 `M3_DELAYED_UNLOCK_AND_DESKTOP_CHECK_PASSED`。
snap-pac 默认管理 root 事务快照，home 使用独立初始快照及 timeline 策略。

## 截图

均来自最终 ISO 或其正式安装盘的真实 QMP `screendump`，未合成终端画面或后期编辑截图。

- [Live 桌面安装图标](m3-live-desktop.png)
- [Calamares 中文欢迎页](m3-calamares.png)
- [默认 btrfs 布局](m3-partition-btrfs.png)、[已勾选加密](m3-partition.png)
- [用户创建](m3-users.png)、[安装摘要](m3-summary.png)、[安装成功](m3-complete.png)
- [LUKS 解锁提示](m3-unlock.png)、[已安装 SDDM](m3-installed-sddm.png)
- [超过两分钟仍等待解锁](m3-unlock-wait.png)、[启动修复与网络检查](m3-boot-check.png)
- [已安装 KDE](m3-installed-desktop.png)
- [要求的已安装系统主截图](m3-installed.png)
- [BIOS 启动与快照持久性](m3-installed-bios.png)
- [snap-pac 真实事务](m3-snap-pac.png)、[安装后中文输入](m3-ime.png)

## 已知限制与修复记录

- M3 提供自动擦除安装，暂不提供手动分区、保留数据或双系统安装流程。
- ESP 与 `/boot` 未加密，系统和 `/home` 位于 LUKS2 内。Secure Boot 未配置。
- 已修复解锁提示与根设备等待时限不一致的问题：正式新安装盘于 16:22:04 到
  16:24:40 保持等待，随后输入口令正常进入 SDDM。未再触发原来的 90 秒根设备超时。
  使用 `rd.luks.options=timeout=0` 与 `rootflags=subvol=@,x-systemd.device-timeout=0`，
  并用 `crypttab` 的 `x-initrd.attach` 替代已弃用的 `crypttab.initramfs`。
- 已验收加密安装；非加密选项、物理硬件和独立 BIOS Live 安装流程未另行安装验收。
  未配置休眠，也未集成 GRUB 快照选择菜单或验证快照回滚。
- 当前宿主 WHPX 可用，未使用 TCG 回退。偶见 interrupt vector 0／TDX 不支持提示，未阻止正常启动。
- 安装器日志含虚拟盘不提供 SMART、未提供 os-prober 的探测提示；本阶段仅提供空盘自动擦除，
  未启用其他系统检测或双系统安装。上述提示未阻止完整安装。
- 早期候选发现品牌缺少必需的 slideshow 字段，以及 lsblk 的 nodeps 查询无法获取 dm-crypt
  父分区；均已修复后重新构建，正式 GUI 安装通过。修复后的父分区检测使用 sysfs。
- 已修复新用户缺失 Desktop 目录而导致桌面显示整个主目录的问题。
- 主机控制工具在 QEMU 已退出时改为明确返回 QMP 不可用与错误码，避免输出整段 traceback；
  启动脚本也会检查进程是否立即退出，并提供 stderr 日志。

M1/M2 的受保护身份、locale、时区、键盘与清华源文件未改；两份历史 ISO 的 SHA-256
已复核不变。其他项目和其他虚拟机磁盘未改动。构建机与验收机均在收尾时正常关闭。
