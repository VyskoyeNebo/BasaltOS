# BasaltOS 0.1.0

BasaltOS 的首个公开版本，面向游戏与安全的 Arch Linux + KDE Plasma 桌面。
这是公开的非草稿 Release，当前成熟度仍为实验阶段，验证范围以本页和各里程碑记录为准。

- 项目：[VyskoyeNebo/BasaltOS](https://github.com/VyskoyeNebo/BasaltOS)
- 官网与文档：[vyskoyenebo.github.io/BasaltOS](https://vyskoyenebo.github.io/BasaltOS/)
- 下载：[Release v0.1.0](https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.0)
- 入门：[快速开始](https://vyskoyenebo.github.io/BasaltOS/docs/QUICKSTART.html)

## 系统内容与版本来源

`v0.1.0` 指向已完成验收的 M6 系统提交 `c014311`，与 `0.1.0-m6`、`m6-release`
采用同一份 ISO payload。M7 只增加对外发布、官网和文档站，不重建系统镜像。
为保留原签名清单，ISO、分片与仓库归档保留 `0.1.0-m6` 文件名。

| 里程碑 | 内容 |
| --- | --- |
| M1 | 官方 archiso、BasaltOS 品牌、中文 locale、上海时区、命令行 Live ISO |
| M2 | KDE Plasma、SDDM、Fcitx5 拼音与中文字体 |
| M3 | Calamares、可选 LUKS2、btrfs 子卷、root/home Snapper、GRUB |
| M4 | Steam、Lutris、Gamescope、MangoHud、GameMode、Vulkan/32 位依赖、Wine Staging |
| M5 | nftables 默认拒绝新入站、更新前快照和 boot/ESP 备份、每周只提醒、隐私默认值 |
| M6 | 测试 GPG 身份、严格签名仓库、check-only、离线签名附件与分片重组 |
| M7 | 个人公开仓库、官网、文档站和本次公开 Release |

## 附件、校验与重组

完整 ISO：`basaltos-0.1.0-m6-x86_64.iso`，**2,353,299,456 bytes**，约 2.35 GB。

```text
SHA-256 0fd12156f204a6b6535c19aca1ae0f229e8e8b02579772602e68530034a27281
```

GitHub 单附件需小于 2 GiB，因此下载附件中的 `.part00`、`.part01`、`.part02`，
核验签名和散列后重组；这三片共同构成完整镜像，不是三个独立 ISO。
Release 还提供 `.sha256`、`SHA256SUMS`、`SHA256SUMS.asc`、公钥、
`pacman-repo-0.1.0-m6.tar.gz` 与便捷重组工具 `join-iso.py`。

公钥指纹：

```text
29DAFB5537B451968276DA003941AA503494B8B1
```

这是 M6 的 **TEST Release 测试身份**，不是已完成组织认证的正式生产签名身份，
主/子钥到期日为 2027-05-01。正式离线密钥保管、轮换与泄漏恢复尚需部署、演练。
ISO 和签名清单由该测试密钥签署；重组工具本身不在原 M6 签名清单中，可对照
[v0.1.0 源码](https://github.com/VyskoyeNebo/BasaltOS/blob/v0.1.0/scripts/join-iso.py)审阅。

完整步骤见 [下载、核验与安装](https://vyskoyenebo.github.io/BasaltOS/docs/QUICKSTART.html)。
Live 账号 `gamer / basaltos`；安装后使用自己创建的用户和口令。

## 已知限制

- **Secure Boot 未启用**：不提供可直接在 Secure Boot 开启时启动的完整签名链。
  sbctl/UKI/NVIDIA 模块签名仅有操作文档，没有固件密钥或真实 NVIDIA 硬件验收。
- **反作弊并非通用兼容**：预装 Steam/Proton 相关工具不代表所有 Windows 游戏可运行。
  游戏厂商会调整支持政策，需逐款核对官方说明；已有记录见游戏指南，不能保证其未来不变。
- **虚拟 GPU 有边界**：游戏工具验收使用 QEMU 软件渲染，不代表真实 GPU 游戏性能。
  软件 Vulkan 路径出现过 MangoHud FPS 为 0/帧时间为 inf；OpenGL 叠加层通过验收。
- **启动验证范围**：M3 完成过 UEFI 和 BIOS 安装后启动；M5/M6 重新验收的是 UEFI。
  本次没有新增物理设备、混合多系统或 USB 写盘兼容测试。
- **加密不包含所有启动文件**：ESP 与独立 `/boot` 明文，LUKS2 内为系统和 home。
- **恢复需要操作**：固定 `rootflags=subvol=@`，不能直接使用通用 `snapper rollback`。
  已验证快照、备份和恢复命令生成，没有完成全部离线恢复、断电或跨版本内核升级情形。
- **自建仓库默认关闭**：启用后信任的是测试签名密钥；包签名 keyring 不按仓库隔离。
  镜像没有硬编码启用公网地址，需用户明确配置后使用。
- **品牌文字沿用历史配置**：安装器仍显示 M3，系统 PRETTY_NAME 仍为 BasaltOS M4。
  本次版本以 Release、标签和 ISO 散列标识。
- **隐私声明的范围**：BasaltOS 自身没有遥测客户端；Steam、游戏和可选云拼音等第三方功能
  仍可能联网或上传数据，详见隐私文档。

## 文档与证据

[M1](https://vyskoyenebo.github.io/BasaltOS/docs/M1-RESULTS.html) ·
[M2](https://vyskoyenebo.github.io/BasaltOS/docs/M2-RESULTS.html) ·
[M3](https://vyskoyenebo.github.io/BasaltOS/docs/M3-RESULTS.html) ·
[M4](https://vyskoyenebo.github.io/BasaltOS/docs/M4-RESULTS.html) ·
[M5](https://vyskoyenebo.github.io/BasaltOS/docs/M5-RESULTS.html) ·
[M6](https://vyskoyenebo.github.io/BasaltOS/docs/M6-RESULTS.html)

构建、游戏、安全、隐私、Secure Boot 与发布说明均保留在官网文档站和 Git 源码中。
