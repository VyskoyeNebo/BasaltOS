# Secure Boot：M5 当前未启用

M5 ISO 与验收系统没有启用 Secure Boot，也没有生成、分发私钥或修改固件密钥。
LUKS 保护关机时的磁盘数据，不能认证明文 `/boot` 或启动链；Secure Boot 与 LUKS 解决不同问题。
以下是用户自行配置的路线，不属于本次已验证功能。

## 建议路线：独立签名 UKI

M3 使用 GRUB、外置 initramfs 和固定 `rootflags=subvol=@`。仅给 GRUB 与内核签名，
不能据此宣称外部 initramfs、grub.cfg 和启动参数已被完整认证。
建议另建一个由 UEFI 直接启动的签名 UKI，内含内核、initramfs、参数，
保留现有 GRUB 配置用于 Secure Boot 关闭时恢复。
参考 [systemd ukify](https://www.freedesktop.org/software/systemd/man/latest/ukify.html)
与 [Linux EFI stub](https://docs.kernel.org/admin-guide/efi-stub.html)。

先备份重要数据、LUKS header、固件 PK/KEK/db/dbx 与 OEM 恢复方式，准备能启动的外置介质。
下列命令在**已安装 UEFI 系统**执行，ESP 实际挂载点需先用 `findmnt /boot/efi` 核实。

```bash
sudo pacman -Syu sbctl systemd-ukify efibootmgr
sudo sbctl status
sudo sbctl create-keys
sudo install -d /boot/efi/EFI/Linux
# 手动编写 /etc/kernel/cmdline：依据当前 /proc/cmdline 与 /etc/default/grub，
# 保留本机真实 rd.luks.name、root、rootflags=subvol=@ 等参数，移除 BOOT_IMAGE。
# 不要照抄其他设备的 UUID，不把 LUKS 密码写进去。
sudo ukify build --linux=/boot/vmlinuz-linux \
  --initrd=/boot/initramfs-linux.img \
  --cmdline=@/etc/kernel/cmdline --os-release=@/etc/os-release \
  --output=/boot/efi/EFI/Linux/basaltos-linux.efi
sudo sbctl sign -s /boot/efi/EFI/Linux/basaltos-linux.efi
sudo sbctl verify
```

M3 的 mkinitcpio 已有 microcode 钩子；检查自己的 initramfs 内容和参数后再继续。
用 `lsblk -o NAME,PATH,FSTYPE,PARTUUID,MOUNTPOINTS` 找到本机 ESP 的磁盘和分区号，
通过 efibootmgr **新增** `\EFI\Linux\basaltos-linux.efi` 启动项；不要照抄 `/dev/sda`、分区号，
不要覆盖 GRUB fallback。可先在 Secure Boot 关闭时用固件一次性启动菜单测试该 UKI。

## 密钥注册与风险

只有确认 UKI 可启动、恢复介质可用后，才考虑进入固件 Setup Mode。
`sbctl enroll-keys -m` 可同时加入 Microsoft 证书，但不保证保留全部 OEM/Option ROM 所需信任。
某些显卡、存储或笔记本固件依赖这些签名，清除或错误注册密钥可能导致无法启动，甚至难以恢复。
不要使用跳过安全检查的强制参数。按照设备厂商恢复说明处理，必要时保持 Secure Boot 关闭。
依据 [sbctl 手册](https://man.archlinux.org/man/sbctl.8.en)。

注册完成并核实后在固件启用 Secure Boot，启动已签名 UKI，再核对 `sbctl status`、启动日志。
旧的未签名 GRUB 入口在开启时不应被当作有效恢复入口；恢复时可能需要在固件关闭 Secure Boot。
私钥只保存在受限的 root 路径，离线加密备份；不能放入 ISO、Git、ESP 或公共共享目录。

每次内核、initramfs、启动参数或 NVIDIA 模块变动后：

1. 确认 mkinitcpio 成功生成与 `/usr/lib/modules` 匹配的 initramfs。
2. 重新构建 UKI，再执行 `sbctl sign -s` 与 `sbctl verify`。
3. 成功后再重启，并保留可用的旧签名 UKI/恢复介质。

只运行签名 hook 并不会自动重建过期 UKI。M5 的更新脚本不自动生成密钥、不负责这条可选启动链；
若用户启用，应自行集成有失败阻断的 UKI 构建/签名流程。
脚本备份 boot/已挂载 ESP，但不备份固件 NVRAM 或代替离线密钥备份。

## NVIDIA 与内核模块签名

`sbctl` 签的是 EFI/UKI 文件，不是 NVIDIA `.ko`。内核是否强制模块签名取决于该内核配置和
lockdown/验证策略，不能仅凭固件 Secure Boot 状态推断。若启用模块验证，必须让签名证书进入
**该内核信任的模块密钥环**，并签署对应内核版本的 NVIDIA 模块：

```bash
# 示意，KEY/CERT/MODULE 必须替换为受控文件；MODULE 是未压缩 .ko：
/usr/lib/modules/$(uname -r)/build/scripts/sign-file sha256 KEY CERT MODULE
```

需要与目标内核匹配的 headers。对压缩模块先按发行方式处理解压/重压缩，随后 `depmod`、
重建 initramfs、重建并签名 UKI。DKMS 每次为新内核重建都要重新签名，不能只签一次。
固件 db 信任、Shim/MOK 信任与内核模块密钥环不是可以无条件互换的概念；
这里的直接 UKI 路线不意味着 `mokutil --import` 就能让内核接受该证书。
`modinfo -F signer` 只显示签名信息，仍要用模块加载结果、内核日志与密钥环检查确认。
参见 [Linux 内核模块签名文档](https://docs.kernel.org/admin-guide/module-signing.html)。

本次没有真实 NVIDIA 硬件、固件密钥注册或开启 Secure Boot 的验收，不承诺该可选路线开箱可用。
