"""Interactive full updates with retained Snapper and boot recovery material."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import uuid

STATE = Path('/var/lib/basaltos-update/transactions')

def run(*args, capture=False, **kwargs):
    return subprocess.run(args, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None, **kwargs)

def output(*args):
    return run(*args, capture=True).stdout.strip()

def mount_info(path):
    return json.loads(output('findmnt', '-J', '-T', path,
                             '-o', 'SOURCE,FSTYPE,UUID,FSROOT,TARGET'))['filesystems'][0]

def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def save(directory, record):
    temporary = directory/'manifest.json.tmp'
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(directory/'manifest.json')

def snapshot(kind, identifier, pre=None):
    args = ['snapper', '-c', 'root', 'create', '--type', kind, '--print-number',
            '--description', f'BasaltOS update {identifier} {kind}',
            '--userdata', f'basaltos-update={identifier}']
    if pre is not None:
        args += ['--pre-number', str(pre)]
    number = int(output(*args))
    if number <= 0:
        raise RuntimeError('Snapper returned an invalid snapshot number')
    return number

def recovery(identifier):
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}', identifier):
        raise RuntimeError('Invalid transaction ID')
    directory = STATE/identifier
    record = json.loads((directory/'manifest.json').read_text())
    for filename, expected in record['archives'].items():
        if digest(directory/filename) != expected:
            raise RuntimeError(f'Backup checksum mismatch: {filename}')
    q = shlex.quote
    print('OFFLINE RECOVERY ONLY. Read docs/SECURITY.md first; these commands are not executed.')
    print('Boot a BasaltOS Live ISO, become root, and verify every UUID using lsblk -f.')
    if record.get('luks_uuid'):
        print(f"cryptsetup open /dev/disk/by-uuid/{q(record['luks_uuid'])} basaltos-recovery")
    print('mkdir -p /mnt/basaltos-top /mnt/basaltos-boot')
    print(f"mount -o subvolid=5 /dev/disk/by-uuid/{q(record['root']['uuid'])} /mnt/basaltos-top")
    print(f"mount /dev/disk/by-uuid/{q(record['boot']['uuid'])} /mnt/basaltos-boot")
    top = '/mnt/basaltos-top'
    replacement = f'@.recovered-{identifier}'
    retained = f'@.before-recovery-{identifier}'
    print(f"btrfs subvolume snapshot {top}/@/.snapshots/{record['pre']}/snapshot {top}/{replacement}")
    print(f'mv {top}/@ {top}/{retained}')
    print(f'mv {top}/{replacement} {top}/@')
    print(f'rmdir {top}/@/.snapshots')
    print(f'mv {top}/{retained}/.snapshots {top}/@/.snapshots')
    backup = f'{top}/{retained}/var/lib/basaltos-update/transactions/{identifier}'
    print(f'mkdir -p /tmp/basaltos-recovery-{identifier}')
    print(f'tar --acls --xattrs --numeric-owner -xpf {backup}/boot.tar -C /tmp/basaltos-recovery-{identifier}')
    print('# Back up the CURRENT /boot before restoring. The following rsync deletes mismatched files only on the verified dedicated boot partition.')
    print(f'tar --one-file-system -cpf {backup}/boot-before-recovery.tar -C /mnt/basaltos-boot .')
    print(f'rsync -aHAX --delete --one-file-system --exclude=/efi/ /tmp/basaltos-recovery-{identifier}/ /mnt/basaltos-boot/')
    if record.get('esp'):
        print('mkdir -p /mnt/basaltos-boot/efi')
        print(f"mount /dev/disk/by-uuid/{q(record['esp']['uuid'])} /mnt/basaltos-boot/efi")
        print(f'tar -cpf {backup}/esp-before-recovery.tar -C /mnt/basaltos-boot/efi .')
        print(f'mkdir -p /tmp/basaltos-esp-{identifier}')
        print(f'tar -xpf {backup}/esp.tar -C /tmp/basaltos-esp-{identifier}')
        print('# ESP restore below is ONLY for the dedicated BasaltOS test layout, never a shared multi-OS ESP.')
        print(f'rsync -rt --delete /tmp/basaltos-esp-{identifier}/ /mnt/basaltos-boot/efi/')
    print('# The pre-snapshot contains our preparation lock. Remove it ONLY from this offline recovered root:')
    print(f'rm -f {top}/@/var/lib/pacman/db.lck')
    print('sync')
    print('Review fstab/crypttab and preserved @home/@log/@cache before unmounting and rebooting.')
    print('Retain the old root and backups until recovery has been verified. Do not use snapper rollback with rootflags=subvol=@.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Create real snapshots/boot backups; only check updates, never install')
    parser.add_argument('--recovery-info', metavar='ID', help='Validate backups and print offline recovery instructions')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo or as root')
    if args.recovery_info:
        recovery(args.recovery_info)
        return
    if Path('/run/archiso/bootmnt').exists():
        raise RuntimeError('Use the installed btrfs system; Live overlay cannot provide persistent root snapshots')
    root = mount_info('/')
    boot = mount_info('/boot')
    if root['fstype'] != 'btrfs' or root['fsroot'] != '/@':
        raise RuntimeError('This updater requires the M3 btrfs root subvolume @')
    if boot['target'] != '/boot' or not boot.get('uuid'):
        raise RuntimeError('Mount the dedicated M3 /boot partition before updating')
    if not Path('/etc/snapper/configs/root').exists():
        raise RuntimeError('Snapper root configuration is missing')
    if not root.get('uuid'):
        raise RuntimeError('Cannot determine root filesystem UUID')
    with open('/run/lock/basaltos-update.lock', 'w') as own_lock:
        try:
            fcntl.flock(own_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another basaltos-update is running')
        identifier = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8]
        STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory = STATE/identifier
        directory.mkdir(mode=0o700)
        record = {'id': identifier, 'root': root, 'boot': boot, 'dry_run': args.dry_run,
                  'status': 'preparing', 'archives': {}, 'created': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        db_lock = Path('/var/lib/pacman/db.lck')
        preparation_lock = None
        try:
            # Reserve the real package database only while making the consistent recovery set.
            # Never remove a lock belonging to another package manager.
            fd = os.open(db_lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            preparation_lock = os.fstat(fd).st_ino
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            record['pre'] = snapshot('pre', identifier)
            print(f"Transaction: {identifier}\nSnapper root pre: {record['pre']}", flush=True)
            source = root['source'].split('[')[0]
            ancestors = output('lsblk', '-s', '-n', '-r', '-o', 'FSTYPE,UUID', source)
            for line in ancestors.splitlines():
                fields = line.split()
                if len(fields) == 2 and fields[0] == 'crypto_LUKS':
                    record['luks_uuid'] = fields[1]
            (directory/'packages-before.txt').write_text(output('pacman', '-Q')+'\n')
            run('tar', '--one-file-system', '--acls', '--xattrs', '--numeric-owner',
                '-cpf', str(directory/'boot.tar'), '-C', '/boot', '.')
            record['archives']['boot.tar'] = digest(directory/'boot.tar')
            esp = mount_info('/boot/efi')
            if esp['target'] == '/boot/efi':
                record['esp'] = esp
                run('tar', '-cpf', str(directory/'esp.tar'), '-C', '/boot/efi', '.')
                record['archives']['esp.tar'] = digest(directory/'esp.tar')
            record['status'] = 'prepared'
            save(directory, record)
        finally:
            if preparation_lock is not None and db_lock.exists() and db_lock.stat().st_ino == preparation_lock:
                db_lock.unlink()
        try:
            if args.dry_run:
                cache = directory/'check-db'
                env = dict(os.environ, CHECKUPDATES_DB=str(cache), LC_ALL='C.UTF-8')
                result = subprocess.run(['checkupdates', '--nocolor'], env=env, capture_output=True, text=True)
                (directory/'check-result.txt').write_text(result.stdout+result.stderr)
                if result.returncode not in (0, 2):
                    raise RuntimeError('Update check failed; see check-result.txt')
                print(f'Update check: {len(result.stdout.splitlines())} available; no packages installed.', flush=True)
                record['status'] = 'dry-run-complete'
            else:
                print('Recovery backups verified. Starting interactive pacman -Syu.', flush=True)
                run('pacman', '-Syu')
                record['status'] = 'updated'
            record['post'] = snapshot('post', identifier, record['pre'])
            (directory/'packages-after.txt').write_text(output('pacman', '-Q')+'\n')
            if args.dry_run and (directory/'packages-before.txt').read_bytes() != (directory/'packages-after.txt').read_bytes():
                raise RuntimeError('Package inventory changed during dry run; check for a concurrent external updater')
            save(directory, record)
            print(f"Snapper root post: {record['post']}\nBoot backup SHA-256: {record['archives']['boot.tar']}\nResult: {record['status']}")
            print(f'Offline recovery instructions: sudo basaltos-update --recovery-info {identifier}')
            print('Snapshots and boot archives are retained; remove them manually only after verifying the system.')
        except BaseException:
            record['status'] = 'failed'
            save(directory, record)
            print(f'Update failed. Retained pre-snapshot {record["pre"]} and boot backups.', file=sys.stderr)
            print(f'Run: sudo basaltos-update --recovery-info {identifier}', file=sys.stderr)
            raise

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        print(f'basaltos-update: {error}', file=sys.stderr)
        raise SystemExit(1)
