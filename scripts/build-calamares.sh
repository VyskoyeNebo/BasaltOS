#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || { echo 'Run as root in the BasaltOS builder.' >&2; exit 1; }
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
pacman -Syu --noconfirm --needed base-devel cmake ninja extra-cmake-modules qt6-tools \
  python python-yaml python-jsonschema yaml-cpp qt6-base qt6-svg qt6-declarative kcoreaddons kconfig \
  ki18n kwidgetsaddons kpmcore libpwquality polkit-qt6 boost boost-libs parted \
  cryptsetup rsync squashfs-tools
id basaltpkg &>/dev/null || useradd --system --create-home basaltpkg
package_dir=/root/BasaltOS/work/calamares-package
install -d -o basaltpkg -g basaltpkg /var/tmp/basaltos-calamares
install -o basaltpkg -g basaltpkg -m644 "$project_dir/packaging/calamares/PKGBUILD" /var/tmp/basaltos-calamares/PKGBUILD
runuser -u basaltpkg -- bash -c 'cd /var/tmp/basaltos-calamares && makepkg --noconfirm --cleanbuild --force'
mkdir -p "$package_dir"
cp /var/tmp/basaltos-calamares/calamares-*.pkg.tar.zst "$package_dir/"
repo-add "$package_dir/basaltos-local.db.tar.gz" "$package_dir"/calamares-*.pkg.tar.zst
sha256sum "$package_dir"/*.pkg.tar.zst
