#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/build-m4.log) 2>&1
trap 'curl -fsS -T /tmp/build-m4.log http://10.0.2.2:8181/work/m4/build-vm.log || true' EXIT
mountpoint -q /mnt || mount /dev/sda1 /mnt
native=/mnt/root/BasaltOS/work/m4-native
mkdir -p "$native"
mountpoint -q "$native" || mount /dev/disk/by-label/BASALT_M4_WORK "$native"
[[ "$(findmnt -nro FSTYPE "$native")" == ext4 ]] || exit 1
source_dir="$(mktemp -d "$native/m4-source.XXXXXXXX")"
curl -fsS http://10.0.2.2:8181/work/m4-source.tar | tar -xf - -C "$source_dir"
guest_source="${source_dir#/mnt}"
echo "M4 source: $guest_source"
for script in "$source_dir"/scripts/*.sh "$source_dir"/profile/airootfs/usr/local/lib/basaltos/*.sh; do
    bash -n "$script"
done
arch-chroot /mnt python "$guest_source/scripts/check-m4-baseline.py"
arch-chroot /mnt bash "$guest_source/scripts/setup-builder.sh"
if [[ ! -f /mnt/root/BasaltOS/work/calamares-package/basaltos-local.db ]]; then
    arch-chroot /mnt bash "$guest_source/scripts/build-calamares.sh"
fi
schema_source=/var/tmp/basaltos-calamares/src/calamares-3.4.3
if [[ -d "/mnt$schema_source" ]]; then
    arch-chroot /mnt python "$guest_source/scripts/validate-calamares.py" "$schema_source"
fi
arch-chroot /mnt env BASALT_MILESTONE=m4 \
    BASALT_BUILD_ROOT=/root/BasaltOS/work/m4-native/linux-build \
    BASALT_OUT_DIR=/root/BasaltOS/work/m4-native/out \
    BASALT_LOCAL_REPO=/root/BasaltOS/work/calamares-package \
    bash "$guest_source/scripts/build.sh"
for artifact in "$native"/out/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/m4/$(basename "$artifact")"
done
echo '=== M4_BUILD_EXPORTED ==='
