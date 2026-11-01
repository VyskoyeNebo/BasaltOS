#!/usr/bin/env bash
# Run inside the mounted target, after Calamares users/fstab or the test installer.
set -euo pipefail
[[ "$(findmnt -nro FSTYPE /)" == btrfs ]] || { echo 'Target root must be btrfs.' >&2; exit 1; }
if [[ ! -s /etc/hostname || -z "$(tr -d '[:space:]' < /etc/hostname)" ]]; then
    echo basaltos > /etc/hostname
fi
root_device="$(findmnt -nro SOURCE /)"
root_device="${root_device%%\[*}"
root_device="$(readlink -f "$root_device")"
root_type="$(lsblk -dnro TYPE "$root_device")"
kernel_params='rootflags=subvol=@ rw'
if [[ "$root_type" == crypt ]]; then
    # lsblk --nodeps can leave PKNAME empty for dm-crypt. Read the actual slave.
    shopt -s nullglob
    parents=(/sys/class/block/"${root_device##*/}"/slaves/*)
    (( ${#parents[@]} == 1 )) || { echo 'Expected one LUKS backing partition.' >&2; exit 1; }
    parent="${parents[0]##*/}"
    [[ -b "/dev/$parent" ]] || { echo 'LUKS backing device is missing.' >&2; exit 1; }
    luks_uuid="$(cryptsetup luksUUID "/dev/$parent")"
    mapper="$(dmsetup info -c --noheadings -o name "$root_device" | xargs)"
    printf '%s UUID=%s none luks,timeout=0,x-initrd.attach\n' "$mapper" "$luks_uuid" > /etc/crypttab
    rm -f /etc/crypttab.initramfs
    # The password prompt can wait indefinitely, but the root UUID device job
    # otherwise expires first (normally after 90 s). Keep both waits aligned.
    kernel_params="rd.luks.name=${luks_uuid}=${mapper} rd.luks.options=timeout=0 rootflags=subvol=@,x-systemd.device-timeout=0 rw"
fi
# Remove Live-only boot settings and root console autologin.
rm -f /etc/mkinitcpio.conf.d/archiso.conf /etc/mkinitcpio.d/archiso.preset
rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
rm -f /etc/systemd/system/multi-user.target.wants/pacman-init.service
rm -f /etc/systemd/system/pacman-init.service /etc/systemd/system/etc-pacman.d-gnupg.mount
rm -f /etc/systemd/journald.conf.d/volatile-storage.conf /etc/systemd/logind.conf.d/do-not-suspend.conf
rm -f /etc/systemd/system-generators/systemd-gpt-auto-generator
rm -f /etc/pacman.d/hooks/zzzz99-remove-custom-hooks-from-airootfs.hook
rm -f /root/Desktop/install-basaltos.desktop /usr/share/applications/install-basaltos.desktop
rm -f /var/lib/sddm/state.conf
pacman-key --init
pacman-key --populate archlinux
cat > /etc/mkinitcpio.conf <<'EOF'
MODULES=(btrfs)
BINARIES=()
FILES=()
HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block sd-encrypt filesystems fsck)
EOF
cat > /etc/mkinitcpio.d/linux.preset <<'EOF'
ALL_kver="/boot/vmlinuz-linux"
PRESETS=('default')
default_image="/boot/initramfs-linux.img"
EOF
kernel_file="$(find /usr/lib/modules -mindepth 2 -maxdepth 2 -name vmlinuz -print -quit)"
[[ -n "$kernel_file" ]] || { echo 'Installed kernel image is missing.' >&2; exit 1; }
install -m644 "$kernel_file" /boot/vmlinuz-linux
mkinitcpio -P
cat > /etc/default/grub <<EOF
GRUB_DEFAULT=0
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="BasaltOS"
GRUB_CMDLINE_LINUX_DEFAULT="$kernel_params"
GRUB_CMDLINE_LINUX=""
GRUB_PRELOAD_MODULES="part_gpt part_msdos"
GRUB_TERMINAL_INPUT=console
GRUB_TERMINAL_OUTPUT=console
GRUB_DISABLE_OS_PROBER=true
EOF
cat > /etc/sddm.conf.d/10-basaltos.conf <<'EOF'
[General]
DisplayServer=x11
[Theme]
Current=breeze
CursorTheme=breeze_cursors
Font=Noto Sans CJK SC,11
[Users]
MinimumUid=1000
MaximumUid=60000
RememberLastUser=true
RememberLastSession=true
EOF
mkdir -p /etc/sudoers.d
printf '%%wheel ALL=(ALL:ALL) ALL\n' > /etc/sudoers.d/10-basaltos-wheel
chmod 440 /etc/sudoers.d/10-basaltos-wheel
# Apply the existing M2 user defaults to the created account through /etc/skel.
while IFS=: read -r name _ uid _ _ user_home _; do
    if (( uid >= 1000 && uid < 60000 )) && [[ -d "$user_home" ]]; then
        cp -a /etc/skel/. "$user_home/"
        # xdg-user-dirs resets missing Desktop directories to the home folder.
        mkdir -p "$user_home/Desktop"
        chown -R "$name:$name" "$user_home"
    fi
done < /etc/passwd
for item in 'root:/' 'home:/home'; do
    config="${item%%:*}"
    subvolume="${item#*:}"
    if [[ ! -f "/etc/snapper/configs/$config" ]]; then
        snapper --no-dbus -c "$config" create-config "$subvolume"
    fi
    snapper --no-dbus -c "$config" set-config TIMELINE_CREATE=yes TIMELINE_CLEANUP=yes \
        TIMELINE_LIMIT_HOURLY=5 TIMELINE_LIMIT_DAILY=7 TIMELINE_LIMIT_WEEKLY=2 \
        TIMELINE_LIMIT_MONTHLY=0 TIMELINE_LIMIT_YEARLY=0 NUMBER_LIMIT=10 NUMBER_LIMIT_IMPORTANT=5
    snapper --no-dbus -c "$config" create --description 'BasaltOS M3 initial installation' --cleanup-algorithm number
done
systemctl enable sddm NetworkManager systemd-resolved snapper-timeline.timer snapper-cleanup.timer
systemctl set-default graphical.target
printf 'BasaltOS — KDE Plasma installed system\n' > /etc/motd
rm -f /etc/machine-id /var/lib/dbus/machine-id
systemd-machine-id-setup
echo 'BasaltOS target finalized: initramfs, KDE users, btrfs and two Snapper configs.'
