# M2 验收结果

2026-11-01（Asia/Shanghai）：**通过**。从最终 ISO 经 SDDM 登录进入 KDE Plasma，
在 Konsole 中验证主机名、网络和真实拼音输入。本次完成后停在 M2。

## 产物与构建

- ISO：`E:\BasaltOS\out\m2\basaltos-2026.11.01-x86_64.iso`
- 大小：`1914241024` 字节，约 `1.914 GB / 1.783 GiB`，低于 4,000,000,000 字节。
- SHA-256：`67a41064938ea25f1586c10aa22bad0248545d07b8b8b97a67451ff44dd3d1a9`
- 校验文件：`out/m2/basaltos-2026.11.01-x86_64.iso.sha256`
- ISO9660 Primary Volume Descriptor 实读卷标：`basaltos`。
- 官方 archiso：`92-1`；完整日志：`out/m2/build.log`。
- 最终源码提交：`d1ff444`；验收文档与截图随最终提交，标签 `m2-desktop`。

继续使用现有 VirtualBox 构建机与 ext4 构建磁盘，未重新安装系统或格式化磁盘。
在官方 Arch Live shell 中执行：

```bash
curl -fsS http://10.0.2.2:8181/scripts/build-m2-vm.sh -o /tmp/build-m2-vm.sh
bash /tmp/build-m2-vm.sh
```

本次脚本实际执行的构建命令：

```bash
arch-chroot /mnt env \
  BASALT_MILESTONE=m2 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/out/m2 \
  bash /root/BasaltOS/work/m2-source.cxs5ajPB/scripts/build.sh
```

最终 mkarchiso 工作目录：`/root/BasaltOS/work/linux-build/m2.HivsQNtv`。
源码快照和构建目录由脚本随机创建，复现时不需要手动复用这些名称。
宿主传输服务、源码打包与完整准备流程见 [BUILD-M2.md](BUILD-M2.md)。

## 桌面与账号

登录账号 **root**，密码 **basaltos**。SDDM 使用官方 Breeze 主题，保留居中头像、
密码框、时钟和电源操作；桌面采用原生 Breeze Light 与 KDE 官方 Next 壁纸。
移除了最初试作的大字品牌壁纸和自绘登录主题。

| 软件 | 最终 ISO 中的版本 |
| --- | --- |
| plasma-desktop / plasma-workspace | 6.8.2-1 |
| sddm | 0.21.0-7 |
| fcitx5 | 5.1.23-1 |
| networkmanager | 1.58.1-2 |
| linux | 7.2.11.arch1-1 |

包含 Konsole、Dolphin、Ark、nano、dhcpcd、iwd、Fcitx5 中文插件与配置工具、
Qt/GTK 集成、CJK 和 Emoji 字体。本阶段未加入浏览器。

## QEMU 实测

Windows 原生 QEMU `11.1.3`，**WHPX 实际启用**，q35、4 vCPU、6 GiB RAM、
virtio-vga、virtio-net、用户态 NAT。通过 BIOS 从最终 ISO 启动，无附加系统磁盘。
验收使用 `-display none` 配合 QMP；交互启动默认打开 SDL 窗口：

```powershell
Set-Location E:\BasaltOS
.\scripts\start-m2-qemu.ps1 -Accelerator whpx
```

脚本使用 `-accel whpx -cpu max -smp 4`，不是 Linux 的 `-enable-kvm`。
WHPX 不可用时可指定 `-Accelerator tcg`；本次无需回退，最终镜像未重复做 TCG 验收。

| 项目 | 实测结果 |
| --- | --- |
| 登录流程 | SDDM 显示 root，输入 basaltos 后进入 KDE 桌面 |
| 会话 | `XDG_SESSION_TYPE=wayland` |
| 主机名 | `hostnamectl --static` 返回 `basaltos` |
| IPv4 | `enp0s3 UP 10.0.2.15/24` |
| Fcitx5 | KWin 启动 `fcitx5-wayland-launcher --reopen` 与 `fcitx5` |
| 中文输入 | Ctrl+Space 切换，键入 zhongwen，候选“中文”，空格后提交“中文”到 Konsole |
| 清华域名 ping | 3 发 3 收，0% 丢包 |
| 清华镜像 HTTPS | `https://mirrors.tuna.tsinghua.edu.cn/archlinux/` 返回 `HTTP/2 200` |
| locale | `LANG=zh_CN.UTF-8` |
| 时区 | `/etc/localtime` 指向 `/usr/share/zoneinfo/Asia/Shanghai` |
| 键盘 | `KEYMAP=us` |

宿主代理将清华域名解析为 `198.18.0.64`；ping 反映代理路径可达，HTTPS 200
补充验证实际镜像访问。UEFI 配置已生成，未单独启动验收；未验收游戏、3D 性能或安装到硬盘。

## 截图

全部为最终 ISO 的真实 QMP `screendump` 截图；输入使用 QEMU 虚拟键盘事件。

- [SDDM 登录页](m2-sddm.png)
- [KDE 桌面](m2-desktop-clean.png)
- [Konsole 主机名、地址、输入法进程与已提交中文](m2-desktop.png)
- [拼音候选窗口](m2-ime-candidates.png)
- [网络、locale、时区与键盘](m2-network-locale.png)

## 问题与处理

- Windows 原先没有 QEMU。通过清华 MSYS2 镜像准备项目内便携版本并校验包 SHA-256，
  未安装全局软件或修改 PATH。WHPX 可正常启动；日志偶见 interrupt vector 0 提示，未阻止验收。
- Wayland 输入法由 KWin 启动，关闭 root 重复 XDG autostart，不全局强制 Qt/GTK IM 模块。
  默认拼音状态下输入终端命令前需切回英文。中文验收保持 UTF-8 locale。
- VirtualBox 曾因独立 `VBOX_USER_HOME` 的服务连接使管理器只显示构建机。
  已恢复默认管理器，并将现有 BasaltOS 构建机登记到其中。其他虚拟机配置与磁盘未删除或移动，
  现在两台独立虚拟机并列显示。后续命令应清空 `VBOX_USER_HOME`，不再切换隔离注册目录。
- 构建中的可选固件警告、保留配置导致的 `.pacnew`、缺少 pv 时使用 cp，以及小写卷标提示
  均未阻止构建。小写卷标按要求保留并通过实读校验。

M1 的 hostname、locale、locale.gen、时区链接、keymap、两份 pacman 配置和清华 mirrorlist
均与 `7e4c075` 相同。原 M1 ISO SHA-256 复核不变，仍为
`b8b2779a5bcbc7345a324353fdf02fda133d3004f22c58c994b0b829129ee76d`。
构建机与验收 QEMU 在完成后关闭，默认 VirtualBox 管理器保留两台独立虚拟机登记。
