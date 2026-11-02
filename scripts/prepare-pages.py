#!/usr/bin/env python3
"""Verify offline-signed Release assets and prepare static Pages files."""
import argparse
import hashlib
import html
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version', required=True)
parser.add_argument('--release-dir', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.]+)?', args.version):
    parser.error('Invalid version')
if args.output.exists():
    parser.error('Output already exists; use a new directory')
release = args.release_dir.resolve()
key = root/'packaging/basaltos-key.asc'
fingerprint = (root/'packaging/basaltos-key.fingerprint').read_text(encoding='ascii').strip()
with tempfile.TemporaryDirectory(prefix='basaltos-pages-') as temporary:
    home = Path(temporary)
    home.chmod(0o700)
    def gpg(*options, **kwargs):
        return subprocess.run(['gpg', '--homedir', str(home), '--batch', *options], check=True, **kwargs)
    gpg('--import', str(key))
    listing = subprocess.check_output(['gpg', '--homedir', str(home), '--batch', '--with-colons', '--list-keys'], text=True)
    assert sum(line.startswith('pub:') for line in listing.splitlines()) == 1, 'Expected exactly one pinned primary key'
    primary = next(line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:'))
    assert primary == fingerprint, 'Public-key fingerprint mismatch'
    gpg('--verify', str(release/'SHA256SUMS.asc'), str(release/'SHA256SUMS'))
    sums = {}
    for line in (release/'SHA256SUMS').read_text(encoding='ascii').splitlines():
        digest, filename = line.split(maxsplit=1)
        assert re.fullmatch(r'[0-9a-f]{64}', digest)
        assert PurePosixPath(filename).name == filename and '\\' not in filename
        assert filename not in sums, 'Duplicate checksum entry'
        sums[filename] = digest
    archive = f'pacman-repo-{args.version}.tar.gz'
    for filename in (archive, 'basaltos-key.asc'):
        with (release/filename).open('rb') as source:
            assert hashlib.file_digest(source, 'sha256').hexdigest() == sums[filename], filename
    assert (release/'basaltos-key.asc').read_bytes() == key.read_bytes()
    staged = home/'site'
    staged.mkdir()
    with tarfile.open(release/archive, 'r:gz') as package:
        members = package.getmembers()
        assert sum(item.size for item in members) < 256*1024**2, 'Repository exceeds M6 staging limit'
        for item in members:
            path = PurePosixPath(item.name)
            assert path.parts and path.parts[0] == 'x86_64' and '..' not in path.parts and '\\' not in item.name
            assert item.isfile() or item.isdir(), 'Pages archives must contain regular files/directories only'
        package.extractall(staged, members=members, filter='data')
    repo = staged/'x86_64'
    for database in ('basaltos.db', 'basaltos.files', 'basaltos.db.tar.gz', 'basaltos.files.tar.gz'):
        gpg('--verify', str(repo/(database+'.sig')), str(repo/database))
    for alias, archive_name in (('basaltos.db', 'basaltos.db.tar.gz'), ('basaltos.files', 'basaltos.files.tar.gz')):
        assert (repo/alias).read_bytes() == (repo/archive_name).read_bytes()
        assert (repo/(alias+'.sig')).read_bytes() == (repo/(archive_name+'.sig')).read_bytes()
    packages = list(repo.glob('*.pkg.tar.zst'))
    assert packages, 'Empty repository'
    for package in packages:
        gpg('--verify', str(package)+'.sig', str(package))
    shutil.copyfile(key, staged/'basaltos-key.asc')
    (staged/'.nojekyll').touch()
    links = '\n'.join(f'<li><a href="x86_64/{html.escape(p.name, quote=True)}">{html.escape(p.name)}</a></li>' for p in sorted(repo.iterdir()))
    (staged/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>BasaltOS test repository</title><h1>BasaltOS test repository</h1><p>Test signing key: '+fingerprint+'</p><ul>'+links+'</ul>', encoding='utf-8')
    shutil.copytree(staged, args.output)
print(f'Verified Pages content prepared: {args.output}')
