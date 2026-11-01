#!/usr/bin/env python3
"""Add installer configuration without changing M2 desktop or M1 identity defaults."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
profile = root / 'profile'

def write(relative, text):
    path = profile / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')

packages = (profile / 'packages.x86_64').read_text().splitlines()
packages += 'calamares grub efibootmgr dosfstools btrfs-progs cryptsetup squashfs-tools snapper snap-pac rsync sudo python python-yaml parted gptfdisk'.split()
write('packages.x86_64', '\n'.join(dict.fromkeys(packages))+'\n')
write('airootfs/etc/calamares/settings.conf', '''---
modules-search: [ local ]
sequence:
  - show: [ welcome, locale, keyboard, partition, users, summary ]
  - exec:
      - partition
      - mount
      - unpackfs
      - machineid
      - fstab
      - locale
      - keyboard
      - localecfg
      - users
      - networkcfg
      - hwclock
      - shellprocess
      - bootloader
      - umount
  - show: [ finished ]
branding: basaltos
prompt-install: true
dont-chroot: false
oem-setup: false
disable-cancel: false
disable-cancel-during-exec: true
quit-at-end: false
''')
configs = {
'welcome': '''showSupportUrl: false
showKnownIssuesUrl: false
showReleaseNotesUrl: false
showDonateUrl: false
requirements:
  requiredStorage: 20
  requiredRam: 2
  check: [ storage, ram, root, screen ]
  required: [ storage, ram, root ]
geoip:
  style: none
  url: https://mirrors.tuna.tsinghua.edu.cn/
  selector: CountryCode
''',
'locale': '''region: Asia
zone: Shanghai
geoip:
  style: none
  url: https://mirrors.tuna.tsinghua.edu.cn/
  selector: TimeZone
''',
'keyboard': '''xOrgConfFileName: /etc/X11/xorg.conf.d/00-keyboard.conf
convertedKeymapPath: /usr/share/kbd/keymaps/xkb
guessLayout: false
useLocale1: false
writeEtcDefaultKeyboard: false
configure:
  kwin: false
''',
'partition': '''efi:
  mountPoint: /boot/efi
  recommendedSize: 512MiB
  minimumSize: 300MiB
  label: BASALT_EFI
userSwapChoices: [ none ]
initialSwapChoice: none
initialPartitioningChoice: erase
defaultPartitionTableType: gpt
createHybridBootloaderLayout: true
defaultFileSystemType: btrfs
availableFileSystemTypes: [ btrfs ]
enableLuksAutomatedPartitioning: true
preCheckEncryption: false
luksGeneration: luks2
allowManualPartitioning: true
showNotEncryptedBootMessage: true
lvm:
  enable: false
partitionLayout:
  - name: basalt-boot
    filesystem: ext4
    noEncrypt: true
    mountPoint: /boot
    size: 1536M
    minSize: 1024M
  - name: basalt-root
    filesystem: btrfs
    mountPoint: /
    size: 100%
    minSize: 16G
''',
'mount': '''extraMounts:
  - { device: proc, fs: proc, mountPoint: /proc }
  - { device: sys, fs: sysfs, mountPoint: /sys }
  - { device: /dev, mountPoint: /dev, options: [ bind ] }
  - { device: tmpfs, fs: tmpfs, mountPoint: /run }
  - { device: /run/udev, mountPoint: /run/udev, options: [ bind ] }
  - { device: efivarfs, fs: efivarfs, mountPoint: /sys/firmware/efi/efivars, efi: true }
btrfsSubvolumes:
  - { mountPoint: /, subvolume: /@ }
  - { mountPoint: /home, subvolume: /@home }
  - { mountPoint: /var/log, subvolume: /@log }
  - { mountPoint: /var/cache, subvolume: /@cache }
mountOptions:
  - { filesystem: default, options: [ defaults ] }
  - { filesystem: efi, options: [ defaults, umask=0077 ] }
  - { filesystem: btrfs, options: [ defaults, compress=zstd:1, noatime ] }
''',
'unpackfs': '''unpack:
  - source: /run/archiso/bootmnt/basalt/x86_64/airootfs.sfs
    sourcefs: squashfs
    destination: ""
''',
'users': '''defaultGroups: [ users, wheel, video, audio, network, storage ]
autologinGroup: autologin
sudoersGroup: wheel
sudoersConfigureWithGroup: true
setRootPassword: true
doReusePassword: true
displayAutologin: false
doAutologin: false
allowWeakPasswords: true
allowWeakPasswordsDefault: false
user:
  shell: /bin/bash
  forbidden_names: [ root ]
  home_permissions: o700
hostname:
  location: EtcFile
  writeHostsFile: true
  template: basaltos
allowActiveDirectory: false
''',
'shellprocess': '''dontChroot: false
timeout: 1200
verbose: true
script:
  - /bin/bash /usr/local/lib/basaltos/finalize-installed.sh
i18n:
  name: Configure BasaltOS and snapshots
  name[zh_CN]: 配置 BasaltOS 与系统快照
''',
'bootloader': '''efiBootLoader: grub
grubInstall: grub-install
grubMkconfig: grub-mkconfig
grubCfg: /boot/grub/grub.cfg
grubProbe: grub-probe
efiBootMgr: efibootmgr
installEFIFallback: true
installHybridGRUB: true
''',
'finished': '''restartNowMode: user-unchecked
restartNowCommand: systemctl -i reboot
notifyOnFinished: false
''',
}
for name, content in configs.items():
    write(f'airootfs/etc/calamares/modules/{name}.conf', '---\n'+content)
write('airootfs/usr/share/calamares/branding/basaltos/branding.desc', '''---
componentName: basaltos
welcomeStyleCalamares: false
welcomeExpandingLogo: false
windowExpanding: normal
windowSize: 1000px,680px
windowPlacement: center
sidebar: widget
navigation: widget
strings:
  productName: BasaltOS
  shortProductName: BasaltOS
  version: M3
  shortVersion: M3
  versionedName: BasaltOS M3
  shortVersionedName: BasaltOS M3
  bootloaderEntryName: BasaltOS
images:
  productIcon: /usr/share/icons/breeze/devices/64/computer.svg
  productLogo: /usr/share/icons/breeze/devices/64/computer.svg
  productWelcome: /usr/share/wallpapers/Next/contents/images/5120x2880.png
style:
  SidebarBackground: "#eff0f1"
  SidebarText: "#232629"
  SidebarTextCurrent: "#ffffff"
  SidebarBackgroundCurrent: "#3daee9"
''')
desktop = '''[Desktop Entry]
Type=Application
Name=Install BasaltOS
Name[zh_CN]=安装 BasaltOS
Comment=Install BasaltOS to a disk
Comment[zh_CN]=将 BasaltOS 安装到硬盘
Exec=/usr/local/bin/install-basaltos
Icon=system-software-install
Terminal=false
Categories=System;
'''
write('airootfs/usr/share/applications/install-basaltos.desktop', desktop)
write('airootfs/root/Desktop/install-basaltos.desktop', desktop)
write('airootfs/root/.config/user-dirs.dirs', 'XDG_DESKTOP_DIR="$HOME/Desktop"\n')
write('airootfs/usr/local/bin/install-basaltos', '''#!/bin/bash
export LANG=zh_CN.UTF-8
export LC_MESSAGES=zh_CN.UTF-8
export QT_QPA_PLATFORM=xcb
if (( EUID == 0 )); then
    exec calamares -D6
fi
exec pkexec --disable-internal-agent /usr/bin/env DISPLAY="$DISPLAY" XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" LANG="$LANG" QT_QPA_PLATFORM=xcb calamares -D6
''')
# Carry the verified M2 desktop/input defaults into newly created users.
for source in (profile / 'airootfs/root/.config').rglob('*'):
    if source.is_file():
        write('airootfs/etc/skel/.config/'+source.relative_to(profile / 'airootfs/root/.config').as_posix(), source.read_text(encoding='utf-8'))
konsole_profile = profile / 'airootfs/root/.local/share/konsole/BasaltOS.profile'
write('airootfs/etc/skel/.local/share/konsole/BasaltOS.profile', konsole_profile.read_text(encoding='utf-8'))
write('airootfs/etc/motd', 'BasaltOS M3 — KDE Plasma Live ISO with Calamares\n')
os_release = (profile / 'airootfs/etc/os-release').read_text().replace('BasaltOS M2', 'BasaltOS M3')
write('airootfs/etc/os-release', os_release)
definition = (profile / 'profiledef.sh').read_text().replace('BasaltOS M2 KDE Plasma Live ISO', 'BasaltOS M3 Installer Live ISO')
for path, mode in [('/usr/local/bin/install-basaltos', '755'),('/usr/local/lib/basaltos/finalize-installed.sh','755'),('/root/Desktop/install-basaltos.desktop','755')]:
    if f'["{path}"]' not in definition:
        definition = definition.replace('file_permissions=(\n', f'file_permissions=(\n  ["{path}"]="0:0:{mode}"\n')
write('profiledef.sh', definition)
print('M3 installer configured; M2 desktop and protected M1 defaults preserved.')
