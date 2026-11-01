#!/usr/bin/env python3
"""Repack TUNA's official Arch bootstrap for docker import without NTFS extraction.

Requires Python 3.14+ for tar.zst support. Preserves Unix ownership, modes and links.
"""
import copy
from pathlib import Path
import sys
import tarfile

source, output = map(Path, sys.argv[1:3])
with tarfile.open(source) as archive, tarfile.open(output, 'w') as target:
    for member in archive:
        if not member.name.startswith('root.x86_64/'):
            continue
        item = copy.copy(member)
        item.name = item.name.removeprefix('root.x86_64/')
        if not item.name:
            continue
        if item.islnk():
            item.linkname = item.linkname.removeprefix('root.x86_64/')
        target.addfile(item, archive.extractfile(member) if member.isfile() else None)
print(output)
