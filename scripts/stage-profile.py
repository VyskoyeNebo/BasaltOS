#!/usr/bin/env python3
"""Stage a Windows or Linux checkout onto a Linux filesystem."""
import json
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
destination = Path(sys.argv[1]).resolve()
if destination.exists():
    raise SystemExit(f'Staging destination already exists: {destination}')
shutil.copytree(root / 'profile', destination, symlinks=True)
links = json.loads((root / 'scripts/profile-symlinks.json').read_text())
for relative, target in links.items():
    path = destination / relative
    if not path.parent.resolve().is_relative_to(destination):
        raise SystemExit(f'Link escapes profile: {relative}')
    path.unlink(missing_ok=True)
    path.symlink_to(target)
print(destination)
