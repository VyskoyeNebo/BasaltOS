#!/usr/bin/env python3
"""Check M5-specific trust boundaries before expensive ISO builds."""
import configparser
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
profile = root/'profile'
subprocess.run([sys.executable, str(root/'scripts/check-m5-baseline.py')], check=True)
previous = set(subprocess.check_output(['git', 'show', 'm4-gaming:profile/packages.x86_64'],
                                      cwd=root).decode().splitlines())
current = set((profile/'packages.x86_64').read_text().splitlines())
assert previous <= current, 'M5 removed M4 packages'
assert {'nftables', 'archlinux-keyring', 'pacman-contrib', 'fakeroot', 'libnotify'} <= current
for relative in ('pacman.conf', 'airootfs/etc/pacman.conf'):
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read(profile/relative)
    assert config['options']['SigLevel'].split() == ['Required', 'DatabaseOptional']
    assert config['options']['LocalFileSigLevel'] == 'Required'
    assert set(config.sections()) == {'options', 'core', 'extra', 'multilib'}
    for repo in ('core', 'extra', 'multilib'):
        assert config[repo]['Server'] == 'https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch'
print('M5 package preservation and runtime repository trust checks passed.')
# systemd sorts drop-ins lexically, including the preexisting archiso.conf.
resolved = configparser.ConfigParser(interpolation=None, strict=False)
resolved.optionxform = str
resolved.read(sorted((profile/'airootfs/etc/systemd/resolved.conf.d').glob('*.conf')))
assert resolved['Resolve']['MulticastDNS'] == 'no'
assert resolved['Resolve']['LLMNR'] == 'no'
print('Effective profile resolved drop-in ordering disables mDNS and LLMNR.')
