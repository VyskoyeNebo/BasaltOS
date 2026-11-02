#!/usr/bin/env bash
set -euo pipefail
key=/usr/share/basaltos/keys/basaltos-key.asc
expected=$(tr -d '\r\n' < /usr/share/basaltos/keys/basaltos-key.fingerprint)
temporary=$(mktemp -d)
trap 'rm -rf -- "$temporary"' EXIT
chmod 700 "$temporary"
actual=$(gpg --homedir "$temporary" --batch --with-colons --show-keys "$key" | awk -F: '$1=="fpr" {print $10;exit}')
[[ "$actual" == "$expected" && "$expected" =~ ^[0-9A-F]{40}$ ]] || { echo 'Release public-key fingerprint mismatch.' >&2; exit 1; }
exec 9>/run/lock/basaltos-keyring.lock
flock 9
pacman-key --init
pacman-key --populate archlinux
pacman-key --add "$key"
pacman-key --lsign-key "$expected"
pacman-key --finger "$expected"
