#!/usr/bin/env python3
"""Add security defaults without rewriting the M1-M4 desktop/installer layer."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
profile = root / 'profile'
subprocess.run([sys.executable, str(root/'scripts/check-m5-baseline.py')], check=True)

def write(name, content):
    path = profile / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8', newline='\n')

packages = (profile/'packages.x86_64').read_text().splitlines()
write('packages.x86_64', '\n'.join(dict.fromkeys(packages +
      ['nftables', 'archlinux-keyring', 'pacman-contrib', 'fakeroot', 'libnotify']))+'\n')
for name in ('pacman.conf', 'airootfs/etc/pacman.conf'):
    write(name, (profile/name).read_text().replace('LocalFileSigLevel = Optional',
                                                'LocalFileSigLevel = Required'))

write('airootfs/etc/nftables.conf', '''#!/usr/bin/nft -f
# Atomic, idempotent replacement of our table only. Never flush ruleset.
destroy table inet basaltos_filter
table inet basaltos_filter {
    chain input {
        type filter hook input priority filter; policy drop;
        iifname "lo" accept
        ct state established,related accept
        meta l4proto { icmp, ipv6-icmp } accept
        meta nfproto ipv4 udp sport 67 udp dport 68 accept
        meta nfproto ipv6 udp sport 547 udp dport 546 accept
        ct state invalid drop
        counter drop
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
''')
write('airootfs/etc/systemd/system/nftables.service.d/90-basaltos.conf', '''[Service]
RemainAfterExit=yes
ExecStartPre=/usr/bin/nft -c -f /etc/nftables.conf
ExecReload=
ExecReload=/usr/bin/nft -f /etc/nftables.conf
ExecStop=
ExecStop=/usr/bin/nft destroy table inet basaltos_filter
''')
write('airootfs/etc/systemd/system/NetworkManager.service.d/90-basaltos-firewall.conf', '''[Unit]
Requires=nftables.service
After=nftables.service
''')
write('airootfs/etc/systemd/resolved.conf.d/90-basaltos-security.conf', '''[Resolve]
LLMNR=no
MulticastDNS=no
''')
write('airootfs/etc/NetworkManager/conf.d/90-basaltos-privacy.conf', '''[connectivity]
enabled=false
uri=
interval=0
''')
write('airootfs/etc/xdg/KDE/UserFeedback.conf', '''[UserFeedback]
Enabled=false
''')
write('airootfs/etc/systemd/system/basaltos-update-check.service', '''[Unit]
Description=Check Arch updates without installing packages
Wants=network-online.target
After=network-online.target
ConditionPathExists=!/run/archiso/bootmnt

[Service]
Type=oneshot
ExecStart=/usr/bin/python /usr/lib/basaltos/check-updates.py
CacheDirectory=basaltos-update-check
StateDirectory=basaltos-update-check
UMask=0022
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
# GnuPG may lock/update trust while verifying repository signatures.
ReadWritePaths=-/etc/pacman.d/gnupg
TimeoutStartSec=10min
''')
write('airootfs/etc/systemd/system/basaltos-update-check.timer', '''[Unit]
Description=Weekly update notification (never automatic installation)

[Timer]
OnCalendar=weekly
Persistent=true
RandomizedDelaySec=30min
Unit=basaltos-update-check.service

[Install]
WantedBy=timers.target
''')
write('airootfs/etc/xdg/autostart/basaltos-update-notifier.desktop', '''[Desktop Entry]
Type=Application
Name=BasaltOS 更新提醒
Exec=/usr/bin/python /usr/lib/basaltos/update-notifier.py
Icon=system-software-update
OnlyShowIn=KDE;
X-KDE-autostart-phase=2
''')
links = json.loads((root/'scripts/profile-symlinks.json').read_text())
links.update({
    'airootfs/etc/systemd/system/multi-user.target.wants/nftables.service': '/usr/lib/systemd/system/nftables.service',
    'airootfs/etc/systemd/system/timers.target.wants/basaltos-update-check.timer': '../basaltos-update-check.timer',
    'airootfs/etc/systemd/system/avahi-daemon.service': '/dev/null',
    'airootfs/etc/systemd/system/avahi-daemon.socket': '/dev/null',
})
for name, target in links.items():
    if not (profile/name).exists() and not (profile/name).is_symlink():
        write(name, target+'\n')
(root/'scripts/profile-symlinks.json').write_text(json.dumps(links, indent=2)+'\n', newline='\n')
text = (profile/'profiledef.sh').read_text().replace('M4 Gaming Live ISO', 'M5 Security Live ISO')
text = text.replace('file_permissions=(\n', 'file_permissions=(\n  ["/usr/bin/basaltos-update"]="0:0:755"\n')
write('profiledef.sh', text)
subprocess.run([sys.executable, str(root/'scripts/check-m5-baseline.py')], check=True)
print('M5 security defaults configured.')
