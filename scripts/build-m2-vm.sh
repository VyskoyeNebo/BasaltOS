#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/build-m2.log) 2>&1
trap 'curl -fsS -T /tmp/build-m2.log http://10.0.2.2:8181/work/m2-vm.log || true' EXIT
mountpoint -q /mnt || mount /dev/sda1 /mnt
source_dir="$(mktemp -d /mnt/root/BasaltOS/work/m2-source.XXXXXXXX)"
curl -fsS http://10.0.2.2:8181/work/m2-source.tar | tar -xf - -C "$source_dir"
guest_source="${source_dir#/mnt}"
echo "M2 source: $guest_source"
arch-chroot /mnt bash "$guest_source/scripts/setup-builder.sh"
arch-chroot /mnt env BASALT_MILESTONE=m2 BASALT_BUILD_ROOT=/root/BasaltOS/work/linux-build BASALT_OUT_DIR=/root/BasaltOS/out/m2 bash "$guest_source/scripts/build.sh"
for artifact in /mnt/root/BasaltOS/out/m2/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/m2/$(basename "$artifact")"
done
echo '=== M2_BUILD_EXPORTED ==='
