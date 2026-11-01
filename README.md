# BasaltOS

基于 Arch Linux 官方 archiso 的游戏与安全向发行版项目。
当前仅实现 M1：可启动的 x86_64 命令行 Live ISO，BIOS 和 UEFI 启动配置。

- 构建与启动：[`docs/BUILD.md`](docs/BUILD.md)
- 环境故障与备用路径：[`docs/ENV-NOTES.md`](docs/ENV-NOTES.md)
- 上游 releng 来源：[`docs/UPSTREAM.md`](docs/UPSTREAM.md)
- archiso 配置：`profile/`
- ISO 产物：`out/`，不纳入 Git。

Live 环境自动登录 root，默认语言 `zh_CN.UTF-8`、时区 `Asia/Shanghai`、键盘 `us`。
以太网由 systemd-networkd 自动 DHCP，DNS 使用 systemd-resolved；无线工具为 iwd。
`dhcpcd` 作为备用工具保留，默认不启动，以免与 systemd-networkd 重复管理网卡。
Linux 文本控制台不提供完整汉字字形；未安装图形桌面或输入法。
