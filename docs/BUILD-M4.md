# M4 构建与 QEMU 启动

继续 `m3-installer` 仓库，游戏配置由 `scripts/configure-m4.py` 生成。
core、extra、multilib 均直接指向清华 Arch 镜像。
`scripts/check-m4-baseline.py` 校验 28 个 M3 保护文件/链接，包括语言、时区、
hostname、启动菜单、Calamares 分区/挂载配置和加密/GRUB/Snapper 目标配置脚本。

## 构建机与工作盘

沿用 `BasaltOS-M1-builder`。原 40 GiB 构建系统分区保留，M4 另用项目内
`E:\BasaltOS\work\vms\BasaltOS-M1-builder\m4-work.vdi`，虚拟容量 64 GiB。
该盘挂接 SATA 端口 2，在构建机中是 `/dev/sdb`，ext4 标签为 `BASALT_M4_WORK`。

仅当重新搭建、且该文件尚不存在时，在构建机正常关闭后创建并挂接：

```powershell
$env:VBOX_USER_HOME = $null
$vbox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
& $vbox createmedium disk --filename E:\BasaltOS\work\vms\BasaltOS-M1-builder\m4-work.vdi --size 65536 --format VDI
& $vbox storageattach BasaltOS-M1-builder --storagectl SATA --port 2 --device 0 --type hdd --medium E:\BasaltOS\work\vms\BasaltOS-M1-builder\m4-work.vdi
& $vbox startvm BasaltOS-M1-builder --type headless
```

新盘首次初始化时，先在构建机 `lsblk -o NAME,SIZE,SERIAL,FSTYPE` 核实新盘。
`scripts/prepare-m4-builder-disk.sh /dev/sdb <实际序列号> --initialize-empty-m4-work-disk`
只接受 VirtualBox 内 64 GiB、匹配序列号、无分区、无签名且未挂载的空盘。
已初始化的工作盘不能再次运行该命令，直接挂载即可。

本次已初始化盘 UUID 为 `4c82efc1-aaaa-4fa8-a8b3-7f640e25ed95`；
VirtualBox 序列号为 `VB8fb0231d-01ef8493`。重新创建的虚拟盘会有不同序列号。

## 构建

Windows PowerShell：

```powershell
Set-Location E:\BasaltOS
python scripts/check-m4-baseline.py
tar -cf work/m4-source.tar .gitattributes .gitignore profile scripts packaging docs README.md
python scripts/transfer-server.py
```

在构建机官方 Arch Live root shell（现有 `/dev/sda1` 内是构建系统）：

```bash
curl -fsS http://10.0.2.2:8181/scripts/build-m4-vm.sh -o /tmp/build-m4-vm.sh
bash /tmp/build-m4-vm.sh
```

脚本挂载现有分区与 M4 工作盘，解压新的源码快照，校验保护文件和 shell 语法，
更新构建工具并检查 Calamares schemas，复用 M3 的自建 Calamares 包。
实际构建调用：

```bash
arch-chroot /mnt env BASALT_MILESTONE=m4 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/m4-native/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/work/m4-native/out \
  BASALT_LOCAL_REPO=/root/BasaltOS/work/calamares-package \
  bash "$guest_source/scripts/build.sh"
```

`guest_source` 是脚本打印的源快照路径。
构建后检查大小大于 500 MB、小于 **8,000,000,000 字节**，实读 ISO9660 卷标 `basaltos`，
生成 SHA-256 并将产物与日志回传到 `E:\BasaltOS\out\m4\`。
Calamares 包来源与构建方法继续见 [BUILD-M3.md](BUILD-M3.md)。

## QEMU

```powershell
& E:\BasaltOS\scripts\start-m4-qemu.ps1 -Accelerator whpx
```

默认 UEFI、16 GiB RAM、4 vCPU、virtio 显卡/网卡，QMP 仅绑定 `127.0.0.1:4454`。
使用 Windows 的 `-accel whpx`；需要回退时传 `-Accelerator tcg`。
脚本只启动 M4 Live ISO，不附加硬盘或宿主物理磁盘。
`-Display none` 用于后台截图，默认 SDL 显示可交互窗口。
普通 Live 用户为 **gamer / basaltos**。

本机正式软件渲染叠加层验收使用 `gamemoderun mangohud --dlsym glxgears`。
Vulkan 路径的 HUD 计数异常及虚拟硬件限制见结果文档；Steam 首次启动仍需下载官方客户端更新。

```powershell
python scripts/qemu-console.py snapshot --port 4454 --filename E:/BasaltOS/docs/m4-steam.png
python scripts/qemu-console.py snapshot --port 4454 --filename E:/BasaltOS/docs/m4-mangohud.png
python scripts/qemu-console.py snapshot --port 4454 --filename E:/BasaltOS/docs/m4-gamemode.png
```

操作方法见 [GAMING.md](GAMING.md)，最终产物和实测边界见 [M4-RESULTS.md](M4-RESULTS.md)。
