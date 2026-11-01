# M3：Calamares、加密安装与快照

在 M2 仓库继续构建，输出目录为 `out/m3/`。M1、M2 ISO 保留。
桌面、Fcitx5、中文 locale、时区、hostname 和清华镜像配置沿用 M2。

## 构建安装器本地包

Arch 官方仓库未提供 Calamares。本项目使用上游 Calamares 3.4.3 的 orig 源码，
从清华 Debian 镜像取得，在 Arch 构建机内通过本仓库 PKGBUILD 编译为 Arch 包。
不使用 Debian 二进制包；Qt、Python、KPMCore 等运行库由 Arch 清华镜像提供。

- 源码：`https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/c/calamares/calamares_3.4.3.orig.tar.xz`
- SHA-256：`b62832265be9e1b80ab4a0851f28cae28ef6808ae6c4969c5ac0369f748f0c29`
- 哈希对应同目录 `calamares_3.4.3-1.dsc` 的 `Checksums-Sha256`。
- 上游：[Calamares Codeberg](https://codeberg.org/Calamares/calamares)。

构建时使用 Arch 的 Boost.Python，避免旧 bundled pybind11 与 Python 3.14 的兼容问题。
本地生成的包进入仅供 mkarchiso 构建使用的 `basaltos-local` 仓库；
已安装系统的 pacman 配置仍为原先的 Arch 清华源。

## VirtualBox 构建

继续使用 `BasaltOS-M1-builder` 与现有磁盘。构建机从原官方 Arch ISO 启动，
脚本挂载现有 `/dev/sda1`，不重新分区或格式化构建磁盘。

Windows PowerShell：

```powershell
Set-Location E:\BasaltOS
$env:VBOX_USER_HOME = $null
& 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe' startvm BasaltOS-M1-builder --type headless
tar -cf work/m3-source.tar .gitattributes .gitignore profile scripts packaging docs README.md
python scripts/transfer-server.py
```

在构建机 Arch Live root shell：

```bash
curl -fsS http://10.0.2.2:8181/scripts/build-m3-vm.sh -o /tmp/build-m3-vm.sh
bash /tmp/build-m3-vm.sh
```

脚本解压新源码快照；若尚无本地 Calamares 包，则执行 `scripts/build-calamares.sh`。
它从清华安装依赖，以非 root 用户运行 `makepkg`，使用 `repo-add` 建立本地仓库。
源码配置已在仓库内；修改生成器后可先运行 `python scripts/configure-m3.py`。

构建脚本实际调用：

```bash
arch-chroot /mnt env \
  BASALT_MILESTONE=m3 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/out/m3 \
  BASALT_LOCAL_REPO=/root/BasaltOS/work/calamares-package \
  bash "$guest_source/scripts/build.sh"
```

`$guest_source` 是脚本打印的源码快照路径。构建使用 ext4 临时目录与官方 mkarchiso。
脚本检查 ISO 大于 500 MB、小于 4,000,000,000 字节、卷标为 `basaltos`，生成 SHA-256，
回传 ISO、校验文件、archiso 版本和日志至宿主 `E:\BasaltOS\out\m3\`。

## 安装布局

Calamares 采用离线解包 Live squashfs 的方式安装同一套系统与内核。
支持可自定义的普通用户、密码和 hostname，SDDM 不自动登录。

自动擦除布局：GPT，BIOS boot 分区、512 MiB ESP、1536 MiB ext4 `/boot`，
其余空间为 btrfs；勾选加密后 btrfs 位于 LUKS2 容器内。
ESP 与 `/boot` 保留明文，系统文件及 `/home` 加密。没有配置休眠或 swap 文件。
普通安装也可不勾选加密。

btrfs 子卷包括 `@`、`@home`、`@cache`、`@log`；挂载启用 zstd 压缩。
根目录与 home 分别配置 Snapper，生成安装初始快照并启用 timeline/cleanup timers。
snap-pac 包自带 pacman 事务 hook，管理根目录软件包事务快照。

`/usr/local/lib/basaltos/finalize-installed.sh` 在目标 chroot 内执行：
配置 sd-encrypt、crypttab、内核与 initramfs、GRUB 参数、用户桌面默认值和 Snapper，
清理 Live 自动登录配置。Calamares 随后通过 bootloader 模块安装 GRUB。

## Windows QEMU

沿用 M2 项目内便携 QEMU。创建**新的空白测试盘**并启动 Live：

```powershell
.\scripts\start-m3-qemu.ps1 -Boot live -Firmware bios -Accelerator whpx -CreateDisk
```

测试盘默认 `E:\BasaltOS\work\m3\installed.qcow2`，虚拟容量 48 GiB，
序列号 `BASALTOS_M3_TARGET`。如果文件已存在，`-CreateDisk` 会拒绝覆盖。
需要另一块测试盘时可指定项目 `work/m3/` 内的新 `.qcow2` 文件路径。
默认 8 GiB RAM、4 vCPU、virtio 显卡和网卡，QMP 仅绑定 `127.0.0.1:4453`。
加 `-Display none` 可用 QMP 后台验收，默认 SDL 显示交互窗口。

Live 登录账号为 `root`，密码 `basaltos`。双击桌面“安装 BasaltOS”，
在分区页选择目标空盘、btrfs 与加密选项，然后创建自己的用户并确认安装。
安装完成后关机，**不挂载 ISO**，从同一测试盘启动：

```powershell
.\scripts\start-m3-qemu.ps1 -Boot disk -Firmware bios -Accelerator whpx
# UEFI 使用同一测试盘，独立项目内 NVRAM 文件：
.\scripts\start-m3-qemu.ps1 -Boot disk -Firmware uefi -Accelerator whpx
```

同一测试盘不能被两个 QEMU 进程同时写入。WHPX 不可用时可指定 `-Accelerator tcg`。
UEFI 配置使用 QEMU 自带 EDK2，不包含 Secure Boot 签名流程。

截图示例：

```powershell
python scripts/qemu-console.py snapshot --port 4453 --filename E:/BasaltOS/docs/m3-calamares.png
python scripts/qemu-console.py snapshot --port 4453 --filename E:/BasaltOS/docs/m3-partition.png
python scripts/qemu-console.py snapshot --port 4453 --filename E:/BasaltOS/docs/m3-installed.png
```

## 脚本安装备用验收

若图形自动化成本过高，允许在新建空盘的 M3 Live 中执行：

```bash
curl -fsS http://10.0.2.2:8181/scripts/install-m3-test.sh -o /tmp/install-m3-test.sh
bash /tmp/install-m3-test.sh --erase-basaltos-m3-test-disk
```

脚本只接受 `/dev/vda`、指定序列号、48 GiB 且无已有签名的专用测试盘，
交互读取新用户名、密码与 LUKS 密码，使用与 Calamares 相同的布局、squashfs 和目标配置脚本，
安装 BIOS 与 UEFI GRUB。它不是通用物理机安装脚本。
如实际采用此路线，必须在结果文档区分“Calamares 界面验证”和“脚本安装验证”。

最终实际通过项目、产物校验值和限制见 `M3-RESULTS.md`。
