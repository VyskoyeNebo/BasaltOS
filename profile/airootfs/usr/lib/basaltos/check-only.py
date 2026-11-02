"""Query enabled repositories using temporary databases and public key material."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

def value(name):
    return subprocess.check_output(['pacman-conf', name], text=True).strip()

def main():
    database = Path(value('DBPath'))
    keyring = Path(value('GPGDir'))
    if not (database/'local').is_dir():
        raise RuntimeError('Installed package database is missing')
    with tempfile.TemporaryDirectory(prefix='basaltos-check-only-') as temporary:
        work = Path(temporary)
        db = work/'db'
        public = work/'gnupg'
        db.mkdir()
        public.mkdir(mode=0o700)
        (db/'local').symlink_to(database/'local', target_is_directory=True)
        for filename in ('pubring.gpg', 'pubring.kbx', 'trustdb.gpg', 'gpg.conf'):
            if (keyring/filename).is_file():
                shutil.copyfile(keyring/filename, public/filename)
        if not any((public/name).exists() for name in ('pubring.gpg', 'pubring.kbx')):
            raise RuntimeError('Initialize the trusted pacman public keyring first')
        options = ['--config', '/etc/pacman.conf', '--dbpath', str(db),
                   '--gpgdir', str(public), '--logfile', '/dev/null']
        env = dict(os.environ, LC_ALL='C.UTF-8')
        repositories = subprocess.check_output(['pacman-conf', '--repo-list'], text=True).splitlines()
        print('BasaltOS check-only: '+', '.join(repositories), flush=True)
        try:
            subprocess.run(['fakeroot', '--', 'pacman', '--disable-sandbox-filesystem',
                            *options, '-Sy', '--noconfirm'], env=env, check=True)
            result = subprocess.run(['pacman', *options, '-Qu'], env=env,
                                    text=True, capture_output=True)
            if result.returncode not in (0, 1) or result.stderr.strip():
                raise RuntimeError(result.stderr.strip() or 'Package query failed')
            print(result.stdout, end='')
            print(f'Check complete: {len(result.stdout.splitlines())} updates; no packages installed, no snapshots created.')
            print('Real pacman databases and keyring were not changed.')
        finally:
            subprocess.run(['gpgconf', '--homedir', str(public), '--kill', 'all'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'basaltos-update --check-only: {error}')
