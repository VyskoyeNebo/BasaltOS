# 上游来源

- 官方 archiso 92-1 软件包中的 `usr/share/archiso/configs/releng/`。
- 下载： https://mirrors.tuna.tsinghua.edu.cn/archlinux/extra/os/x86_64/archiso-92-1-any.pkg.tar.zst
- 软件包 SHA-256： `a79f7a3a3032295e9d041c759e47ee4324166aa4c1cf19a4c3e5550ade5312e2`
- 上游项目： https://gitlab.archlinux.org/archlinux/archiso
- 本仓库只做 x86_64 的 M1 命令行 Live ISO 定制。
- Windows 工作区中的符号链接以目标字符串保存，Git 索引记录为符号链接；`scripts/stage-profile.py` 在 Linux 构建副本中按清单恢复链接。
