#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/m6-release-export.log) 2>&1
trap 'curl -fsS -T /tmp/m6-release-export.log http://10.0.2.2:8181/work/m6/release-export.log || true' EXIT
source=${1:?Usage: export-m6-release.sh /mnt/root/BasaltOS/work/m4-native/m6-source.XXXXXXXX}
[[ "$source" == /mnt/root/BasaltOS/work/m4-native/m6-source.* && -d "$source/scripts" ]] || exit 1
pages=$(mktemp -d /mnt/root/BasaltOS/work/m4-native/pages-m6-check.XXXXXXXX)
rmdir "$pages"
curl -fsS http://10.0.2.2:8181/scripts/prepare-pages.py -o "$source/scripts/prepare-pages.py"
arch-chroot /mnt python "${source#/mnt}/scripts/prepare-pages.py" --version 0.1.0-m6 \
  --release-dir /root/BasaltOS/work/m4-native/release-m6-split/0.1.0-m6 \
  --output "${pages#/mnt}" > /tmp/m6-pages-final.log 2>&1
curl -fsS -T /tmp/m6-pages-final.log http://10.0.2.2:8181/work/m6/pages-verify.log
for file in /mnt/root/BasaltOS/work/m4-native/release-m6-split/0.1.0-m6/*; do
    [[ "$file" != *.iso ]] || continue
    curl -f --retry 3 -T "$file" "http://10.0.2.2:8181/out/releases/0.1.0-m6/$(basename "$file")"
done
echo '=== M6_SPLIT_RELEASE_EXPORTED ==='
