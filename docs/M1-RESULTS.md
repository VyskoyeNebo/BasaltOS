# M1 验收结果

2026-11-01（Asia/Shanghai）：**通过**。本次停在 M1，未安装图形桌面或输入法。

## 产物

- ISO：`E:\BasaltOS\out\basaltos-2026.11.01-x86_64.iso`
- 大小：`932524032` 字节，约 `889.32 MiB`，超过 500 MB。
- SHA-256：`b8b2779a5bcbc7345a324353fdf02fda133d3004f22c58c994b0b829129ee76d`
- 校验文件：`out/basaltos-2026.11.01-x86_64.iso.sha256`
- ISO 9660 Primary Volume Descriptor 实读卷标：`basaltos`。
- 构建工具：官方 archiso `92-1`，内核 `7.2.11-arch1-1`。
- 完整构建日志：`out/build.log`。

## 实际构建命令

在官方 Arch Live ISO 启动的专用 VirtualBox 构建机中：

```bash
arch-chroot /mnt bash /root/BasaltOS/scripts/setup-builder.sh
arch-chroot /mnt bash /root/BasaltOS/scripts/build.sh
```

最终构建中执行的 mkarchiso 命令：

```bash
mkarchiso -v \
  -w /root/BasaltOS/work/linux-build/m1.N9Izp7wF/work \
  -o /root/BasaltOS/out \
  /root/BasaltOS/work/linux-build/m1.N9Izp7wF/profile
```

全新构建时工作目录随机生成，不需要手动复用这个目录。
容器和虚拟机的完整准备步骤见 [BUILD.md](BUILD.md)。

## QEMU 实测

QEMU `11.1.3`，BIOS 从同一 ISO 启动，q35、qemu64、1 vCPU、2 GiB RAM、
单线程 TCG、`-icount shift=auto,sleep=on -rtc clock=vm`。
当前宿主不支持嵌套 KVM，未直接实测 Windows WHPX 或 Linux KVM。
TCG 启动耗时数分钟；实际通过 VGA 自动进入 root shell。

| 项目 | 实测结果 |
| --- | --- |
| root shell | 自动登录，`uid=0(root)` |
| 内核 hostname | `/proc/sys/kernel/hostname` 为 `basaltos` |
| IPv4 | `enp0s2` 为 `10.0.2.15/24`，由 DHCP 获得 |
| ping 清华镜像域名 | 3 发 3 收，0% 丢包 |
| HTTPS 访问清华镜像 | `https://mirrors.tuna.tsinghua.edu.cn/archlinux/` 返回 `HTTP/2 200` |
| 默认 locale | `LANG=zh_CN.UTF-8` |
| 已生成 locale | 包含 `zh_CN.utf8`、`en_US.utf8` |
| 时区 | `/etc/localtime` 指向 `/usr/share/zoneinfo/Asia/Shanghai` |
| 键盘 | `KEYMAP=us` |
| 保留工具 | dhcpcd `10.5.2-1`、iwd `3.12-2`、nano `9.2-1` |

宿主代理将镜像域名解析为 `198.18.0.64`；ping 反映代理网络路径的可达性。
额外的 HTTPS 200 结果用于确认实际镜像站访问。BIOS 已实测，UEFI 启动配置已生成，
本次未额外进行 UEFI 启动验收。

## 截图

- 要求的主截图：[m1-qemu.png](m1-qemu.png)，包含内核 hostname、root、地址及 ping 结果。
- 补充配置与 HTTPS：[m1-qemu-locale-https.png](m1-qemu-locale-https.png)。

两张图均为 QMP 对真实 VGA 帧缓冲区的截图，命令通过 QEMU 虚拟键盘输入。
没有合成终端画面。验收 shell 临时使用 `LC_ALL=C`，便于文本控制台显示；
默认中文 locale 配置没有改变。

## 遇到的问题

Docker Desktop 启动崩溃，改走独立 VirtualBox；嵌套 TCG 最初出现定时器 panic，
后调整虚拟 CPU 和时钟参数。早期验收附加的串口配置已移除并重新构建。
详细记录及失败证据见 [ENV-NOTES.md](ENV-NOTES.md)。
