#!/usr/bin/env bash
# Only for a newly created, dedicated 64 GiB VirtualBox M4 work disk.
set -euo pipefail
(( EUID == 0 )) || exit 1
disk="${1:-}"
expected_serial="${2:-}"
[[ "${3:-}" == --initialize-empty-m4-work-disk ]] || exit 1
[[ "$disk" == /dev/sdb && "$expected_serial" =~ ^VB[0-9a-f]{8}-[0-9a-f]{8}$ ]] || exit 1
[[ "$(systemd-detect-virt)" == oracle ]] || exit 1
[[ "$(lsblk -dnro SERIAL "$disk" | xargs)" == "$expected_serial" ]] || exit 1
[[ "$(blockdev --getsize64 "$disk")" == 68719476736 ]] || exit 1
[[ "$(lsblk -nrpo NAME "$disk" | wc -l)" == 1 ]] || exit 1
[[ -z "$(lsblk -nrpo MOUNTPOINTS "$disk" | tr -d '[:space:]')" ]] || exit 1
[[ -z "$(wipefs --noheadings --output TYPE "$disk")" ]] || { echo 'Disk is not blank.' >&2; exit 1; }
mkfs.ext4 -L BASALT_M4_WORK "$disk"
udevadm trigger --action=change "/sys/class/block/${disk##*/}"
udevadm settle
echo 'New dedicated M4 work disk initialized.'
