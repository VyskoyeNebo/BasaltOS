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
GreeterEnvironment=QT_QUICK_BACKEND=software

[Theme]
Current=basaltos
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
ColorScheme=BreezeDark

[KDE]
LookAndFeelPackage=org.kde.breezedark.desktop
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
write('airootfs/root/.config/autostart/basaltos-wallpaper.desktop', '''[Desktop Entry]
Type=Application
Name=BasaltOS wallpaper
Exec=/usr/bin/plasma-apply-wallpaperimage /usr/share/backgrounds/basaltos/m2.svg
TryExec=/usr/bin/plasma-apply-wallpaperimage
OnlyShowIn=KDE;
X-KDE-autostart-phase=2
StartupNotify=false
''')
write('airootfs/usr/share/backgrounds/basaltos/m2.svg', '''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
<defs><linearGradient id="sky" x2="1" y2="1"><stop stop-color="#081a29"/><stop offset="1" stop-color="#203743"/></linearGradient>
<radialGradient id="sun"><stop stop-color="#e7ab70" stop-opacity=".55"/><stop offset="1" stop-color="#e7ab70" stop-opacity="0"/></radialGradient></defs>
<path fill="url(#sky)" d="M0 0h1920v1080H0z"/><circle cx="1450" cy="330" r="480" fill="url(#sun)"/>
<circle cx="1450" cy="330" r="72" fill="#e6b984"/>
<path fill="#132933" d="M0 760L500 390l260 320 220-140 320 310 310-310 310 200v310H0z"/>
<path fill="#0c2029" d="M0 850l310-200 280 160 380-120 340 240 330-160 280 100v210H0z"/>
<g stroke="#29434c" stroke-width="2" fill="#102833"><path d="M1050 1080V790l70-40 70 40v290M1190 1080V710l70-40 70 40v370M1330 1080V810l70-40 70 40v270M1470 1080V680l70-40 70 40v400M1610 1080V760l70-40 70 40v320M1750 1080V860l70-40 70 40v220"/></g>
<text x="110" y="155" fill="#e7ecec" font-family="sans-serif" font-size="54" letter-spacing="9">BASALTOS</text>
<path stroke="#cf9c6e" stroke-width="4" d="M112 186h92"/>
</svg>
''')
write('airootfs/usr/share/sddm/themes/basaltos/metadata.desktop', '''[SddmGreeterTheme]
Name=BasaltOS
Description=BasaltOS Live login
Author=BasaltOS
Type=sddm-theme
Version=1.0
MainScript=Main.qml
ConfigFile=theme.conf
Theme-API=2.0
QtVersion=6
''')
write('airootfs/usr/share/sddm/themes/basaltos/theme.conf', '[General]\nbackground=/usr/share/backgrounds/basaltos/m2.svg\n')
write('airootfs/usr/share/sddm/themes/basaltos/Main.qml', '''import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: screen
    width: 1280; height: 800
    color: "#10232d"
    function login() { sddm.login(username.text, password.text, Math.max(0, sessions.currentIndex)) }
    Image { anchors.fill: parent; source: config.background; fillMode: Image.PreserveAspectCrop }
    Rectangle {
        anchors.centerIn: parent; width: 390; height: 430; radius: 18
        color: "#e810202b"; border.color: "#45616b"
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 35; spacing: 16
            Label { text: "BasaltOS"; color: "#f2eee8"; font.pixelSize: 34; font.bold: true }
            Label { text: "欢迎进入 Plasma 桌面"; color: "#b4c8cd"; font.pixelSize: 15 }
            Item { Layout.preferredHeight: 5 }
            TextField { id: username; text: "root"; placeholderText: "用户名"; Layout.fillWidth: true }
            TextField {
                id: password; placeholderText: "密码"; echoMode: TextInput.Password
                Layout.fillWidth: true; onAccepted: screen.login()
                Component.onCompleted: forceActiveFocus()
            }
            ComboBox { id: sessions; model: sessionModel; textRole: "name"; currentIndex: Math.max(0, sessionModel.lastIndex); Layout.fillWidth: true }
            Button { text: "登录"; highlighted: true; Layout.fillWidth: true; onClicked: screen.login() }
            Label { id: error; text: "Live 会话 · root"; color: "#b4c8cd"; font.pixelSize: 12 }
        }
    }
    Connections {
        target: sddm
        function onLoginFailed() { error.text = "登录失败，请重试"; password.text = ""; password.forceActiveFocus() }
    }
}
''')
write('airootfs/etc/motd', 'BasaltOS M2 — KDE Plasma Live ISO\n')
os_release = (profile / 'airootfs/etc/os-release').read_text().replace('BasaltOS M1','BasaltOS M2')
write('airootfs/etc/os-release', os_release)
definition = (profile / 'profiledef.sh').read_text().replace('BasaltOS M1 Command Line Live ISO','BasaltOS M2 KDE Plasma Live ISO')
write('profiledef.sh', definition)
manifest.write_text(json.dumps(links, indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')
print('M2 desktop profile configured. Protected M1 hostname/locale/timezone/mirrors untouched.')
