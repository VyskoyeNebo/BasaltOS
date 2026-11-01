#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
iso="$(find "$project_dir/out" -maxdepth 1 -name 'basaltos-*.iso' | sort | tail -n 1)"
test -n "$iso"
runtime_dir="$(mktemp -d /tmp/basaltos-qemu.XXXXXXXX)"
trap 'if [[ -f "$runtime_dir/qemu.pid" ]]; then kill "$(cat "$runtime_dir/qemu.pid")" 2>/dev/null || true; fi' EXIT
qemu-system-x86_64 --version | head -n 1
# Nested hardware acceleration is unavailable on this builder; TCG performs the actual boot test.
qemu-system-x86_64 -accel tcg -cpu max -m 2048 -smp 2 \
    -cdrom "$iso" -boot d -display none -vga std \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
    -serial "unix:$runtime_dir/serial.sock,server=on,wait=off" \
    -qmp "unix:$runtime_dir/qmp.sock,server=on,wait=off" \
    -pidfile "$runtime_dir/qemu.pid" -daemonize -no-reboot
python "$project_dir/scripts/verify-qemu.py" "$runtime_dir" "$project_dir"
for artifact in m1-qemu.png m1-qemu-serial.txt m1-qemu-result.json; do
    curl -f --retry 3 -T "$project_dir/out/$artifact" "http://10.0.2.2:8181/out/$artifact"
done
echo '=== QEMU_ACCEPTANCE_OK ==='
