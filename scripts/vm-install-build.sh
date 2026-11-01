#!/usr/bin/env bash
# Run ONLY in the dedicated BasaltOS-M1-builder VM booted from the official Arch ISO.
set -euo pipefail
exec > >(tee /dev/ttyS0 /tmp/basaltos-builder.log) 2>&1
bridge=http://10.0.2.2:8181
trap 'status=$?; curl -fsS -T /tmp/basaltos-builder.log "$bridge/work/vm-install-build.log" || true; exit "$status"' EXIT
echo '=== BasaltOS dedicated Arch VM installation ==='
[[ "$(cat /sys/class/dmi/id/product_name)" == 'VirtualBox' ]]
[[ "$(blockdev --getsize64 /dev/sda)" == 42949672960 ]]
[[ -z "$(lsblk -n -o FSTYPE /dev/sda | tr -d '[:space:]')" ]] || {
    echo 'Disk is not blank; refusing automatic format.'; exit 1;
}
printf '%s\n' 'Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
timedatectl set-ntp true
printf 'label: dos\n, , 83, *\n' | sfdisk /dev/sda
mkfs.ext4 -L basalt-build /dev/sda1
mount /dev/sda1 /mnt
pacstrap -K /mnt base linux grub archiso python qemu-base
genfstab -U /mnt >> /mnt/etc/fstab
echo basaltos-builder > /mnt/etc/hostname
ln -sf /usr/share/zoneinfo/Asia/Shanghai /mnt/etc/localtime
printf 'en_US.UTF-8 UTF-8\n' > /mnt/etc/locale.gen
echo LANG=en_US.UTF-8 > /mnt/etc/locale.conf
mkdir -p /mnt/etc/systemd/network
printf '[Match]\nType=ether\n\n[Network]\nDHCP=yes\n' > /mnt/etc/systemd/network/20-wired.network
arch-chroot /mnt locale-gen
arch-chroot /mnt systemctl enable systemd-networkd systemd-resolved
ln -sf /run/systemd/resolve/stub-resolv.conf /mnt/etc/resolv.conf
arch-chroot /mnt grub-install --target=i386-pc /dev/sda
arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg
mkdir -p /mnt/root/BasaltOS
curl -fsS "$bridge/work/source.tar" | tar -xf - -C /mnt/root/BasaltOS
# arch-chroot supplies the live environment's working resolver during the build.
arch-chroot /mnt bash /root/BasaltOS/scripts/setup-builder.sh
arch-chroot /mnt bash /root/BasaltOS/scripts/build.sh
for artifact in /mnt/root/BasaltOS/out/*; do
    curl -f --retry 3 -T "$artifact" "$bridge/out/$(basename "$artifact")"
done
echo '=== BUILD_AND_EXPORT_OK ==='
arch-chroot /mnt bash /root/BasaltOS/scripts/verify-qemu.sh
