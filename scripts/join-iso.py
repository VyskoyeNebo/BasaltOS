#!/usr/bin/env python3
"""Join split ISO assets AFTER verifying the signed SHA256SUMS manifest."""
import argparse
import hashlib
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--release-dir', type=Path, required=True)
parser.add_argument('--version', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.]+)?', args.version):
    parser.error('Invalid version')
name = f'basaltos-{args.version}-x86_64.iso'
sums = {}
for line in (args.release_dir/'SHA256SUMS').read_text(encoding='ascii').splitlines():
    digest, filename = line.split(maxsplit=1)
    if not re.fullmatch('[a-f0-9]{64}', digest) or Path(filename).name != filename or filename in sums:
        parser.error('Invalid checksum manifest')
    sums[filename] = digest
parts = sorted(filename for filename in sums if re.fullmatch(re.escape(name)+r'\.part\d{2}', filename))
if not parts or parts != [name+f'.part{number:02d}' for number in range(len(parts))] or name not in sums:
    parser.error('Missing ISO checksum or non-contiguous parts')
partial = args.output.with_name(args.output.name+'.partial')
if args.output.exists() or partial.exists():
    parser.error('Output or partial output exists; refusing to overwrite')
whole = hashlib.sha256()
with partial.open('xb') as destination:
    for part in parts:
        digest = hashlib.sha256()
        with (args.release_dir/part).open('rb') as source:
            while block := source.read(4*1024**2):
                digest.update(block)
                whole.update(block)
                destination.write(block)
        if digest.hexdigest() != sums[part]:
            raise SystemExit(f'Checksum mismatch: {part}; partial output retained for inspection')
if whole.hexdigest() != sums[name]:
    raise SystemExit('Reassembled ISO checksum mismatch; partial output retained')
partial.replace(args.output)
print(f'Reassembled ISO SHA-256: {whole.hexdigest()}')
print('Checksum verification passed. Authenticity requires separate GPG verification of SHA256SUMS.asc.')
