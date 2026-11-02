#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/m6-repo.log) 2>&1
trap 'curl -fsS -T /tmp/m6-repo.log http://10.0.2.2:8181/work/m6/repo-build.log || true' EXIT
native=/mnt/root/BasaltOS/work/m4-native
source=$(mktemp -d "$native/m6-source.XXXXXXXX")
curl -fsS http://10.0.2.2:8181/work/m6-source.tar | tar -xf - -C "$source"
guest=${source#/mnt}
arch-chroot /mnt env BASALT_REPO_DIR=/root/BasaltOS/work/m4-native/repo-m6/x86_64 bash "$guest/scripts/build-repo.sh"
arch-chroot /mnt pacman-key --add "$guest/packaging/basaltos-key.asc"
arch-chroot /mnt pacman-key --lsign-key "$(cat "$source/packaging/basaltos-key.fingerprint")"
for file in "$native"/repo-m6/x86_64/*; do
    curl -fsS -T "$file" "http://10.0.2.2:8181/work/m6/repo/x86_64/$(basename "$file")"
done
echo '=== M6_SIGNED_REPO_EXPORTED ==='
