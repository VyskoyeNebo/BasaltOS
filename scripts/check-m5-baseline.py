#!/usr/bin/env python3
"""Check all preexisting M4 profile settings except declared M5 changes."""
import hashlib
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root/'scripts/m5-protected-sha256.json').read_text())
for relative, expected in manifest.items():
    path = root / relative
    if expected['type'] == 'link':
        actual = os.readlink(path) if path.is_symlink() else path.read_text().strip()
        assert actual == expected['target'], relative
    else:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256'], relative
print(f'M4 protected configuration unchanged: {len(manifest)} files/links.')
