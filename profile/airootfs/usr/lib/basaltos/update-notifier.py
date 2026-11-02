"""Read local check results; this desktop process performs no network requests."""
import json
import os
from pathlib import Path
import subprocess
import time

if Path('/run/archiso/bootmnt').exists():
    raise SystemExit(0)
state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state')))/'basaltos-update'
state.mkdir(parents=True, exist_ok=True)
marker = state/'last-notified'
while True:
    try:
        data = json.loads(Path('/var/lib/basaltos-update-check/result.json').read_text())
        stamp = data['checked_at']
        if (not marker.exists() or marker.read_text() != stamp) and data['status'] != 'current':
            message = (f"发现 {len(data['updates'])} 个软件包更新。打开 Konsole，运行 sudo basaltos-update。"
                       if data['status'] == 'updates' else '更新检查失败，请检查网络并查看 basaltos-update-check.service 日志。')
            subprocess.run(['/usr/bin/notify-send', '-a', 'BasaltOS', '系统更新', message], check=True)
            marker.write_text(stamp)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError):
        pass
    time.sleep(60)
