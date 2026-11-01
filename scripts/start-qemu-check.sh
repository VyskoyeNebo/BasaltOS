#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
iso="$(find "$project_dir/out" -maxdepth 1 -name 'basaltos-*.iso' | sort | tail -n 1)"
test -n "$iso"
mkdir -p "$project_dir/work"
pidfile="$project_dir/work/qemu-check.pid"
trap 'if [[ -f "$pidfile" ]]; then kill "$(cat "$pidfile")" 2>/dev/null || true; fi' EXIT
qemu-system-x86_64 --version | head -n 1
sysctl -w 'net.ipv4.ping_group_range=0 2147483647'
qemu-system-x86_64 -machine q35 -accel tcg,thread=single \
    -icount shift=auto,sleep=on -rtc clock=vm -cpu qemu64 -m 2048 -smp 1 \
    -cdrom "$iso" -boot d -display none -vga std \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
    -serial "file:$project_dir/out/m1-qemu-serial.txt" \
    -qmp tcp:0.0.0.0:4444,server=on,wait=off \
    -pidfile "$pidfile" -daemonize -no-reboot
echo 'QEMU started; use qemu-console.py and the VirtualBox localhost port forward.'
# arch-chroot uses a private PID namespace: keep its init process alive until QEMU exits.
while kill -0 "$(cat "$pidfile")" 2>/dev/null; do
    sleep 1
done
