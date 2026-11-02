#!/usr/bin/env bash
# Temporary listener on the disposable M5 disk; always terminate our own child.
set -euo pipefail
(( EUID == 0 )) || exit 1
lsblk -dn -o SERIAL /dev/vda | grep -qx BASALTOS_M5_TARGET || exit 1
[[ ! -d /run/archiso/bootmnt ]] || exit 1
exec > >(tee /tmp/m5-inbound-probe.log) 2>&1
directory=$(mktemp -d /tmp/basaltos-inbound.XXXXXXXX)
printf 'M5 loopback test\n' > "$directory/index.html"
python -m http.server 18085 --bind 0.0.0.0 --directory "$directory" &
server=$!
cleanup() {
    kill "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
    curl -fsS -T /tmp/m5-inbound-probe.log http://10.0.2.2:8181/work/m5/inbound-probe.log || true
}
trap cleanup EXIT
sleep 1
curl -fsS http://127.0.0.1:18085/
ss -tlnp 'sport = :18085'
nft list chain inet basaltos_filter input
printf ready > "$directory/ready.txt"
curl -fsS -T "$directory/ready.txt" http://10.0.2.2:8181/work/m5/inbound-ready.txt
echo 'Host now attempts 127.0.0.1:18085; this listener must be unreachable through QEMU NAT.'
sleep 45
nft list chain inet basaltos_filter input
echo 'Probe finished; listener will be removed by EXIT trap.'
