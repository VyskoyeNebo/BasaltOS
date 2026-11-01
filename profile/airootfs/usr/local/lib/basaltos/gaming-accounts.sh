#!/usr/bin/env bash
set -euo pipefail
if [[ -d /run/archiso/bootmnt ]]; then
  if ! id gamer >/dev/null 2>&1; then
    groups=()
    for group in wheel video audio network storage input render gamemode; do
        if getent group "$group" >/dev/null; then groups+=("$group"); fi
    done
    extra_groups="$(IFS=,; echo "${groups[*]}")"
    useradd --create-home --user-group --uid 1000 --groups "$extra_groups" --shell /usr/bin/bash gamer
    printf 'gamer:basaltos\n' | chpasswd
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
