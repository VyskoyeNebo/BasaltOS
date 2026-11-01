# BasaltOS M1 构建与启动

## 目标与目录

只构建 x86_64 命令行 Live ISO，不包含图形桌面或输入法。
配置基于官方 archiso 92-1 的 releng；保留 BIOS/SYSLINUX、UEFI/systemd-boot。

```text
E:\BasaltOS\
  profile\       archiso 配置与 Live 系统覆盖文件
  scripts\       环境准备、构建、QEMU 验收脚本
  docs\          文档与验收截图
  work\          下载、虚拟机、Linux 构建临时文件（Git 忽略）
  out\           ISO、校验值与完整日志（Git 忽略）
```

所有 pacman 仓库均使用：

```text
https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
```

不启用第三方仓库，不关闭软件包签名校验。默认 root 自动登录；hostname 为
`basaltos`，ISO 卷标为 `basaltos`，LANG 为 `zh_CN.UTF-8`，时区为
`Asia/Shanghai`，keymap 为 `us`。
以太网使用 systemd-networkd DHCP，DNS 使用 systemd-resolved；iwd 默认启用。
保留 dhcpcd，但不默认启用，避免重复管理网卡。

## 方式一：Docker Desktop 的特权 Linux 容器

先确认 Docker Desktop 已启用 Linux 容器并能连接引擎。本次机器的 Docker
启动故障见 [ENV-NOTES.md](ENV-NOTES.md)，实际构建改走方式二。

宿主 PowerShell，在 `E:\BasaltOS` 执行。若已经有官方 `archlinux:latest`
镜像，使用本地镜像，避免隐式从 Docker Hub 下载：

```powershell
Set-Location E:\BasaltOS
docker version
docker image inspect archlinux:latest
docker volume create basaltos-m1-linux-work
docker run --pull=never --rm --privileged --name basaltos-m1-builder `
  --mount 'type=bind,source=E:\BasaltOS,target=/project' `
  --mount 'type=volume,source=basaltos-m1-linux-work,target=/build' `
  -e BASALT_BUILD_ROOT=/build -it archlinux:latest bash
```

如果本地没有官方 Docker 镜像，为满足“下载均从清华镜像”的要求，可以用
清华提供的**官方 Arch bootstrap rootfs**生成本地镜像。它不是 Docker Hub
官方 `archlinux` 镜像；后续 archiso 构建命令相同。宿主需要 Python 3.14+：

```powershell
New-Item -ItemType Directory -Force work\downloads | Out-Null
curl.exe -fL --retry 3 -o work/downloads/archlinux-bootstrap-x86_64.tar.zst `
  https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/latest/archlinux-bootstrap-x86_64.tar.zst
curl.exe -fL -o work/downloads/sha256sums.txt `
  https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/latest/sha256sums.txt
Get-FileHash work/downloads/archlinux-bootstrap-x86_64.tar.zst -Algorithm SHA256
Get-Content work/downloads/sha256sums.txt
# 对照对应文件的 SHA-256，一致后继续。
python scripts/make-bootstrap-image.py `
  work/downloads/archlinux-bootstrap-x86_64.tar.zst work/downloads/archlinux-rootfs.tar
docker import work/downloads/archlinux-rootfs.tar basaltos-archlinux-tuna:local
docker volume create basaltos-m1-linux-work
docker run --pull=never --rm --privileged --name basaltos-m1-builder `
  --mount 'type=bind,source=E:\BasaltOS,target=/project' `
  --mount 'type=volume,source=basaltos-m1-linux-work,target=/build' `
  -e BASALT_BUILD_ROOT=/build -it basaltos-archlinux-tuna:local bash
```

以下命令全部在容器内以 root 执行：

```bash
printf '%s\n' 'Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
pacman-key --init
pacman-key --populate archlinux
bash /project/scripts/setup-builder.sh

# 检查 loop/mount 能力；临时文件位于 Linux volume。
mkdir -p /build/loop-test
truncate -s 32M /build/loop-test.img
mkfs.ext4 -F /build/loop-test.img
mount -o loop /build/loop-test.img /build/loop-test
umount /build/loop-test

BASALT_BUILD_ROOT=/build bash /project/scripts/build.sh
```

如果 loop 分配或挂载失败，保存真实报错到 `docs/ENV-NOTES.md`，改用方式二。
不要通过关闭签名校验或把 archiso 工作目录放在 Windows NTFS 上规避问题。

## 方式二：VirtualBox 中安装 Arch Linux

给独立构建机分配约 8 vCPU、16 GiB 内存、40 GiB 磁盘和 NAT 网卡。
Windows 上的配置、磁盘和下载放在项目 `work/`。官方安装介质下载命令：

```powershell
Set-Location E:\BasaltOS
New-Item -ItemType Directory -Force work\downloads,work\vbox-config,out | Out-Null
curl.exe -fL --retry 3 -o work/downloads/archlinux-x86_64.iso `
  https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/latest/archlinux-x86_64.iso
curl.exe -fL -o work/downloads/sha256sums.txt `
  https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/latest/sha256sums.txt
