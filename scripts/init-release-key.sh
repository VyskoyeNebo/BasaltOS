#!/usr/bin/env bash
# Test key only. Private storage MUST be outside the source/package/ISO trees.
set -euo pipefail
(( EUID == 0 )) || { echo 'Run on the dedicated Linux builder as root.' >&2; exit 1; }
private=/root/BasaltOS/work/m6-private
umask 077
mkdir -p "$private/gnupg"
chmod 700 "$private" "$private/gnupg"
export GNUPGHOME="$private/gnupg"
if [[ ! -s "$private/fingerprint" ]]; then
    [[ ! -e "$private/passphrase" ]] || { echo 'Incomplete key state; inspect it manually.' >&2; exit 1; }
    openssl rand -hex 32 > "$private/passphrase"
    gpg --batch --pinentry-mode loopback --passphrase-file "$private/passphrase" \
        --quick-generate-key 'BasaltOS TEST Release <basaltos-release@basaltos.local>' ed25519 cert 180d
    gpg --batch --with-colons --list-keys | awk -F: '$1=="fpr" {print $10;exit}' > "$private/fingerprint"
    gpg --batch --pinentry-mode loopback --passphrase-file "$private/passphrase" \
        --quick-add-key "$(cat "$private/fingerprint")" ed25519 sign 180d
fi
fingerprint=$(cat "$private/fingerprint")
public=/root/BasaltOS/work/m6-public
mkdir -p "$public"
gpg --batch --armor --export "$fingerprint" > "$public/basaltos-key.asc"
printf '%s\n' "$fingerprint" > "$public/basaltos-key.fingerprint"
gpg --batch --with-subkey-fingerprint --list-keys "$fingerprint"
echo 'Only public material follows this point.'
for item in "$public"/*; do
    curl -fsS -T "$item" "http://10.0.2.2:8181/work/m6/$(basename "$item")"
done
