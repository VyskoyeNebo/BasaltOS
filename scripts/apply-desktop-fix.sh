#!/usr/bin/env bash
# Apply only the 0.1.1 desktop files to an existing BasaltOS installation.
set -euo pipefail
(( EUID == 0 )) || { echo 'Run with sudo.' >&2; exit 1; }
project=${1:?Usage: apply-desktop-fix.sh SOURCE_DIRECTORY}
grep -qx 'ID=basaltos' /etc/os-release || { echo 'BasaltOS required.' >&2; exit 1; }
source="$project/profile/airootfs"
for name in computer trash files settings; do
    entry="basaltos-$name.desktop"
    desktop-file-validate "$source/etc/skel/Desktop/$entry"
    install -Dm755 "$source/etc/skel/Desktop/$entry" "/etc/skel/Desktop/$entry"
done
install -Dm755 "$source/usr/bin/basaltos-desktop-shortcuts" /usr/bin/basaltos-desktop-shortcuts
install -Dm644 "$source/etc/xdg/autostart/basaltos-desktop-shortcuts.desktop" /etc/xdg/autostart/basaltos-desktop-shortcuts.desktop
install -m644 "$source/etc/os-release" /etc/os-release
echo 'Installed 0.1.1 desktop defaults. Run basaltos-desktop-shortcuts as your desktop user, without sudo.'
