#!/usr/bin/env python3
"""Add the gaming layer; leave M3 installation and boot settings intact."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
profile = root / 'profile'
subprocess.run([sys.executable, str(root / 'scripts/check-m4-baseline.py')], check=True)

def write(relative, text):
    path = profile / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')

for relative in ('pacman.conf', 'airootfs/etc/pacman.conf'):
    path = profile / relative
    config = path.read_text()
    if '[multilib]' not in config:
        config += '\n[multilib]\nServer = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch\n'
    write(relative, config)

packages = (profile / 'packages.x86_64').read_text().splitlines()
packages += '''steam steam-devices lutris gamescope mangohud lib32-mangohud
gamemode lib32-gamemode vulkan-icd-loader lib32-vulkan-icd-loader mesa lib32-mesa
vulkan-radeon lib32-vulkan-radeon vulkan-intel lib32-vulkan-intel
vulkan-swrast lib32-vulkan-swrast wine-staging winetricks vulkan-tools mesa-utils'''.split()
write('packages.x86_64', '\n'.join(dict.fromkeys(p for p in packages if p))+'\n')

write('airootfs/etc/skel/.config/MangoHud/MangoHud.conf', '''# BasaltOS gaming defaults; unsupported sensors may be unavailable in VMs.
fps
frametime
frame_timing
cpu_stats
cpu_temp
gpu_stats
gpu_temp
ram
vram
gamemode
position=top-left
font_size=22
background_alpha=0.45
toggle_hud=Shift_R+F12
''')

for name, icon, command, title in (
    ('steam', 'steam', 'steam %U', 'Steam'),
    ('lutris', 'lutris', 'lutris %U', 'Lutris'),
):
    entry = f'''[Desktop Entry]
Type=Application
Name={title}
Exec={command}
Icon={icon}
Terminal=false
Categories=Game;
'''
    write(f'airootfs/etc/skel/Desktop/{name}.desktop', entry)

# Enable the package's user service for all user managers, including new users.
relative = 'airootfs/etc/systemd/user/default.target.wants/gamemoded.service'
target = '/usr/lib/systemd/user/gamemoded.service'
links_path = root / 'scripts/profile-symlinks.json'
links = json.loads(links_path.read_text())
links[relative] = target
links_path.write_text(json.dumps(links, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
path = profile / relative
path.parent.mkdir(parents=True, exist_ok=True)
if path.is_symlink():
    path.unlink()
write(relative, target)

# The account is created in the Live overlay, never in the squashfs installed
# by Calamares. Installed users continue to come from the M3 users module.
write('airootfs/usr/local/lib/basaltos/gaming-accounts.sh', '''#!/usr/bin/env bash
set -euo pipefail
if [[ -d /run/archiso/bootmnt ]]; then
  if ! id gamer >/dev/null 2>&1; then
    groups=()
    for group in wheel video audio network storage input render gamemode; do
        if getent group "$group" >/dev/null; then groups+=("$group"); fi
    done
    extra_groups="$(IFS=,; echo "${groups[*]}")"
    useradd --create-home --user-group --uid 1000 --groups "$extra_groups" --shell /usr/bin/bash gamer
    printf 'gamer:basaltos\\n' | chpasswd
  fi
  install -d -o gamer -g gamer /home/gamer/Desktop
  install -o gamer -g gamer -m755 /root/Desktop/install-basaltos.desktop /home/gamer/Desktop/install-basaltos.desktop
  chmod 755 /home/gamer/Desktop/steam.desktop /home/gamer/Desktop/lutris.desktop
fi
# The official policy grants CPU/GPU helpers to this group. Apply before SDDM
# opens a session so installed users receive the supplementary group at login.
if getent group gamemode >/dev/null; then
    while IFS=: read -r name _ uid _ _ _ _; do
        if (( uid >= 1000 && uid < 60000 )); then
            usermod --append --groups gamemode "$name"
        fi
    done < /etc/passwd
fi
''')
write('airootfs/etc/systemd/system/basaltos-gaming-accounts.service', '''[Unit]
Description=Prepare BasaltOS gaming accounts
After=systemd-sysusers.service
Before=display-manager.service

[Service]
Type=oneshot
ExecStart=/bin/bash /usr/local/lib/basaltos/gaming-accounts.sh
RemainAfterExit=yes
''')
write('airootfs/etc/systemd/system/sddm.service.d/20-basaltos-gaming-accounts.conf', '''[Unit]
Wants=basaltos-gaming-accounts.service
After=basaltos-gaming-accounts.service
''')
write('airootfs/etc/sddm.conf.d/20-basaltos-gaming.conf', '''[Users]
MinimumUid=1000
MaximumUid=60000
''')
write('airootfs/var/lib/sddm/state.conf', '''[Last]
User=gamer
Session=/usr/share/wayland-sessions/plasma.desktop
''')

definition = (profile / 'profiledef.sh').read_text()
definition = definition.replace('BasaltOS M3 Installer Live ISO', 'BasaltOS M4 Gaming Live ISO')
for name in ('steam', 'lutris'):
    path = f'/etc/skel/Desktop/{name}.desktop'
    if f'["{path}"]' not in definition:
        definition = definition.replace('file_permissions=(\n', f'file_permissions=(\n  ["{path}"]="0:0:755"\n')
write('profiledef.sh', definition)
os_release = (profile / 'airootfs/etc/os-release').read_text().replace('BasaltOS M3', 'BasaltOS M4')
write('airootfs/etc/os-release', os_release)
write('airootfs/etc/motd', 'BasaltOS M4 — KDE Plasma Gaming Live ISO\n')
subprocess.run([sys.executable, str(root / 'scripts/check-m4-baseline.py')], check=True)
