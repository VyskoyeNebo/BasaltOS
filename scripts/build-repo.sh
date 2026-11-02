#!/usr/bin/env bash
set -euo pipefail
(( EUID == 0 )) || { echo 'Run on the Linux builder as root.' >&2; exit 1; }
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
private=/root/BasaltOS/work/m6-private
export GNUPGHOME="${GNUPGHOME:-$private/gnupg}"
key="${BASALT_SIGNING_KEY:-$(cat "$private/fingerprint")}"
destination="${BASALT_REPO_DIR:-$project/repo/x86_64}"
[[ "$key" == "$(tr -d '\r\n' < "$project/packaging/basaltos-key.fingerprint")" ]] || exit 1
mkdir -p "$destination"
id basaltpkg &>/dev/null || useradd --system --create-home basaltpkg
package_work=$(mktemp -d /var/tmp/basaltos-release.XXXXXXXX)
install -o basaltpkg -g basaltpkg -m644 "$project/packaging/basaltos-release/PKGBUILD" "$package_work/PKGBUILD"
chown basaltpkg:basaltpkg "$package_work"
runuser -u basaltpkg -- bash -c 'cd "$1" && makepkg --noconfirm --cleanbuild' bash "$package_work"
cp "$package_work"/basaltos-release-*.pkg.tar.zst "$destination/"
# Re-sign the unchanged, previously reviewed Calamares package too.
calamares=/root/BasaltOS/work/calamares-package/calamares-3.4.3-1-x86_64.pkg.tar.zst
printf '%s  %s\n' 962127440180c43f8b8752174de190c9e29c364178acbe1bd406003580e40f81 "$calamares" | sha256sum -c -
cp "$calamares" "$destination/"
for package in "$destination"/*.pkg.tar.zst; do
    if [[ -s "$private/passphrase" ]]; then
        gpg --batch --yes --pinentry-mode loopback --passphrase-file "$private/passphrase" \
            --local-user "$key" --detach-sign --output "$package.sig" "$package"
    else
        gpg --local-user "$key" --detach-sign --output "$package.sig" "$package"
    fi
    gpg --verify "$package.sig" "$package"
done
# gpg-agent holds the test signing subkey after the explicit signing above.
repo-add --sign --key "$key" "$destination/basaltos.db.tar.gz" "$destination"/*.pkg.tar.zst
gpg --verify "$destination/basaltos.db.tar.gz.sig" "$destination/basaltos.db.tar.gz"
gpg --verify "$destination/basaltos.files.tar.gz.sig" "$destination/basaltos.files.tar.gz"
echo 'Signed repository ready:'
ls -lh "$destination"
