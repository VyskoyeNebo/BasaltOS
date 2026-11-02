# M5 构建与 QEMU 验收

继续 M4 仓库和独立的 BasaltOS-M1-builder 虚拟机。不要切换飞牛 OS 的磁盘，
不要重新格式化已有 `BASALT_M4_WORK` 工作盘。

## Linux/VirtualBox 构建机内

源码应在 Linux 原生 ext4/btrfs 工作目录；Windows/共享目录仅传输源码和最终产物。

```bash
cd /path/to/BasaltOS
python scripts/check-m5-baseline.py
sudo bash scripts/setup-builder.sh
# 首次才需要编译 M3 安装器；已有固定校验值的本地仓库可复用：
sudo bash scripts/build-calamares.sh
sudo env BASALT_MILESTONE=m5 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/m4-native/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/work/m4-native/out-m5 \
  BASALT_LOCAL_REPO=/root/BasaltOS/work/calamares-package \
  bash scripts/build.sh
```

M5 固定检查本次已审核的 Calamares 主包 SHA-256。自行重新编译时，时间戳、工具链等可能
改变包散列；应先核对源码和编译结果，再显式更新 `scripts/build.sh` 中的固定值，
不能通过取消签名检查或跳过散列检查来处理。本次使用已有的 M3/M4 构建缓存。

本次沿用 Live 构建机挂载旧系统 `/dev/sda1` 到 `/mnt`，通过 arch-chroot 调用上述脚本。
64 GiB 原生工作盘按卷标挂载在 `/mnt/root/BasaltOS/work/m4-native`。
`scripts/build-m5-vm.sh` 完整记录本机传输、挂载、检查、构建和回传流程，
不格式化任何盘，源码每次放在新的 `m5-source.XXXXXXXX` 目录。

本机 PowerShell 传输与启动示例：

```powershell
Set-Location E:\BasaltOS
# 保持本项目传输服务运行（另一个终端）：
python scripts/transfer-server.py
tar -cf work/m5-source.tar .gitattributes .gitignore profile scripts packaging docs README.md
# 在 BasaltOS 构建机 Live tty1 中执行：
# curl -fsS http://10.0.2.2:8181/scripts/build-m5-vm.sh -o /tmp/build-m5-vm.sh
# bash /tmp/build-m5-vm.sh
```

脚本先重建 Windows checkout 中的符号链接，检查 M4 的 90 个受保护配置，
Calamares 主包固定 SHA-256，再执行 mkarchiso，检查卷标 `basaltos`、
ISO >500 MB 且 <8,000,000,000 bytes，生成 `.sha256`。
最终导出到 `E:\BasaltOS\out\m5\`。旧 M1–M4 产物不覆盖。
本机环境的权限、loop 限制和 VirtualBox 注册隔离问题继续参照 `ENV-NOTES.md`。

## 新测试盘与 QEMU

```powershell
Set-Location E:\BasaltOS
# 创建只属于 M5 的全新 48 GiB qcow2；存在时拒绝覆盖：
.\scripts\start-m5-qemu.ps1 -Boot live -Firmware uefi -Accelerator whpx -CreateDisk
# 在 Live 内用 Calamares 安装到 BASALTOS_M5_TARGET，选择 btrfs + LUKS。
# 正常关机后，移除 ISO 从硬盘启动：
.\scripts\start-m5-qemu.ps1 -Boot disk -Firmware uefi -Accelerator whpx
```

脚本实际使用 Windows `-accel whpx`、16 GiB RAM、4 vCPU、virtio 显卡/磁盘/网卡、
UEFI 独立 vars，磁盘限制在 `E:\BasaltOS\work\m5\`；不用物理磁盘。
Linux 对应可用 `-enable-kvm`，但本次没有 Linux KVM 验收。
若 WHPX 不可用，改 `-Accelerator tcg`，速度显著降低。
`-Display none` 可供 QMP 验收，默认 SDL 适合手动交互。

QMP 监听 `127.0.0.1:4455`。仅为防火墙拒绝入站测试，脚本把主机回环
`127.0.0.1:18085` 转到来宾 18085；不是向外网开放宿主端口。
没有附加 M3、M4、飞牛 OS 的磁盘。

```powershell
python scripts/qemu-console.py --port 4455 snapshot --filename E:/BasaltOS/docs/m5-firewall.png
```

以 `python scripts/qemu-console.py --help` 显示的参数顺序为准。
安装后通过 Konsole 成为 root，下载并执行 `scripts/accept-m5.sh` 可复现实验：

```bash
curl -fsS http://10.0.2.2:8181/scripts/accept-m5.sh -o /tmp/accept-m5.sh
bash /tmp/accept-m5.sh
```

脚本核对磁盘序列号，拒绝在 Live 或其他磁盘运行；不执行真实包更新、不自动回滚。
截图和最终观测值以 [M5-RESULTS.md](M5-RESULTS.md) 为准。
