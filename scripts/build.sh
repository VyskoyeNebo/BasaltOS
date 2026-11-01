#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_root="${BASALT_BUILD_ROOT:-${project_dir}/work/linux-build}"
out_dir="${BASALT_OUT_DIR:-${project_dir}/out}"
milestone="${BASALT_MILESTONE:-m1}"
mkdir -p "$build_root" "$out_dir"
case "$(stat -f -c %T "$build_root")" in
    9p|drvfs|vboxsf|ntfs|fuseblk)
        echo 'BASALT_BUILD_ROOT must be on a native Linux filesystem.' >&2; exit 1 ;;
esac
run_dir="$(mktemp -d "${build_root}/${milestone}.XXXXXXXX")"
python "$project_dir/scripts/stage-profile.py" "$run_dir/profile"
if [[ -n "${BASALT_LOCAL_REPO:-}" ]]; then
    [[ -f "$BASALT_LOCAL_REPO/basaltos-local.db" ]] || { echo 'Local package repository is missing.' >&2; exit 1; }
    printf '\n[basaltos-local]\nSigLevel = Optional TrustAll\nServer = file://%s\n' "$BASALT_LOCAL_REPO" >> "$run_dir/profile/pacman.conf"
fi
echo "Build workspace: $run_dir"
pacman -Q archiso | tee "$out_dir/archiso-version.txt"
touch "$run_dir/build-start"
mkarchiso -v -w "$run_dir/work" -o "$out_dir" "$run_dir/profile" 2>&1 | tee "$run_dir/build.log"
cp "$run_dir/build.log" "$out_dir/build.log"
mapfile -t images < <(find "$out_dir" -maxdepth 1 -name 'basaltos-*.iso' -type f -newer "$run_dir/build-start")
(( ${#images[@]} == 1 )) || { echo 'Expected one newly built ISO.' >&2; exit 1; }
iso="${images[0]}"
(( $(stat -c %s "$iso") > 500000000 )) || { echo 'ISO is below the M1 size threshold.' >&2; exit 1; }
if [[ "$milestone" == m2 || "$milestone" == m3 ]] && (( $(stat -c %s "$iso") >= 4000000000 )); then
    echo "$milestone ISO exceeds the 4 GB target." >&2; exit 1
fi
python - "$iso" <<'PY'
from pathlib import Path
import sys
with Path(sys.argv[1]).open('rb') as source:
    source.seek(16 * 2048)
    descriptor = source.read(2048)
assert descriptor[1:6] == b'CD001', 'Missing ISO9660 primary descriptor'
label = descriptor[40:72].decode('ascii').rstrip()
assert label == 'basaltos', f'Unexpected ISO volume label: {label!r}'
print(f'ISO volume label verified: {label}')
PY
(cd "$out_dir" && sha256sum "$(basename "$iso")" > "$(basename "$iso").sha256")
echo "ISO ready: $iso ($(stat -c %s "$iso") bytes)"
