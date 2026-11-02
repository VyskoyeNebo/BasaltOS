#!/usr/bin/env bash
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/build-desktop-fix.log) 2>&1
trap 'curl -fsS -T /tmp/build-desktop-fix.log http://10.0.2.2:8181/work/desktop-fix/build-vm.log || true' EXIT
mountpoint -q /mnt || mount /dev/sda1 /mnt
native=/mnt/root/BasaltOS/work/m4-native
mountpoint -q "$native" || mount /dev/disk/by-label/BASALT_M4_WORK "$native"
[[ "$(findmnt -nro FSTYPE "$native")" == ext4 ]] || exit 1
source_dir=$(mktemp -d "$native/desktop-source.XXXXXXXX")
curl -fsS http://10.0.2.2:8181/work/desktop-fix-source.tar | tar -xf - -C "$source_dir"
guest=${source_dir#/mnt}
arch-chroot /mnt python "$guest/scripts/check-desktop-fix.py"
bash -n "$source_dir/profile/airootfs/usr/bin/basaltos-desktop-shortcuts"
arch-chroot /mnt bash "$guest/scripts/setup-builder.sh"
arch-chroot /mnt pacman -S --needed --noconfirm desktop-file-utils
for name in computer trash files settings; do
    arch-chroot /mnt desktop-file-validate "$guest/profile/airootfs/etc/skel/Desktop/basaltos-$name.desktop"
done
arch-chroot /mnt env BASALT_REPO_DIR=/root/BasaltOS/work/m4-native/repo-0.1.1-verified/x86_64 bash "$guest/scripts/build-repo.sh"
arch-chroot /mnt env BASALT_MILESTONE=m6 \
    BASALT_BUILD_ROOT=/root/BasaltOS/work/m4-native/linux-build \
    BASALT_OUT_DIR=/root/BasaltOS/work/m4-native/out-0.1.1-verified \
    BASALT_LOCAL_REPO=/root/BasaltOS/work/m4-native/repo-0.1.1-verified/x86_64 \
    bash "$guest/scripts/build.sh"
iso=$(find "$native/out-0.1.1-verified" -maxdepth 1 -name 'basaltos-*.iso' -type f -print -quit)
arch-chroot /mnt env BASALT_REPO_DIR=/root/BasaltOS/work/m4-native/repo-0.1.1-verified/x86_64 \
    BASALT_RELEASE_DIR=/root/BasaltOS/work/m4-native/release-0.1.1-verified \
    bash "$guest/scripts/release.sh" 0.1.1 --existing-iso "${iso#/mnt}"
for artifact in "$native"/out-0.1.1-verified/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/desktop-fix/$(basename "$artifact")"
done
for artifact in "$native"/release-0.1.1-verified/*; do
    curl -f --retry 3 -T "$artifact" "http://10.0.2.2:8181/out/releases/0.1.1/$(basename "$artifact")"
done
echo '=== BASALTOS_0.1.1_BUILD_AND_RELEASE_EXPORTED ==='
