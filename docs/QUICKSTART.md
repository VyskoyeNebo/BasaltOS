# BasaltOS 快速开始

BasaltOS 0.1.1 是首版的桌面入口修正版，使用新构建的 x86_64 ISO。
它包含 KDE Plasma、Fcitx5 拼音与游戏工具，安装器支持可选 LUKS2 加密和 btrfs。
完整镜像约 2.35 GB；**Secure Boot 当前未启用**，下载前请阅读
[0.1.1 发行说明](RELEASE-NOTES-0.1.1.md)。

## 1. 下载附件

从 [GitHub Release](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.1) 下载：

- `basaltos-0.1.1-x86_64.iso.part00`
- `basaltos-0.1.1-x86_64.iso.part01`
- `basaltos-0.1.1-x86_64.iso.part02`
- `SHA256SUMS`、`SHA256SUMS.asc`、`basaltos-key.asc`
- `basaltos-0.1.1-x86_64.iso.sha256`

三个分片需要放在同一目录。它们使用本次 0.1.1 文件名和签名清单；
本次公开 Release 版本为 0.1.1，包含四个新增桌面入口。
下载较慢时可使用支持断点续传的下载工具，完成后再校验。

## 2. 校验签名、重组并检查 ISO {#verify}

当前使用 **既有 TEST Release 测试签名身份**，主钥完整指纹为：

```text
29DAFB5537B451968276DA003941AA503494B8B1
```

该密钥有效至 2027-05-01。正式离线密钥管理尚未部署；相同下载站点上的指纹
不能替代独立的身份核对。安装 GPG 的环境可执行：

```bash
gpg --show-keys --with-fingerprint basaltos-key.asc
gpg --import basaltos-key.asc
gpg --verify SHA256SUMS.asc SHA256SUMS
```

核对完整指纹并确认签名有效后，再检查文件散列与重组。SHA-256 检查完整性，
它本身不证明发布者身份。

### Windows：Python 重组

从 Release 附件下载 `join-iso.py`，或从 [v0.1.1 源码](https://github.com/VyskoyeNebo/BasaltOS/blob/v0.1.1/scripts/join-iso.py)
取得同一工具。需要 Python 3.10 或更新版本，不需要第三方 Python 库。
在附件所在目录打开 PowerShell：

```powershell
python .\join-iso.py --release-dir . --version 0.1.1 --output .\basaltos-0.1.1-x86_64.iso
Get-FileHash .\basaltos-0.1.1-x86_64.iso -Algorithm SHA256
```

工具逐片校验，拒绝覆盖已有目标文件，最后校验完整 ISO。
`join-iso.py` 是源码工具，不在 本次签名清单内，可对照上述版本化源码审阅；
它不代替 GPG 验签。

### Linux：二进制拼接

```bash
sha256sum --ignore-missing -c SHA256SUMS
cat basaltos-0.1.1-x86_64.iso.part00 \
    basaltos-0.1.1-x86_64.iso.part01 \
    basaltos-0.1.1-x86_64.iso.part02 \
    > basaltos-0.1.1-x86_64.iso
sha256sum -c basaltos-0.1.1-x86_64.iso.sha256
```

完整 ISO 的预期 SHA-256：

```text
ca16fc6de24984b2ef05f20b56175ce6b699b07302ab146c3e10668aa5028905
```

完整大小：**2,353,299,456 bytes**。散列不一致时停止使用该文件，重新检查下载和分片顺序。

## 3. 写入 U 盘

先备份目标 U 盘中的文件，确认盘符与容量。用可信的镜像写盘工具，把**重组并核验后的完整 ISO**
按磁盘镜像写入空 U 盘；写盘会清空所选 U 盘。
本次没有测试具体写盘工具，不承诺所有物理设备的启动兼容性。

## 4. 启动 Live 桌面

从固件启动菜单选择 U 盘。当前发行版没有签名 Secure Boot 启动链，
需在设备固件中关闭 Secure Boot 才能使用这一镜像。

Live 登录账号：`gamer`，密码：`basaltos`。
默认语言为 `zh_CN.UTF-8`，时区为 `Asia/Shanghai`，键盘为 `us`。
Fcitx5 拼音通过 **Ctrl+Space** 切换中英文；若出现可选云拼音询问，可按自己的隐私偏好选择。

桌面新增“计算机、回收站、文件管理器、控制面板”。Plasma 6 首次点选启动器可能需要确认信任，先核对来源和命令。

## 5. 安装到硬盘

桌面双击“安装 BasaltOS”。安装器会询问位置、键盘、分区和用户信息。

1. 核对目标磁盘，先备份已有数据。自动擦除方案会清空所选磁盘。
2. 默认使用 btrfs，可勾选“加密系统”并设置自己的 LUKS 口令。
3. 创建普通用户与登录密码。安装后使用自己创建的账号；Live 账号不会作为固定安装账号。
4. 确认安装摘要，完成后正常关机，移除 U 盘，再从安装盘启动。

加密方案中的 ESP 和独立 `/boot` 保持明文，系统与 home 位于 LUKS2 内。
这不是“包括所有启动文件在内的全盘加密”。
当前布局、子卷与验证范围见 [M3 验收](M3-RESULTS.md)和 [M6 验收](M6-RESULTS.md)。

## 6. 首次更新与游戏

在已安装系统的 Konsole 中：

```bash
sudo basaltos-update --check-only
sudo basaltos-update
```

正常更新先创建 root 快照、boot/ESP 备份，再执行完整 `pacman -Syu`。
自建仓库默认关闭，官方仓库使用清华镜像。
本次自建仓库仅作为测试用途，公钥具有较大的包签名信任权限；
需要试用时阅读 [签名与仓库说明](RELEASE.md)和 [公开部署说明](PUBLISHING.md)。

Steam 首次启动还会下载客户端更新；Proton、游戏和账号登录由用户按需完成。
MangoHud、GameMode、Proton-GE 和反作弊边界见 [游戏指南](GAMING.md)。
更新失败后的离线恢复见 [安全与恢复](SECURITY.md)，固定 `@` 布局不应直接套用 `snapper rollback`。
