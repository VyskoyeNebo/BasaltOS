#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/build-m6.log) 2>&1
trap 'curl -fsS -T /tmp/build-m6.log http://10.0.2.2:8181/work/m6/build-vm.log || true' EXIT
mountpoint -q /mnt || mount /dev/sda1 /mnt
native=/mnt/root/BasaltOS/work/m4-native
mountpoint -q "$native" || mount /dev/disk/by-label/BASALT_M4_WORK "$native"
[[ "$(findmnt -nro FSTYPE "$native")" == ext4 ]] || exit 1
source_dir=$(mktemp -d "$native/m6-source.XXXXXXXX")
curl -fsS http://10.0.2.2:8181/work/m6-source.tar | tar -xf - -C "$source_dir"
guest=${source_dir#/mnt}
arch-chroot /mnt python "$guest/scripts/check-m6-baseline.py"
for script in "$source_dir"/scripts/*.sh "$source_dir"/profile/airootfs/usr/lib/basaltos/*.sh; do bash -n "$script"; done
arch-chroot /mnt bash "$guest/scripts/setup-builder.sh"
arch-chroot /mnt env BASALT_MILESTONE=m6 \
    BASALT_BUILD_ROOT=/root/BasaltOS/work/m4-native/linux-build \
    BASALT_OUT_DIR=/root/BasaltOS/work/m4-native/out-m6 \
    BASALT_LOCAL_REPO=/root/BasaltOS/work/m4-native/repo-m6/x86_64 \
    bash "$guest/scripts/build.sh"
iso=$(find "$native/out-m6" -maxdepth 1 -name 'basaltos-*.iso' -type f -print -quit)
arch-chroot /mnt env BASALT_REPO_DIR=/root/BasaltOS/work/m4-native/repo-m6/x86_64 \
    BASALT_RELEASE_DIR=/root/BasaltOS/work/m4-native/release-m6/0.1.0-m6 \
    bash "$guest/scripts/release.sh" 0.1.0-m6 --existing-iso "${iso#/mnt}"
for artifact in "$native"/out-m6/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/m6/$(basename "$artifact")"
done
for artifact in "$native"/release-m6/0.1.0-m6/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/releases/0.1.0-m6/$(basename "$artifact")"
done
echo '=== M6_BUILD_AND_RELEASE_EXPORTED ==='
