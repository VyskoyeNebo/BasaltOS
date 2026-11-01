#!/usr/bin/env python3
"""Import the official archiso package's releng profile, including link metadata."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

root = Path(__file__).resolve().parents[1]
package = Path(sys.argv[1])
profile = root / 'profile'
if profile.exists():
    raise SystemExit('profile/ already exists; refusing to overwrite it')
prefix = 'usr/share/archiso/configs/releng/'
links = {}
with tarfile.open(package) as archive:
    for member in archive.getmembers():
        if not member.name.startswith(prefix):
            continue
        relative = member.name[len(prefix):]
        if not relative:
            continue
        destination = profile / relative
        if not destination.resolve().is_relative_to(profile.resolve()):
            raise SystemExit(f'Unsafe archive member: {member.name}')
        if member.isdir():
            destination.mkdir(parents=True, exist_ok=True)
        elif member.issym():
            links[relative] = member.linkname
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(member.linkname, encoding='utf-8')
        elif member.isfile():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.extractfile(member).read())

(root / 'scripts/profile-symlinks.json').write_text(
    json.dumps(links, indent=2, sort_keys=True) + '\n', encoding='utf-8')
(root / 'docs/UPSTREAM.md').write_text(
    '# 上游来源\n\n'
    '- 官方 archiso 92-1 软件包中的 `usr/share/archiso/configs/releng/`。\n'
    '- 下载： https://mirrors.tuna.tsinghua.edu.cn/archlinux/extra/os/x86_64/archiso-92-1-any.pkg.tar.zst\n'
    f'- 软件包 SHA-256： `{hashlib.sha256(package.read_bytes()).hexdigest()}`\n'
    '- 上游项目： https://gitlab.archlinux.org/archlinux/archiso\n'
    '- 本仓库只做 x86_64 的 M1 命令行 Live ISO 定制。\n'
    '- Windows 工作区中的符号链接以目标字符串保存，Git 索引记录为符号链接；'
    '`scripts/stage-profile.py` 在 Linux 构建副本中按清单恢复链接。\n',
    encoding='utf-8')
print(f'Imported releng; {len(links)} symbolic links recorded')
