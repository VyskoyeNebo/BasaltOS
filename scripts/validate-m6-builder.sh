#!/usr/bin/env bash
set -euo pipefail
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d /root/BasaltOS/work/m6-check.XXXXXXXX)
cp "$project/profile/airootfs/etc/pacman.conf" "$work/pacman.conf"
printf '\n[basaltos]\nSigLevel = Required\nServer = file:///root/BasaltOS/work/m4-native/repo-m6/x86_64\n' >> "$work/pacman.conf"
before=$(sha256sum /etc/pacman.conf /etc/pacman.d/gnupg/pubring.gpg /etc/pacman.d/gnupg/trustdb.gpg)
unshare --mount bash -c 'mount --bind "$1" /etc/pacman.conf; python "$2"' bash \
    "$work/pacman.conf" "$project/profile/airootfs/usr/lib/basaltos/check-only.py"
after=$(sha256sum /etc/pacman.conf /etc/pacman.d/gnupg/pubring.gpg /etc/pacman.d/gnupg/trustdb.gpg)
[[ "$before" == "$after" ]] || { echo 'FAIL: real config/keyring changed'; exit 1; }
echo 'M6 check-only isolated validation passed; real config/keyring unchanged.'
