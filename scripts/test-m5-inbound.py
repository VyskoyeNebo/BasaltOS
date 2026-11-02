#!/usr/bin/env python3
"""Host-side allow/drop comparison on the dedicated QEMU M5 probe only."""
import http.client
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
console = root/'scripts/qemu-console.py'
result = {}

def command(text):
    subprocess.run([sys.executable, str(console), 'type', '--port', '4455', '--text', text], check=True)

def request():
    client = http.client.HTTPConnection('127.0.0.1', 18085, timeout=3)
    try:
        client.request('GET', '/')
        response = client.getresponse()
        return response.status, response.read().decode()
    finally:
        client.close()

def blocked(key):
    try:
        status, body = request()
    except OSError as error:
        result[key] = {'blocked': True, 'error': str(error)}
    else:
        raise RuntimeError(f'Unexpected response under drop policy: {status} {body!r}')

ready = root/'work/m5/inbound-ready.txt'
previous = ready.stat().st_mtime_ns if ready.exists() else 0
command('curl -fsS http://10.0.2.2:8181/scripts/probe-m5-inbound.sh -o /tmp/probe.sh && bash /tmp/probe.sh > /tmp/probe-console.log 2>&1 &')
deadline = time.monotonic()+15
while not ready.exists() or ready.stat().st_mtime_ns == previous:
    if time.monotonic() > deadline:
        raise RuntimeError('Guest probe did not become ready')
    time.sleep(0.2)
try:
    blocked('default')
    command('nft insert rule inet basaltos_filter input tcp dport 18085 accept')
    time.sleep(0.5)
    status, body = request()
    assert status == 200 and body.strip() == 'M5 loopback test', (status, body)
    result['temporary_allow'] = {'status': status, 'body': body.strip()}
finally:
    command('systemctl reload nftables')
time.sleep(0.5)
blocked('restored_default')
(root/'work/m5/inbound-host-test.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
