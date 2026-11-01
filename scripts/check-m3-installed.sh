#!/usr/bin/env bash
# Acceptance check for the dedicated, newly installed M3 QEMU test disk.
# Reinstalls nano through pacman to exercise real snap-pac pre/post hooks.
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root in the installed M3 test VM.' >&2; exit 1; }
[[ "$(lsblk -dnro SERIAL /dev/vda | xargs)" == BASALTOS_M3_TARGET ]] || exit 1
label="${1:-final}"
[[ "$label" =~ ^[a-z0-9-]+$ ]] || exit 1
export LC_ALL=C.UTF-8
log="/tmp/m3-installed-$label.log"
exec > >(tee "$log") 2>&1
trap 'status=$?; curl -fsS -T "$log" "http://10.0.2.2:8181/work/m3/installed-$label.log" || true; exit "$status"' EXIT
hostnamectl --static
[[ "$(hostnamectl --static)" == basaltos ]] || { echo 'Expected the default hostname basaltos.' >&2; exit 1; }
[[ "$(lsblk -dnro FSTYPE /dev/vda4)" == crypto_LUKS ]]
[[ "$(findmnt -nro FSTYPE /)" == btrfs ]]
[[ "$(findmnt -nro FSROOT /)" == /@ ]]
[[ "$(findmnt -nro FSROOT /home)" == /@home ]]
[[ -f /etc/snapper/configs/root && -f /etc/snapper/configs/home ]]
[[ -d /.snapshots/1/snapshot && -d /home/.snapshots/1/snapshot ]]
id
if [[ -d /sys/firmware/efi ]]; then echo BOOT_MODE=UEFI; else echo BOOT_MODE=BIOS; fi
cat /proc/cmdline
lsblk -o NAME,FSTYPE,MOUNTPOINTS /dev/vda
btrfs subvolume list /
snapper -c root list
snapper -c home list
systemctl is-enabled sddm NetworkManager snapper-timeline.timer snapper-cleanup.timer
ip -br a
pgrep -a fcitx5
cat /etc/locale.conf
readlink /etc/localtime
curl -fsSI --max-time 30 https://mirrors.tuna.tsinghua.edu.cn/archlinux/
before=$(find /.snapshots -mindepth 1 -maxdepth 1 -type d | wc -l)
pacman -Syu --noconfirm nano
after=$(find /.snapshots -mindepth 1 -maxdepth 1 -type d | wc -l)
(( after >= before + 2 )) || { echo 'snap-pac did not create both transaction snapshots.' >&2; exit 1; }
snapper -c root list
echo M3_INSTALLED_CHECKS_PASSED
