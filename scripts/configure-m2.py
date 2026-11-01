#!/usr/bin/env python3
"""Extend the M1 profile with Plasma/SDDM/Fcitx while retaining its protected settings."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
profile = root / 'profile'
manifest = root / 'scripts/profile-symlinks.json'
links = json.loads(manifest.read_text())

def write(path, text):
    target = profile / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    target.write_text(text, encoding='utf-8', newline='\n')

def link(path, destination):
    write(path, destination)
    links[path] = destination

def remove(path):
    (profile / path).unlink(missing_ok=True)
    links.pop(path, None)

packages = (profile / 'packages.x86_64').read_text().splitlines()
packages += '''plasma-desktop
sddm
konsole
dolphin
ark
breeze
kscreen
plasma-nm
networkmanager
fcitx5
fcitx5-chinese-addons
fcitx5-configtool
fcitx5-qt
fcitx5-gtk
noto-fonts
noto-fonts-cjk
noto-fonts-emoji
xorg-server
xorg-xauth
xorg-xwayland
mesa
qt6-wayland
pipewire
pipewire-pulse
wireplumber
'''.splitlines()
write('packages.x86_64', '\n'.join(dict.fromkeys(packages))+'\n')
for path in list(links):
    if 'systemd-networkd' in path or 'dbus-org.freedesktop.network1' in path or path.endswith('/iwd.service'):
        remove(path)
link('airootfs/etc/systemd/system/default.target', '/usr/lib/systemd/system/graphical.target')
link('airootfs/etc/systemd/system/display-manager.service', '/usr/lib/systemd/system/sddm.service')
link('airootfs/etc/systemd/system/multi-user.target.wants/NetworkManager.service', '/usr/lib/systemd/system/NetworkManager.service')
link('airootfs/etc/systemd/system/dbus-org.freedesktop.NetworkManager.service', '/usr/lib/systemd/system/NetworkManager.service')
write('airootfs/etc/NetworkManager/conf.d/10-basaltos.conf', '''[main]
dns=systemd-resolved

[device]
wifi.backend=iwd
''')
write('airootfs/etc/shadow', 'root:$6$basaltos-m2$sox.tv65BjIA3Fl0J31sbnfu2hUTT/kQSGAITHmXAC/.7Grs5ZURYTomS.z0aitCcbgFGHcH/t4LyZvc8BAWa0:20758::::::\n')
write('airootfs/etc/sddm.conf.d/10-basaltos.conf', '''[General]
DisplayServer=x11

[Theme]
Current=breeze
CursorTheme=breeze_cursors
Font=Noto Sans CJK SC,11

[Users]
MinimumUid=0
MaximumUid=0
RememberLastUser=true
RememberLastSession=true
''')
write('airootfs/var/lib/sddm/state.conf', '''[Last]
User=root
Session=/usr/share/wayland-sessions/plasma.desktop
''')
write('airootfs/root/.config/autostart/org.fcitx.Fcitx5.desktop', '''[Desktop Entry]
Type=Application
Name=Fcitx 5 (started by KWin on Wayland)
Hidden=true
''')
write('airootfs/root/.config/kwinrc', '''[Wayland]
InputMethod[$e]=/usr/share/applications/fcitx5-wayland-launcher.desktop
VirtualKeyboardEnabled=true
''')
write('airootfs/root/.config/environment.d/90-fcitx5.conf', 'XMODIFIERS=@im=fcitx\n')
write('airootfs/root/.config/fcitx5/profile', '''[Groups/0]
Name=Default
Default Layout=us
DefaultIM=pinyin

[Groups/0/Items/0]
Name=keyboard-us
Layout=

[Groups/0/Items/1]
Name=pinyin
Layout=

[GroupOrder]
0=Default
''')
write('airootfs/root/.config/fcitx5/config', '''[Behavior]
ActiveByDefault=True

[Hotkey/TriggerKeys]
0=Control+space
''')
write('airootfs/root/.config/kdeglobals', '''[General]
ColorScheme=BreezeLight

[KDE]
LookAndFeelPackage=org.kde.breeze.desktop
''')
write('airootfs/root/.config/konsolerc', '''[Desktop Entry]
DefaultProfile=BasaltOS.profile

[KonsoleWindow]
SaveGeometryOnExit=false
''')
write('airootfs/root/.local/share/konsole/BasaltOS.profile', '''[Appearance]
ColorScheme=Breeze
Font=Noto Sans Mono CJK SC,12,-1,5,50,0,0,0,0,0

[General]
Name=BasaltOS
Parent=FALLBACK/
TerminalColumns=105
TerminalRows=28
''')
# Use KDE's packaged Breeze login, standard layout and official Next wallpaper.
for obsolete in (
    'airootfs/root/.config/autostart/basaltos-wallpaper.desktop',
    'airootfs/usr/share/backgrounds/basaltos/m2.svg',
    'airootfs/usr/share/sddm/themes/basaltos/Main.qml',
    'airootfs/usr/share/sddm/themes/basaltos/metadata.desktop',
    'airootfs/usr/share/sddm/themes/basaltos/theme.conf',
):
    remove(obsolete)
write('airootfs/etc/motd', 'BasaltOS M2 — KDE Plasma Live ISO\n')
os_release = (profile / 'airootfs/etc/os-release').read_text().replace('BasaltOS M1','BasaltOS M2')
write('airootfs/etc/os-release', os_release)
definition = (profile / 'profiledef.sh').read_text().replace('BasaltOS M1 Command Line Live ISO','BasaltOS M2 KDE Plasma Live ISO')
write('profiledef.sh', definition)
manifest.write_text(json.dumps(links, indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')
print('M2 desktop profile configured. Protected M1 hostname/locale/timezone/mirrors untouched.')
