"""Only synchronize an isolated database and publish a local notification record."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

cache = Path('/var/cache/basaltos-update-check')
state = Path('/var/lib/basaltos-update-check')
cache.mkdir(parents=True, exist_ok=True)
state.mkdir(parents=True, exist_ok=True)
with (cache/'check.lock').open('w') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    env = dict(os.environ, CHECKUPDATES_DB=str(cache/'db'), LC_ALL='C.UTF-8')
    result = subprocess.run(['/usr/bin/checkupdates', '--nocolor'], env=env,
                            capture_output=True, text=True)
    data = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status': 'updates' if result.returncode == 0 else
                      'current' if result.returncode == 2 else 'error',
            'updates': result.stdout.splitlines(), 'error': result.stderr.strip()}
    temporary = state/'result.json.tmp'
    temporary.write_text(json.dumps(data, ensure_ascii=False)+'\n')
    temporary.chmod(0o644)
    temporary.replace(state/'result.json')
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0 if result.returncode in (0, 2) else 1)
