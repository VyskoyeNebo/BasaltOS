#!/usr/bin/env bash
# Explicit fallback for M3 acceptance: only formats a fresh, serial-tagged QEMU disk.
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root in the M3 Live VM.' >&2; exit 1; }
disk=/dev/vda
[[ "$(lsblk -dnro SERIAL "$disk" | xargs)" == BASALTOS_M3_TARGET ]] || { echo 'Not the dedicated M3 test disk.' >&2; exit 1; }
[[ "$(lsblk -dnro SIZE -b "$disk")" == 51539607552 ]] || { echo 'Expected the new 48 GiB test disk.' >&2; exit 1; }
[[ -z "$(wipefs --noheadings --output TYPE "$disk")" ]] || { echo 'Test disk is not blank; refusing format.' >&2; exit 1; }
[[ $# == 1 && "$1" == --erase-basaltos-m3-test-disk ]] || { echo 'Explicit test-disk erase argument required.' >&2; exit 1; }
read -r -p 'New login name: ' login_name
[[ "$login_name" =~ ^[a-z][a-z0-9_]{0,30}$ && "$login_name" != root ]] || exit 1
read -rs -p 'Login password: ' user_password; echo
read -rs -p 'LUKS passphrase: ' luks_password; echo
[[ ${#user_password} -ge 8 && ${#luks_password} -ge 8 ]] || { echo 'Use at least 8 characters.' >&2; exit 1; }
sfdisk "$disk" <<'EOF'
label: gpt
size=512MiB, type=U, name="BASALT_EFI"
size=8MiB, type=21686148-6449-6E6F-744E-656564454649, name="basalt-bios"
size=1536MiB, type=L, name="basalt-boot"
type=L, name="basalt-root"
EOF
udevadm settle
mkfs.fat -F32 -n BASALT_EFI /dev/vda1
mkfs.ext4 -L basalt-boot /dev/vda3
printf '%s' "$luks_password" | cryptsetup luksFormat --type luks2 --batch-mode --key-file - /dev/vda4
printf '%s' "$luks_password" | cryptsetup open --key-file - /dev/vda4 basalt-root
unset luks_password
mkfs.btrfs -L basalt-root /dev/mapper/basalt-root
target=/mnt/basaltos-m3-test
mkdir -p "$target"
mount /dev/mapper/basalt-root "$target"
for name in @ @home @cache @log; do btrfs subvolume create "$target/$name"; done
umount "$target"
mount -o subvol=@,compress=zstd:1,noatime /dev/mapper/basalt-root "$target"
mkdir -p "$target"/{home,var/cache,var/log,boot}
mount -o subvol=@home,compress=zstd:1,noatime /dev/mapper/basalt-root "$target/home"
mount -o subvol=@cache,compress=zstd:1,noatime /dev/mapper/basalt-root "$target/var/cache"
mount -o subvol=@log,compress=zstd:1,noatime /dev/mapper/basalt-root "$target/var/log"
mount /dev/vda3 "$target/boot"
mkdir -p "$target/boot/efi"
mount -o umask=0077 /dev/vda1 "$target/boot/efi"
unsquashfs -f -d "$target" /run/archiso/bootmnt/basalt/x86_64/airootfs.sfs
genfstab -U "$target" > "$target/etc/fstab"
arch-chroot "$target" useradd -m -U -G wheel -s /bin/bash "$login_name"
printf '%s:%s\nroot:%s\n' "$login_name" "$user_password" "$user_password" | arch-chroot "$target" chpasswd
unset user_password
arch-chroot "$target" /bin/bash /usr/local/lib/basaltos/finalize-installed.sh
arch-chroot "$target" grub-install --target=i386-pc "$disk"
arch-chroot "$target" grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=BasaltOS --removable --no-nvram
arch-chroot "$target" grub-mkconfig -o /boot/grub/grub.cfg
sync
umount -R "$target"
cryptsetup close basalt-root
echo 'M3 scripted installation completed. Shut down and boot the test disk without the ISO.'
