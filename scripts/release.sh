#!/usr/bin/env bash
# Prepare reviewable attachments locally; never push or publish automatically.
set -euo pipefail
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
version=${1:?Usage: release.sh VERSION [--existing-iso PATH]}
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9.]+)?$ ]] || { echo 'Invalid release version.' >&2; exit 1; }
shift
if (( $# == 0 )); then
    export BASALT_MILESTONE=m6
    bash "$project/scripts/build.sh"
    out=${BASALT_OUT_DIR:-$project/out}
    mapfile -t images < <(find "$out" -maxdepth 1 -name 'basaltos-*.iso' -type f)
    (( ${#images[@]} == 1 )) || { echo 'Specify exactly one ISO with --existing-iso.' >&2; exit 1; }
    iso=${images[0]}
elif [[ "$1" == --existing-iso && $# == 2 ]]; then
    iso=$(realpath -- "$2")
else
    echo 'Usage: release.sh VERSION [--existing-iso PATH]' >&2; exit 1
fi
(( $(stat -c %s "$iso") > 500000000 && $(stat -c %s "$iso") < 8000000000 )) || exit 1
private=/root/BasaltOS/work/m6-private
export GNUPGHOME="${GNUPGHOME:-$private/gnupg}"
key="${BASALT_SIGNING_KEY:-$(cat "$project/packaging/basaltos-key.fingerprint")}"
[[ "$key" == "$(cat "$project/packaging/basaltos-key.fingerprint")" ]] || exit 1
repo=${BASALT_REPO_DIR:-$project/repo/x86_64}
gpg --verify "$repo/basaltos.db.sig" "$repo/basaltos.db"
destination=${BASALT_RELEASE_DIR:-$project/out/releases/$version}
[[ ! -e "$destination" ]] || { echo 'Release output already exists; do not overwrite signed attachments.' >&2; exit 1; }
mkdir -p "$destination"
cp --reflink=auto "$iso" "$destination/basaltos-$version-x86_64.iso"
cp "$project/packaging/basaltos-key.asc" "$destination/basaltos-key.asc"
# dereference repo-add aliases: Pages artifacts must not contain links.
tar --dereference -czf "$destination/pacman-repo-$version.tar.gz" -C "$(dirname "$repo")" x86_64
(
    cd "$destination"
    sha256sum "basaltos-$version-x86_64.iso" "pacman-repo-$version.tar.gz" basaltos-key.asc > SHA256SUMS
)
sign=(gpg --batch --yes --local-user "$key" --armor --detach-sign)
if [[ -s "$private/passphrase" ]]; then
    sign+=(--pinentry-mode loopback --passphrase-file "$private/passphrase")
fi
"${sign[@]}" --output "$destination/SHA256SUMS.asc" "$destination/SHA256SUMS"
gpg --verify "$destination/SHA256SUMS.asc" "$destination/SHA256SUMS"
cat > "$destination/RELEASE-NOTES.md" <<EOF
# BasaltOS $version

Test release, not production signing identity. Key: $key

- ISO, signed pacman repository archive, public key, SHA256SUMS and signature are attachments.
- Verify the fingerprint independently, then verify SHA256SUMS.asc and sha256sum -c SHA256SUMS.
- Fill in the final Git commit/tag, Pages URL, changes and known limitations before publication.
- Updates retain the M5 snapshot and boot/ESP backup behavior; see docs/SECURITY.md.

Prepared locally. No GitHub upload or Pages deployment has been performed.
EOF
cat > "$destination/UPLOAD.txt" <<EOF
Review RELEASE-NOTES.md and SHA256SUMS first.
Create/push the version tag only after local verification:
  git tag -a $version -m 'BasaltOS $version'
  git push origin $version
Create a DRAFT Release, then review it on GitHub before making it public:
  gh release create $version --verify-tag --draft --title 'BasaltOS $version' --notes-file RELEASE-NOTES.md basaltos-$version-x86_64.iso pacman-repo-$version.tar.gz basaltos-key.asc SHA256SUMS SHA256SUMS.asc
Deploy the repository separately through the gh-pages branch workflow after publishing the reviewed Release.
EOF
echo "Release attachments prepared locally: $destination"
