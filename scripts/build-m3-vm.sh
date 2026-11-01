#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/build-m3.log) 2>&1
trap 'curl -fsS -T /tmp/build-m3.log http://10.0.2.2:8181/work/m3/build-vm.log || true' EXIT
mountpoint -q /mnt || mount /dev/sda1 /mnt
source_dir="$(mktemp -d /mnt/root/BasaltOS/work/m3-source.XXXXXXXX)"
curl -fsS http://10.0.2.2:8181/work/m3-source.tar | tar -xf - -C "$source_dir"
guest_source="${source_dir#/mnt}"
echo "M3 source: $guest_source"
for script in "$source_dir"/scripts/*.sh "$source_dir"/profile/airootfs/usr/local/lib/basaltos/*.sh; do
    bash -n "$script"
done
arch-chroot /mnt bash "$guest_source/scripts/setup-builder.sh"
if [[ ! -f /mnt/root/BasaltOS/work/calamares-package/basaltos-local.db ]]; then
    arch-chroot /mnt bash "$guest_source/scripts/build-calamares.sh"
fi
arch-chroot /mnt python - "$guest_source" <<'PY'
from pathlib import Path
import sys
import yaml
source = Path(sys.argv[1])
for path in (source / 'profile/airootfs/etc/calamares').rglob('*.conf'):
    yaml.safe_load(path.read_text())
print('Calamares YAML and shell syntax checks passed.')
PY
arch-chroot /mnt env BASALT_MILESTONE=m3 \
    BASALT_BUILD_ROOT=/root/BasaltOS/work/linux-build \
    BASALT_OUT_DIR=/root/BasaltOS/out/m3 \
    BASALT_LOCAL_REPO=/root/BasaltOS/work/calamares-package \
    bash "$guest_source/scripts/build.sh"
for artifact in /mnt/root/BasaltOS/out/m3/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/m3/$(basename "$artifact")"
done
echo '=== M3_BUILD_EXPORTED ==='
