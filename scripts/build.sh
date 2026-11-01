#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root.' >&2; exit 1; }
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_root="${BASALT_BUILD_ROOT:-${project_dir}/work/linux-build}"
mkdir -p "$build_root" "$project_dir/out"
case "$(stat -f -c %T "$build_root")" in
    9p|drvfs|vboxsf|ntfs|fuseblk)
        echo 'BASALT_BUILD_ROOT must be on a native Linux filesystem.' >&2; exit 1 ;;
esac
run_dir="$(mktemp -d "${build_root}/m1.XXXXXXXX")"
python "$project_dir/scripts/stage-profile.py" "$run_dir/profile"
echo "Build workspace: $run_dir"
pacman -Q archiso | tee "$project_dir/out/archiso-version.txt"
mkarchiso -v -w "$run_dir/work" -o "$project_dir/out" "$run_dir/profile" 2>&1 | tee "$run_dir/build.log"
cp "$run_dir/build.log" "$project_dir/out/build.log"
mapfile -t images < <(find "$project_dir/out" -maxdepth 1 -name 'basaltos-*.iso' -type f -newer "$run_dir/profile/profiledef.sh")
(( ${#images[@]} == 1 )) || { echo 'Expected one newly built ISO.' >&2; exit 1; }
iso="${images[0]}"
(( $(stat -c %s "$iso") > 500000000 )) || { echo 'ISO is below the M1 size threshold.' >&2; exit 1; }
(cd "$project_dir/out" && sha256sum "$(basename "$iso")" > "$(basename "$iso").sha256")
echo "ISO ready: $iso ($(stat -c %s "$iso") bytes)"
