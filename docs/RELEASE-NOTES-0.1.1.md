# BasaltOS 0.1.1

0.1.1 修复首版缺少常用桌面入口的问题。新增“计算机、回收站、文件管理器、控制面板”，
分别使用 Dolphin 和 KDE 系统设置。保留原生 Breeze 桌面、中文输入法、安装器、游戏套件与安全配置。

- [下载 0.1.1](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.1)
- [快速开始](https://vyskoyenebo.github.io/BasaltOS/docs/QUICKSTART.html)
- [本次验收记录](https://vyskoyenebo.github.io/BasaltOS/docs/DESKTOP-FIX-0.1.1.html)
- [首版 0.1.0](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.0) 继续保留，旧标签和附件不覆盖。

## 修正内容

- 四个中文桌面入口预置于 `/etc/skel/Desktop/`，模式为 755。
- “计算机”打开 Dolphin 的根文件系统，磁盘与可移动设备位于侧栏；“文件管理器”启动 Dolphin；
  “回收站”打开 `trash:/`；“控制面板”启动 KDE 系统设置。
- KDE 登录后补齐缺失的四个入口，已有同名文件保留。新建图标时使用 `kbuildsycoca6 --noincremental` 刷新当前用户应用缓存。
- 桌面文件经过 `desktop-file-validate` 检查。Plasma 6 **首次点选可能需要确认信任**；
  如提示“未信任的程序”，确认来源和命令后再选择允许启动。这不代表文件执行权限可以省略。
- 更新 ISO 版本说明、`VERSION_ID=0.1.1` 和自建 `basaltos-release` 包版本。

## 下载与校验

完整 ISO 为 **2,353,299,456 bytes**（约 2.35 GB）。SHA256：

```text
ca16fc6de24984b2ef05f20b56175ce6b699b07302ab146c3e10668aa5028905
```

截图与本次构建记录见验收文档。GitHub 提供三个 ISO 分片、签名清单、公钥和重组工具；
先核对完整公钥指纹并验证 `SHA256SUMS.asc`，再校验分片与完整 ISO。

```text
29DAFB5537B451968276DA003941AA503494B8B1
```

继续使用有效至 2027-05-01 的 TEST Release 测试身份，正式离线签名身份尚未部署。
新增独立 `.sha256` 与 `join-iso.py` 不属于签名清单；ISO 与分片散列由签名的 `SHA256SUMS` 认证。

## 已有安装

下载新 ISO 不会自动修改旧系统。本次项目内的 M6 测试盘已使用同一组文件修正；
其他旧安装可以检出 `v0.1.1` 源码，在该 BasaltOS 系统内执行：

```bash
sudo bash scripts/apply-desktop-fix.sh "$PWD"
basaltos-desktop-shortcuts
```

第二条命令以桌面用户执行，不加 sudo。它遵循 XDG 桌面目录，不覆盖同名文件。
自建 `basaltos-release` 包只保存版本元数据，单独升级该包不会给旧安装自动部署桌面修正。

## 验证范围与限制

本次验证新 ISO 的 UEFI Live KDE 桌面及既有 M6 加密测试盘修正，实际双击“计算机”打开 Dolphin。
没有重新完成整套 Calamares 安装或 BIOS 回归；M3 的 BIOS/UEFI 和 M6 的 UEFI 安装验收仍为历史依据。
Secure Boot 未启用，ESP 与独立 `/boot` 明文，反作弊逐游戏而异，虚拟 GPU 不代表实体游戏性能。
快照恢复仍需按安全文档操作。测试仓库默认关闭，安装器仍保留 M3 品牌文字。
详情见[首版限制](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.0)。
