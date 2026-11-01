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
- 当前主机不提供嵌套硬件虚拟化；虚拟机内的 QEMU 使用 `-accel tcg -cpu max`。
- Windows 用户直接运行 QEMU 时使用 `-accel whpx`，Linux 有 `/dev/kvm` 时使用 `-enable-kvm`。

## Windows 文件系统注意事项

Git 对符号链接使用 mode `120000`；Windows checkout 可用普通文件保存链接目标。
`scripts/profile-symlinks.json` 记录所需链接，`stage-profile.py` 只在 Linux 构建副本中恢复。
archiso 的工作目录必须位于 Linux 文件系统，不能直接在 NTFS、DrvFS 或 VirtualBox 共享文件系统上构建 rootfs。
软件包仓库、ISO 内 pacman 配置和镜像列表均固定到清华镜像，保留软件包签名验证。