Get-FileHash work/downloads/archlinux-x86_64.iso -Algorithm SHA256
Get-Content work/downloads/sha256sums.txt
# 校验一致后创建虚拟机。以下创建命令只运行一次。
$env:VBOX_USER_HOME = 'E:\BasaltOS\work\vbox-config'
$vbox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
& $vbox createvm --name BasaltOS-M1-builder --ostype ArchLinux_64 `
  --basefolder E:\BasaltOS\work\vms --register
& $vbox modifyvm BasaltOS-M1-builder --memory 16384 --cpus 8 `
  --graphicscontroller vmsvga --vram 32 --nic1 nat `
  --uart1 0x3f8 4 --uartmode1 file E:\BasaltOS\work\builder-serial.log
& $vbox createmedium disk `
  --filename E:\BasaltOS\work\vms\BasaltOS-M1-builder\build.vdi --size 40960 --format VDI
& $vbox storagectl BasaltOS-M1-builder --name SATA --add sata --controller IntelAhci
& $vbox storageattach BasaltOS-M1-builder --storagectl SATA --port 0 --device 0 `
  --type hdd --medium E:\BasaltOS\work\vms\BasaltOS-M1-builder\build.vdi
& $vbox storageattach BasaltOS-M1-builder --storagectl SATA --port 1 --device 0 `
  --type dvddrive --medium E:\BasaltOS\work\downloads\archlinux-x86_64.iso
& $vbox modifyvm BasaltOS-M1-builder --boot1 dvd --boot2 disk --boot3 none --boot4 none
& $vbox startvm BasaltOS-M1-builder --type headless
```

在宿主另一个 PowerShell 中打包并启动本地传输服务：

```powershell
Set-Location E:\BasaltOS
tar -cf work/source.tar .gitattributes .gitignore profile scripts docs README.md
python scripts/transfer-server.py
```

Arch ISO 进入 root shell 后，在**专用构建虚拟机内**运行下面的命令。
安装脚本会格式化新建的空白 40 GiB `/dev/sda`，安装 Arch、内核和 GRUB；
脚本检查 VirtualBox 标识、磁盘容量及空白状态，已有文件系统时拒绝执行。
此脚本用于首次安装，不可用于重复构建：

```bash
curl -fsS http://10.0.2.2:8181/scripts/vm-install-build.sh -o /tmp/basaltos-build.sh
bash /tmp/basaltos-build.sh
```

其关键构建命令为：

```bash
# 安装时通过 pacstrap 将 archiso 等依赖安装到专用磁盘上的 Arch 系统。
# 在 Live 环境中，已经安装的系统挂载于 /mnt。
arch-chroot /mnt bash /root/BasaltOS/scripts/setup-builder.sh
arch-chroot /mnt bash /root/BasaltOS/scripts/build.sh

# 若已启动安装好的 Arch 系统，直接运行：
cd /root/BasaltOS
bash scripts/setup-builder.sh
bash scripts/build.sh
```

`build.sh` 在 Linux ext4 上创建新的工作目录、恢复 profile 链接，然后执行：

```bash
mkarchiso -v -w "$run_dir/work" -o /root/BasaltOS/out "$run_dir/profile"
```

首次安装脚本将产物通过本地服务回传到宿主 `E:\BasaltOS\out\`。
重复构建后，在虚拟机中手动回传：

```bash
for artifact in /root/BasaltOS/out/*; do
  curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/$(basename "$artifact")"
done
```

## QEMU 启动与验收

Windows PowerShell，已安装 QEMU 且启用 Windows Hypervisor Platform 后：

```powershell
Set-Location E:\BasaltOS
$iso = (Get-ChildItem .\out\basaltos-*.iso | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
qemu-system-x86_64 -accel whpx -m 2048 -smp 2 -boot d -cdrom "$iso" `
  -netdev user,id=net0 -device virtio-net-pci,netdev=net0
```

Linux，有 KVM 权限时：

```bash
qemu-system-x86_64 -enable-kvm -cpu host -m 2048 -smp 2 -boot d \
  -cdrom out/basaltos-2026.11.01-x86_64.iso \
  -netdev user,id=net0 -device virtio-net-pci,netdev=net0
```

以上均从 ISO 的 BIOS 引导路径进入 root shell。UEFI 可加对应 QEMU/OVMF 的
pflash 固件参数；默认命令不启用 Secure Boot。
无硬件加速时可把加速参数换为 `-accel tcg -cpu max`，启动较慢。

进入 Live shell 后执行：

```bash
hostname                 # basaltos
id -u                    # 0
ip a                     # 有非 loopback 的 IPv4 地址
ping -c 3 mirrors.tuna.tsinghua.edu.cn
cat /etc/locale.conf     # LANG=zh_CN.UTF-8
locale -a                # 包含 zh_CN.utf8
readlink /etc/localtime  # /usr/share/zoneinfo/Asia/Shanghai
cat /etc/vconsole.conf   # KEYMAP=us
```

本项目的自动验收使用 QEMU TCG、真实串口交互和 QMP VGA 屏幕截图：

```bash
# 在 Arch 构建虚拟机内运行；宿主传输服务须仍在运行。
cd /root/BasaltOS
bash scripts/verify-qemu.sh
```

输出回传到 `out/m1-qemu.png`、`out/m1-qemu-serial.txt`、
`out/m1-qemu-result.json`。宿主保存最终证据：

```powershell
Copy-Item out\m1-qemu.png docs\m1-qemu.png
Copy-Item out\m1-qemu-serial.txt docs\m1-qemu-serial.txt
Copy-Item out\m1-qemu-result.json docs\m1-qemu-result.json
```

ISO 路径格式：`E:\BasaltOS\out\basaltos-YYYY.MM.DD-x86_64.iso`。
同目录保存 `.iso.sha256`、`build.log` 和 `archiso-version.txt`。
验收结果以实际截图、串口日志及 `docs/M1-RESULTS.md` 为准。
