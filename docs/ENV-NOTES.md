# M1 构建环境记录

## 2026-11-01，Windows 11，Asia/Shanghai

- 项目目录：`E:\BasaltOS`，Git 仓库位于此目录。
- Docker CLI 29.2.1，Docker Desktop 4.61.0，默认上下文 `desktop-linux`。
- VirtualBox 7.2.20；Ryzen 7 8700G，硬件虚拟化可用。
- Windows PATH 未找到 `qemu-system-x86_64`，因此 QEMU 验收计划在独立 Arch 构建机内进行。

## Docker 路径失败的实际原因

初始 `docker version` 无法连接 `dockerDesktopLinuxEngine` 管道。
启动 Docker Desktop 后，其后端日志于北京时间 2026-11-01 11:00:57 报错：

```text
starting services: initializing Inference manager:
listening on unix://<HOME>\AppData\Local\Docker\run\dockerInference:
remove <HOME>\AppData\Local\Docker\run\dockerInference:
The file cannot be accessed by the system.
(listener: The filename, directory name, or volume label syntax is incorrect.)
```

Docker 在引擎启动前崩溃，未能运行特权容器，也未执行 loop/挂载测试。
这次故障不能归因于 WSL2 loop 设备限制。没有重置 Docker、删除其文件或修改全局配置。

## VirtualBox 备用路径

- 新建 `BasaltOS-M1-builder`，8 vCPU、16 GiB RAM、40 GiB 动态 VDI、NAT 网络。
- `VBOX_USER_HOME=E:\BasaltOS\work\vbox-config`，隔离虚拟机注册信息。
- 虚拟机配置和磁盘：`E:\BasaltOS\work\vms\BasaltOS-M1-builder\`。
- 不操作宿主现有虚拟机。
- 官方 Arch 2026.10.01 ISO 从清华镜像下载；`latest` 在本次下载时指向该版本。
- 安装介质 SHA-256：`684ded26c63240ff4a41e8c25ee84ea6da233f557364821f13d12c2b0a9059a5`，与镜像站校验文件一致。
- 项目传输服务仅监听 `127.0.0.1:8181`，虚拟机通过 NAT 的 `10.0.2.2:8181` 访问。
- 构建系统安装在专用 VDI 的 ext4 分区中；ISO 经本地 HTTP 回传项目 `out/`。
- 当前主机不提供嵌套硬件虚拟化；虚拟机内的 QEMU 使用 TCG 软件模拟。
- 实际验收采用 QEMU 11.1.3、q35、单线程 TCG、qemu64、1 vCPU，
  `-icount shift=auto,sleep=on -rtc clock=vm`；下面记录了选择这些参数的原因。
- Windows 用户直接运行 QEMU 时使用 `-accel whpx`，Linux 有 `/dev/kvm` 时使用 `-enable-kvm`。
- 构建机中的清华域名解析为 `198.18.0.64`（宿主代理网络的虚拟地址）；ping 成功表示当前代理网络路径可达，不代表直接对镜像站公网地址的 ICMP 测量。QEMU 验收同时请求镜像站 HTTPS，核实实际站点访问。

## Windows 文件系统注意事项

Git 对符号链接使用 mode `120000`；Windows checkout 可用普通文件保存链接目标。
`scripts/profile-symlinks.json` 记录所需链接，`stage-profile.py` 只在 Linux 构建副本中恢复。
archiso 的工作目录必须位于 Linux 文件系统，不能直接在 NTFS、DrvFS 或 VirtualBox 共享文件系统上构建 rootfs。
软件包仓库、ISO 内 pacman 配置和镜像列表均固定到清华镜像，保留软件包签名验证。

## 构建过程中的提示

mkinitcpio 提示部分可选硬件固件缺失，包括 `qla1280`、`qed`、`bfa`、
`qla2xxx`、`aic94xx`、`wd719x`、`xhci_pci_renesas`。这是特定硬件的固件提示，
并非构建失败；保留标准 `linux-firmware` 套件，未添加额外的冷门存储控制器固件。
M1 的硬件覆盖以本次 QEMU 实测为准。

另外，`pv` 未安装时 archiso 自动用 `cp` 完成复制；自定义 passwd、DNS 和
pacman 配置使软件包默认文件保存为 `.pacnew`，自定义配置保留。
小写卷标 `basaltos` 触发 xorriso 的 ISO 9660 字符规则提示；按 M1 要求保留小写，
已直接读取 ISO 的 Primary Volume Descriptor 确认卷标为 `basaltos`。

## QEMU 启动兼容性排查

初始 i440FX + TCG + max CPU + 2 vCPU，在内核 IO-APIC 定时器初始化处 panic：

```text
IO-APIC + timer doesn't work!
```

仅改 q35 后仍然出现同类错误。失败串口证据保存在
`docs/m1-qemu-first-failure.txt`、`docs/m1-qemu-q35-failure.txt`。
后续采用单线程 TCG、1 vCPU、基础 qemu64 CPU，并让指令计数时钟与 RTC 使用
同一虚拟时钟。此配置最终通过 VGA 自动登录 root，并完成 DHCP、ping 和 HTTPS 验收。
TCG 下启动明显慢于硬件虚拟化，排查时通过 QMP 定期导出真实 VGA 画面，
避免把正常的启动处理误判为卡死。

早期自动验收额外加入的串口控制台引发 `/dev/ttyS0` 设备等待，随后移除了
该附加配置并重新构建 ISO。最终配置沿用 releng 的 VGA root 自动登录，
通过 QMP 真实虚拟键盘和屏幕截图验收，不依赖串口登录。

排查期间 VirtualBox Guest Control 会话发生超时，构建机经 ACPI 正常关机后重新启动；
磁盘和已输出 ISO 保留。重试通过 Live 控制台挂载现有 Arch 系统，不重新格式化磁盘。
arch-chroot 的私有 PID 命名空间会在入口退出后清理后台进程，因此最终 QEMU
启动脚本保持前台等待，直到 QMP 发出退出命令。
这些现象是本次嵌套测试环境的实测记录，未据此断言 Windows WHPX 或 Linux KVM
存在相同问题；两种硬件加速路径的命令已提供，但本次没有直接实测。

## 最小 Live 环境中的命令提示

基础包没有安装 inetutils 中的独立 `hostname` 工具，验收直接读取
`/proc/sys/kernel/hostname`，得到内核实际值 `basaltos`。
archiso 会清理软件包仓库同步数据库，因此 `pacman -Q` 虽能显示已安装版本，
也会提示 core/extra 数据库尚不存在。需要安装或升级软件时使用 `pacman -Syu`，
会从已经固定的清华源同步数据库并进行完整升级。
