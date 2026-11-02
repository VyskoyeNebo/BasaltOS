#!/usr/bin/env bash
# Run only as root on the new, disposable M5 installed QEMU disk.
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
[[ ! -d /run/archiso/bootmnt ]] || { echo 'Installed system required.' >&2; exit 1; }
lsblk -dn -o SERIAL /dev/vda | grep -qx BASALTOS_M5_TARGET || { echo 'Not the M5 disposable QEMU target.' >&2; exit 1; }
exec > >(tee /tmp/m5-accept.log) 2>&1
trap 'curl -fsS -T /tmp/m5-accept.log http://10.0.2.2:8181/work/m5/installed-acceptance.log || true' EXIT
echo '=== M5 ENVIRONMENT ==='
hostnamectl --static
localectl status
timedatectl status
lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINTS,UUID
btrfs subvolume list /
snapper -c root list
snapper -c home list
echo '=== FIREWALL ==='
systemctl is-enabled nftables
systemctl is-active nftables
nft -c -f /etc/nftables.conf
# Prove reload keeps unrelated tables, instead of using flush ruleset.
if nft list table inet basaltos_m5_reload_probe >/dev/null 2>&1; then
    echo 'Reload-probe table already exists; refusing to modify it.'; exit 1
fi
nft add table inet basaltos_m5_reload_probe
systemctl reload nftables
nft list table inet basaltos_m5_reload_probe
nft delete table inet basaltos_m5_reload_probe
nft list ruleset
echo '=== NETWORK AND DEFAULT LISTENERS ==='
ip -br a
ping -c 3 mirrors.tuna.tsinghua.edu.cn
curl -fsSI --max-time 20 https://mirrors.tuna.tsinghua.edu.cn/archlinux/
ss -tlnp
ss -ulnp
if ss -H -ulnp | grep -E ':(5353|5355)[[:space:]]'; then
    echo 'FAIL: unexpected mDNS/LLMNR listener'; exit 1
fi
echo '=== SERVICES AND PRIVACY ==='
systemctl --no-pager --type=service --state=running
systemctl --no-pager list-timers --all
systemctl is-enabled avahi-daemon.service avahi-daemon.socket || true
systemd-analyze cat-config systemd/resolved.conf
NetworkManager --print-config
cat /etc/xdg/KDE/UserFeedback.conf
ps -ef | grep -Ei 'telemetry|feedback|report|crash' | grep -v grep || true
echo '=== PACKAGE TRUST ==='
pacman-conf SigLevel LocalFileSigLevel
pacman -Q archlinux-keyring nftables pacman-contrib snapper snap-pac
cat /etc/pacman.conf
echo '=== UNSIGNED LOCAL PACKAGE MUST BE REJECTED ==='
probe=$(mktemp -d /tmp/basaltos-signature-probe.XXXXXXXX)
mkdir -p "$probe/usr/share/basaltos-signature-probe"
printf 'M5 disposable test\n' > "$probe/usr/share/basaltos-signature-probe/marker"
cat > "$probe/.PKGINFO" <<'EOF'
pkgname = basaltos-signature-probe
pkgbase = basaltos-signature-probe
pkgver = 1-1
pkgdesc = M5 unsigned package rejection test
builddate = 1793577600
packager = BasaltOS disposable test
size = 19
arch = any
EOF
bsdtar -cf "$probe/probe.pkg.tar" -C "$probe" .PKGINFO usr
zstd -q "$probe/probe.pkg.tar" -o "$probe/basaltos-signature-probe-1-1-any.pkg.tar.zst"
pacman -Qip "$probe/basaltos-signature-probe-1-1-any.pkg.tar.zst"
if pacman -U --noconfirm "$probe/basaltos-signature-probe-1-1-any.pkg.tar.zst"; then
    echo 'FAIL: unsigned package was accepted'; exit 1
fi
if pacman -Q basaltos-signature-probe; then
    echo 'FAIL: probe package installed'; exit 1
fi
echo 'Unsigned local package rejected; nothing installed.'
echo '=== UPDATE DRY RUN ==='
basaltos-update --dry-run
snapper -c root list
latest=$(find /var/lib/basaltos-update/transactions -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
basaltos-update --recovery-info "$(basename "$latest")" > /tmp/m5-recovery.txt
cat /tmp/m5-recovery.txt
curl -fsS -T /tmp/m5-recovery.txt http://10.0.2.2:8181/work/m5/recovery-info.txt
echo '=== WEEKLY CHECK ==='
systemctl start basaltos-update-check.service
systemctl --no-pager status basaltos-update-check.timer
cat /var/lib/basaltos-update-check/result.json
echo '=== M5_INSTALLED_ACCEPTANCE_DONE ==='
