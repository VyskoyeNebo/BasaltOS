# M2：KDE Plasma 与中文输入法

继续 M1 仓库，M1 基线提交为 `7e4c075`。M1 ISO 和校验文件保留在 `out/`；
M2 使用 `out/m2/`，同名 ISO 不会覆盖 M1。
M1 的 hostname、locale、时区、键盘和 pacman 清华源配置保持不变。

## 配置与账号

- 桌面为 Plasma Wayland；精简入口包 `plasma-desktop`，配套 SDDM、Konsole、Dolphin、Ark。
- SDDM 使用 KDE 官方 Breeze 登录主题，采用居中头像、账户与密码框的熟悉布局；greeter 使用 X11，登录后的 Plasma 使用 Wayland。
- Live 登录账号：**root**，密码：**basaltos**。不自动跳过 SDDM，便于检查登录流程。
- 保留 `dhcpcd`、`iwd`、`nano`；NetworkManager 主管有线与无线网络，使用 iwd 后端和 systemd-resolved DNS。
- fcitx5 默认拼音，按 **Ctrl+Space** 切换中英文；安装 Qt/GTK 集成、CJK 和 Emoji 字体。
- KWin 根据 `/root/.config/kwinrc` 启动 `fcitx5-wayland-launcher.desktop`；禁用 root 用户的重复 XDG autostart。
- 只设置 `XMODIFIERS=@im=fcitx`，不全局强制 Qt/GTK IM 模块，遵循 [Fcitx 的 Plasma Wayland 配置](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland#KDE_Plasma)。
- 桌面使用原生 Breeze Light 与 KDE 官方 Next 壁纸；不额外绘制大字 Logo 或装饰面板。未加入 Firefox/Chromium。

`scripts/configure-m2.py` 用于从 M1 profile 应用这些配置；已经配置后的仓库无需每次构建重跑。

## VirtualBox 构建

沿用 M1 已安装的 `BasaltOS-M1-builder`，无需重新建仓库、格式化磁盘或安装系统。
当前采用默认 VirtualBox 管理器，将已有构建机与其他虚拟机同时列出。
不要再将 `VBOX_USER_HOME` 指向 `work/vbox-config`；旧隔离注册文件仅作为历史记录保留。
构建机配置和磁盘仍在 `E:\BasaltOS\work\vms\BasaltOS-M1-builder\`，不移动其他虚拟机文件。
如果默认管理器尚未注册已有构建机，只需登记一次，不能重复创建或格式化：

```powershell
$env:VBOX_USER_HOME = $null
& 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe' registervm `
  'E:\BasaltOS\work\vms\BasaltOS-M1-builder\BasaltOS-M1-builder.vbox'
```

宿主 PowerShell：

```powershell
Set-Location E:\BasaltOS
$env:VBOX_USER_HOME = $null
$vbox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
& $vbox startvm BasaltOS-M1-builder --type headless
tar -cf work/m2-source.tar .gitattributes .gitignore profile scripts docs README.md
python scripts/transfer-server.py
```

在 Arch Live root shell 中执行：

```bash
curl -fsS http://10.0.2.2:8181/scripts/build-m2-vm.sh -o /tmp/build-m2-vm.sh
bash /tmp/build-m2-vm.sh
```

脚本挂载现有 `/dev/sda1`，将源码快照解压到已有项目 `work/m2-source.*`，
避免覆盖时遗留 M1 中已移除的服务链接。然后在已有磁盘系统内执行：

```bash
arch-chroot /mnt bash "$guest_source/scripts/setup-builder.sh"
arch-chroot /mnt env \
  BASALT_MILESTONE=m2 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/out/m2 \
  bash "$guest_source/scripts/build.sh"
```

`$guest_source` 是脚本打印的源码快照路径。构建继续使用官方 `mkarchiso`；
工作目录为 ext4。脚本检查 ISO 大于 500 MB 且小于 **4,000,000,000 字节**，
生成 SHA-256，再将产物和日志回传宿主 `out/m2/`。

## Windows QEMU / WHPX

本次使用 MSYS2 UCRT64 QEMU 便携文件，全部从清华镜像下载，仅解压到 `work/tools/`。
没有运行全局安装器或修改 PATH。准备命令（Python 3.14+）：

```powershell
python scripts/setup-qemu-windows.py
```

脚本读取清华 UCRT64 数据库、解析运行依赖并逐个校验 SHA-256。
该路线也由 [QEMU 官方 Windows 下载说明](https://www.qemu.org/download/#windows)列出。

启动 M2 ISO（6 GiB 内存、4 vCPU、virtio 显卡、NAT 网络）：

```powershell
.\scripts\start-m2-qemu.ps1 -Accelerator whpx
```

若 WHPX 无法启动，可使用已保留的 TCG 时钟配置：

```powershell
.\scripts\start-m2-qemu.ps1 -Accelerator tcg
```

脚本默认打开 SDL 可见窗口，QMP 控制口仅绑定 `127.0.0.1:4452`。
需要后台截图验收时加 `-Display none`，使用同一 ISO 和其余启动参数。
WHPX 的 [QEMU 参数说明](https://www.qemu.org/docs/master/system/invocation.html)。

## 图形验收

确认画面已出现 SDDM 后保存截图：

```powershell
python scripts/qemu-console.py status --port 4452
python scripts/qemu-console.py snapshot --port 4452 --filename E:/BasaltOS/docs/m2-sddm.png
```

登录字段默认 root，密码框获得焦点。通过真实虚拟键盘输入密码：

```powershell
python scripts/qemu-console.py type --port 4452 --text basaltos
```

进入 KDE 后，用 Ctrl+Alt+T 打开 Konsole。根据输入法当前状态用 Ctrl+Space 切到英文，
执行 hostname、网络、fcitx5 进程检查，再切到拼音输入实际中文。
`type --no-enter` 可以保留预编辑候选窗口，不自动执行命令。

```powershell
python scripts/qemu-console.py key --port 4452 --key ctrl-alt-t
python scripts/qemu-console.py key --port 4452 --key ctrl-spc
python scripts/qemu-console.py type --port 4452 --text 'hostnamectl --static; ip -br a; pgrep -a fcitx5'
# 完成真实拼音输入后保存桌面与 Konsole：
python scripts/qemu-console.py snapshot --port 4452 --filename E:/BasaltOS/docs/m2-desktop.png
# 退出本次测试进程：
python scripts/qemu-console.py quit --port 4452
```

截图来自真实 QEMU VGA 帧缓冲区，输入通过 QMP 键盘事件完成。
最终结果、ISO 大小和校验值以 `docs/M2-RESULTS.md` 为准。
