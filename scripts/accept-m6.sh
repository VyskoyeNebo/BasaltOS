#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || exit 1
[[ ! -d /run/archiso/bootmnt ]] || { echo 'Installed system required.'; exit 1; }
lsblk -dn -o SERIAL /dev/vda | grep -qx BASALTOS_M6_TARGET || exit 1
exec > >(tee /tmp/m6-accept.log) 2>&1
trap 'curl -fsS -T /tmp/m6-accept.log http://10.0.2.2:8181/work/m6/installed-acceptance.log || true' EXIT
export LC_ALL=C.UTF-8
echo '=== M6 INSTALLED ENVIRONMENT ==='
hostnamectl --static
localectl status
timedatectl status
lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINTS
systemctl is-active nftables NetworkManager
systemctl start basaltos-keyring.service
systemctl --no-pager status basaltos-keyring.service
fingerprint=$(cat /usr/share/basaltos/keys/basaltos-key.fingerprint)
pacman-key --finger "$fingerprint"
echo '=== ENABLE STRICT SIGNED REPOSITORY ==='
basaltos-repo enable http://10.0.2.2:8181/repo/x86_64 --allow-http
pacman-conf --repo basaltos SigLevel Server
state_hash() {
    find /var/lib/pacman /etc/pacman.d/gnupg -type f ! -name '*.lock' ! -name '*~' -exec sha256sum {} + | sort
    snapper -c root list --columns number,type,pre-number,description
    snapper -c home list --columns number,type,pre-number,description
}
state_hash > /tmp/m6-state-before
echo '=== CHECK-ONLY MUST NOT CHANGE SYSTEM STATE ==='
basaltos-update --check-only
state_hash > /tmp/m6-state-after
cmp /tmp/m6-state-before /tmp/m6-state-after
echo 'PASS: real pacman/keyring files and root/home snapshot lists unchanged.'
echo '=== TAMPERED DATABASE MUST FAIL ==='
bad=$(mktemp /tmp/basaltos-bad-config.XXXXXXXX)
sed 's#http://10.0.2.2:8181/repo/x86_64#http://10.0.2.2:8181/work/m6/bad-repo/x86_64#' /etc/pacman.conf > "$bad"
if unshare --mount bash -c 'mount --bind "$1" /etc/pacman.conf; basaltos-update --check-only' bash "$bad" > /tmp/m6-negative.log 2>&1; then
    echo 'FAIL: tampered database accepted'; exit 1
fi
cat /tmp/m6-negative.log
grep -Eiq 'PGP signature|invalid signature|BAD signature|signature.*invalid' /tmp/m6-negative.log
echo 'PASS: tampered repository rejected; real repository configuration unchanged.'
echo '=== M5 SNAPSHOT AND BOOT BACKUP REGRESSION ==='
basaltos-update --dry-run
echo '=== PACMAN FULL SYNC/UPGRADE AND SIGNED DEMO INSTALL ==='
pacman -Syu --noconfirm basaltos-release
pacman -Q basaltos-release
cat /usr/share/basaltos/release-info
curl -fsS http://10.0.2.2:8181/repo/x86_64/basaltos.db -o /tmp/m6-basaltos.db
curl -fsS http://10.0.2.2:8181/repo/x86_64/basaltos.db.sig -o /tmp/m6-basaltos.db.sig
pacman-key --verify /tmp/m6-basaltos.db.sig /tmp/m6-basaltos.db
echo '=== FINAL CHECK-ONLY ==='
basaltos-update --check-only
nft list ruleset
ss -tlnp
ss -ulnp
snapper -c root list --columns number,type,pre-number,description
echo '=== M6_INSTALLED_ACCEPTANCE_DONE ==='
