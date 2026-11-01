#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
printf '%s\n' 'Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
pacman -Syu --needed --noconfirm archiso python
pacman -Q archiso
