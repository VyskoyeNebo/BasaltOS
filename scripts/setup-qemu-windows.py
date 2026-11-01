#!/usr/bin/env python3
"""Install a portable MSYS2 UCRT64 QEMU under work/tools, using TUNA only.

Python 3.14+ is required for .tar.zst. No installers, registry changes or package hooks run.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1] / 'work/tools'
cache = root / 'packages'
destination = root / 'msys2'
cache.mkdir(parents=True, exist_ok=True)
destination.mkdir(parents=True, exist_ok=True)
base = 'https://mirrors.tuna.tsinghua.edu.cn/msys2/mingw/ucrt64/'
database = root / 'ucrt64.db'
if not database.exists():
    urllib.request.urlretrieve(base+'ucrt64.db', database)
packages = {}
providers = {}
with tarfile.open(database) as archive:
    for member in archive:
        if not member.name.endswith('/desc'):
            continue
        blocks = archive.extractfile(member).read().decode().strip().split('\n\n')
        data = {}
        for block in blocks:
            lines = block.splitlines()
            data[lines[0].strip('%')] = lines[1:]
        name = data['NAME'][0]
        packages[name] = data
        for provided in data.get('PROVIDES', []):
            providers[re.split(r'[<>=]', provided)[0]] = name
selected = {}

def include(name):
    name = re.split(r'[<>=]', name)[0]
    if name not in packages:
        name = providers.get(name, name)
    if name in selected:
        return
    data = packages[name]
    selected[name] = data
    for dependency in data.get('DEPENDS', []):
        include(dependency)

include('mingw-w64-ucrt-x86_64-qemu')
print(f'{len(selected)} packages; {sum(int(p["CSIZE"][0]) for p in selected.values())/1048576:.1f} MiB download', flush=True)

def fetch(data):
    filename = data['FILENAME'][0]
    path = cache / filename
    expected = data['SHA256SUM'][0]
    if path.exists() and hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == expected:
        return path
    temporary = path.with_name(path.name+'.partial')
    for attempt in range(3):
        try:
            with urllib.request.urlopen(base+filename, timeout=120) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response, output)
            actual = hashlib.file_digest(temporary.open('rb'), 'sha256').hexdigest()
            if actual != expected:
                raise RuntimeError(f'Checksum mismatch: {filename}')
            temporary.replace(path)
            return path
        except Exception:
            if attempt == 2:
                raise

with ThreadPoolExecutor(max_workers=6) as pool:
    archives = list(pool.map(fetch, selected.values()))
print('Downloads and SHA-256 checks complete; extracting portable files', flush=True)
for index, path in enumerate(archives):
    with tarfile.open(path) as archive:
        links = []
        for member in archive:
            if not member.name.startswith('ucrt64/'):
                continue
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise RuntimeError(f'Unsafe archive path: {member.name}')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open('wb') as output:
                    shutil.copyfileobj(source, output)
            elif member.issym() or member.islnk():
                links.append((target, member))
        for target, member in links:
            source = ((target.parent / member.linkname) if member.issym() else (destination/member.linkname)).resolve()
            if source.is_relative_to(destination.resolve()) and source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    if index % 10 == 0:
        print(f'Extracted {index+1}/{len(archives)}', flush=True)
(root / 'qemu-packages.json').write_text(json.dumps(selected, indent=2)+'\n')
print(destination / 'ucrt64/bin/qemu-system-x86_64.exe', flush=True)
