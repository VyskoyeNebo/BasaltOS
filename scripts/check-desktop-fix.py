#!/usr/bin/env python3
"""Preserve the M6 system baseline except the approved 0.1.1 version label."""
import hashlib
import json
import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'scripts/m6-protected-sha256.json').read_text())
for relative, expected in manifest.items():
    path=root/relative
    if relative == 'profile/airootfs/etc/os-release':
        assert path.read_text() == '\n'.join(['NAME="BasaltOS"','PRETTY_NAME="BasaltOS 0.1.1"','VERSION_ID=0.1.1','ID=basaltos','ID_LIKE=arch','BUILD_ID=rolling','ANSI_COLOR="1;36"',''])
    elif expected['type'] == 'link':
        assert (os.readlink(path) if path.is_symlink() else path.read_text().strip()) == expected['target'],relative
    else:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256'],relative
print('M6 baseline preserved: 106 unchanged files/links; approved os-release 0.1.1 label.')
