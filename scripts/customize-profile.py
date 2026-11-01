#!/usr/bin/env python3
"""Apply the BasaltOS M1 changes to a newly imported releng profile once."""
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
profile = root / 'profile'
manifest = root / 'scripts/profile-symlinks.json'
links = json.loads(manifest.read_text())

def write(relative, content):
    path = profile / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        path.unlink()
    path.write_text(content, encoding='utf-8', newline='\n')

def remove(relative):
    path = profile / relative
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
    for key in list(links):
        if key == relative or key.startswith(relative + '/'):
            del links[key]

def link(relative, target):
    write(relative, target)
    links[relative] = target

write('profiledef.sh', '''#!/usr/bin/env bash
# shellcheck disable=SC2034
iso_name="basaltos"
iso_label="basaltos"
iso_publisher="BasaltOS"
iso_application="BasaltOS M1 Command Line Live ISO"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="basalt"
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
)
''')
write('packages.x86_64', '''amd-ucode
arch-install-scripts
base
ca-certificates
curl
dhcpcd
ethtool
intel-ucode
iproute2
iputils
iw
iwd
less
linux
linux-firmware
mkinitcpio
mkinitcpio-archiso
nano
pciutils
syslinux
systemd-resolvconf
usbutils
wireless-regdb
''')
remove('packages.aarch64')
remove('bootstrap_packages')
mirror = 'Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch\n'
pacman = '''[options]
Architecture = auto
HoldPkg = pacman glibc
ParallelDownloads = 5
SigLevel = Required DatabaseOptional
LocalFileSigLevel = Optional

[core]
'''+mirror+'''\n[extra]
'''+mirror
write('pacman.conf', pacman)
write('airootfs/etc/pacman.conf', pacman)
write('airootfs/etc/pacman.d/mirrorlist', mirror)
remove('airootfs/etc/pacman.d/hooks/uncomment-mirrors.hook')
write('airootfs/etc/hostname', 'basaltos\n')
write('airootfs/etc/locale.conf', 'LANG=zh_CN.UTF-8\n')
write('airootfs/etc/locale.gen', 'en_US.UTF-8 UTF-8\nzh_CN.UTF-8 UTF-8\n')
write('airootfs/etc/vconsole.conf', 'KEYMAP=us\n')
link('airootfs/etc/localtime', '/usr/share/zoneinfo/Asia/Shanghai')
write('airootfs/etc/passwd', 'root:x:0:0:root:/root:/usr/bin/bash\n')
write('airootfs/etc/motd', 'BasaltOS M1 — Command Line Live ISO\n')
write('airootfs/etc/os-release', '''NAME="BasaltOS"
PRETTY_NAME="BasaltOS M1"
ID=basaltos
ID_LIKE=arch
BUILD_ID=rolling
ANSI_COLOR="1;36"
''')
write('airootfs/etc/pacman.d/hooks/40-basaltos-locale.hook', '''# remove from airootfs!
[Trigger]
Operation = Install
Operation = Upgrade
Type = Package
Target = glibc

[Action]
Description = Generating BasaltOS UTF-8 locales...
When = PostTransaction
Depends = glibc
Exec = /usr/bin/locale-gen
''')
write('airootfs/etc/mkinitcpio.conf.d/archiso.conf', '''HOOKS=(base udev microcode modconf memdisk archiso archiso_loop_mnt block filesystems keyboard)
COMPRESSION="xz"
COMPRESSION_OPTIONS=(-6)
''')
keep_services = {
    'dbus-org.freedesktop.network1.service',
    'dbus-org.freedesktop.resolve1.service',
    'dbus-org.freedesktop.timesync1.service',
    'systemd-networkd.service', 'systemd-networkd.socket',
    'systemd-networkd-wait-online.service', 'systemd-resolved.service',
    'systemd-timesyncd.service', 'systemd-time-wait-sync.service',
    'iwd.service', 'pacman-init.service',
}
for relative in list(links):
    if relative.startswith('airootfs/etc/systemd/system/') and Path(relative).name not in keep_services:
        remove(relative)
for relative in (
    'airootfs/etc/systemd/system/choose-mirror.service',
    'airootfs/etc/systemd/system/livecd-alsa-unmuter.service',
    'airootfs/etc/systemd/system/livecd-talk.service',
    'airootfs/etc/ssh', 'airootfs/usr/local',
    'airootfs/root/.zlogin', 'airootfs/root/.automated_script.sh', 'airootfs/root/.gnupg',
    'efiboot/loader/entries/02-archiso-speech-linux.conf',
):
    remove(relative)
for path in (profile / 'efiboot/loader/entries').glob('*memtest*'):
    remove(path.relative_to(profile).as_posix())
write('airootfs/etc/systemd/system/serial-getty@ttyS0.service.d/autologin.conf', '''[Service]
ExecStart=
ExecStart=-/usr/bin/agetty --autologin root --noclear --keep-baud 115200,38400,9600 - $TERM
''')
write('syslinux/archiso_head.cfg', '''SERIAL 0 115200
UI menu.c32
MENU TITLE BasaltOS
MENU CLEAR
''')
write('syslinux/archiso_sys-linux.cfg', '''LABEL basaltos
MENU LABEL BasaltOS
LINUX /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux
INITRD /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux.img
APPEND archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID% console=ttyS0,115200 console=tty0 %KERNEL_PARAMS%
''')
write('syslinux/archiso_sys.cfg', '''INCLUDE archiso_head.cfg
DEFAULT basaltos
TIMEOUT 30
INCLUDE archiso_sys-linux.cfg
''')
remove('syslinux/splash.png')
remove('syslinux/archiso_pxe-linux.cfg')
remove('syslinux/archiso_pxe.cfg')
remove('syslinux/archiso_tail.cfg')
write('syslinux/syslinux.cfg', 'DEFAULT basaltos\nINCLUDE archiso_sys.cfg\n')
write('efiboot/loader/entries/01-archiso-linux.conf', '''title    BasaltOS
sort-key 01
linux    /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux
initrd   /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux.img
options  archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID% console=ttyS0,115200 console=tty0 %KERNEL_PARAMS%
''')
write('efiboot/loader/loader.conf', 'default 01-archiso-linux.conf\ntimeout 3\nconsole-mode keep\n')
# Keep upstream GRUB templates for loopback booting, with BasaltOS branding.
for path in (profile / 'grub').glob('*.cfg'):
    text = path.read_text().replace('Arch Linux install medium', 'BasaltOS').replace('Arch Linux', 'BasaltOS')
    path.write_text(text, encoding='utf-8', newline='\n')
manifest.write_text(json.dumps(links, indent=2, sort_keys=True)+'\n', encoding='utf-8')
print(f'BasaltOS M1 profile ready; {len(links)} symbolic links retained')
