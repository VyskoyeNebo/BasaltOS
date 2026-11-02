#!/usr/bin/env python3
"""Check release public material, preserved update path and excluded artifacts."""
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(root/'scripts/check-m6-baseline.py')], check=True)
public = (root/'packaging/basaltos-key.asc').read_bytes()
assert b'-----BEGIN PGP PUBLIC KEY BLOCK-----' in public
assert b'PRIVATE KEY' not in public
assert public == (root/'profile/airootfs/usr/share/basaltos/keys/basaltos-key.asc').read_bytes()
fingerprint = (root/'packaging/basaltos-key.fingerprint').read_text(encoding='ascii').strip()
assert re.fullmatch('[A-F0-9]{40}', fingerprint)
assert fingerprint == (root/'profile/airootfs/usr/share/basaltos/keys/basaltos-key.fingerprint').read_text(encoding='ascii').strip()
old = subprocess.check_output(['git', 'show', 'm5-security:profile/airootfs/usr/lib/basaltos/update.py'], cwd=root).decode()
new = (root/'profile/airootfs/usr/lib/basaltos/update.py').read_text(encoding='utf-8')
marker = "    if Path('/run/archiso/bootmnt').exists():"
assert old[old.index(marker):] == new[new.index(marker):], 'M5 update/recovery path changed'
for name in ('profile/pacman.conf', 'profile/airootfs/etc/pacman.conf'):
    config = (root/name).read_text(encoding='utf-8')
    assert '# [basaltos]\n# SigLevel = Required\n' in config
    assert '\n[basaltos]\n' not in config, 'Placeholder repo enabled by default'
for name in subprocess.check_output(['git', 'ls-files'], cwd=root).decode().splitlines():
    assert not name.startswith(('work/', 'out/', 'repo/x86_64/'))
    assert not name.endswith(('.pkg.tar.zst', '.iso', '.sec.asc', '.private'))
print('Public key, preserved M5 update path, disabled placeholder and Git exclusions: PASS')
