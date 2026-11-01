#!/usr/bin/env python3
"""Boot evidence via real serial console and QMP VGA screendump; no synthetic terminal."""
import json
from pathlib import Path
import re
import socket
import struct
import sys
import time
import zlib

runtime = Path(sys.argv[1])
project = Path(sys.argv[2])
serial = socket.socket(socket.AF_UNIX)
serial.connect(str(runtime / 'serial.sock'))
serial.settimeout(2)
qmp = socket.socket(socket.AF_UNIX)
qmp.connect(str(runtime / 'qmp.sock'))
qfile = qmp.makefile('rwb', buffering=0)
json.loads(qfile.readline())

def command(name, arguments=None):
    payload = {'execute': name}
    if arguments:
        payload['arguments'] = arguments
    qfile.write(json.dumps(payload).encode() + b'\n')
    while True:
        result = json.loads(qfile.readline())
        if 'error' in result:
            raise RuntimeError(result)
        if 'return' in result:
            return result['return']

command('qmp_capabilities')
transcript = bytearray()
log = (project / 'out/m1-qemu-serial.txt').open('wb')

def wait_for(pattern, timeout=600):
    start = len(transcript)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            block = serial.recv(65536)
        except socket.timeout:
            continue
        if not block:
            raise RuntimeError('QEMU serial connection closed')
        transcript.extend(block)
        log.write(block)
        log.flush()
        if re.search(pattern, transcript[start:]):
            return
    raise TimeoutError(f'Console wait timed out: {pattern!r}; see serial log')

wait_for(rb'root@basaltos[^\r\n]*#')
print('QEMU reached root@basaltos shell', flush=True)
check = "test \"$(hostname)\" = basaltos && test \"$(id -u)\" = 0 && ip -4 -o a show scope global | grep -q inet && ping -c 3 -W 5 mirrors.tuna.tsinghua.edu.cn && test \"$(cat /etc/locale.conf)\" = LANG=zh_CN.UTF-8 && test \"$(readlink /etc/localtime)\" = /usr/share/zoneinfo/Asia/Shanghai && locale -a | grep -qi zh_CN.utf8 && grep -qx KEYMAP=us /etc/vconsole.conf && grep -q mirrors.tuna.tsinghua.edu.cn /etc/pacman.conf"
serial.sendall(("LC_ALL=C bash -c '" + check + "'; printf '\\nM1_RESULT=%s\\n' \"$?\"\n").encode())
wait_for(rb'\r?\nM1_RESULT=\d+\r?\n', 120)
result = re.search(rb'\r?\nM1_RESULT=(\d+)\r?\n', transcript)
if result.group(1) != b'0':
    raise RuntimeError('M1 guest checks failed; inspect serial evidence')
print('QEMU guest hostname/root/address/ping/locale/timezone checks passed', flush=True)

# Type into the real VGA tty1 root shell so the screenshot shows a genuine command and prompt.
keycodes = {' ': 'spc', ';': 'semicolon', '-': 'minus', '.': 'dot', '\n': 'ret', '=': 'equal'}
text = 'export LC_ALL=C; clear; hostname; id; ip -br a; ping -c 3 mirrors.tuna.tsinghua.edu.cn\n'
for character in text:
    codes = [keycodes.get(character, character)]
    if character.isupper():
        codes = ['shift', character.lower()]
    elif character == '_':
        codes = ['shift', 'minus']
    command('send-key', {'keys': [{'type': 'qcode', 'data': code} for code in codes], 'hold-time': 20})
    time.sleep(0.05)
time.sleep(8)
ppm = runtime / 'screen.ppm'
command('screendump', {'filename': str(ppm)})
with ppm.open('rb') as source:
    assert source.readline().strip() == b'P6'
    dimensions = source.readline()
    while dimensions.startswith(b'#'):
        dimensions = source.readline()
    width, height = map(int, dimensions.split())
    assert source.readline().strip() == b'255'
    pixels = source.read()
assert len(pixels) == width * height * 3

def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)

scanlines = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b'')
(project / 'out/m1-qemu.png').write_bytes(png)
(project / 'out/m1-qemu-result.json').write_text(json.dumps({
    'passed': True, 'accelerator': 'tcg', 'boot': 'BIOS ISO',
    'hostname': 'basaltos', 'uid': 0, 'ipv4': True,
    'ping': 'mirrors.tuna.tsinghua.edu.cn', 'locale': 'zh_CN.UTF-8',
    'timezone': 'Asia/Shanghai', 'keymap': 'us', 'mirror': 'TUNA',
    'screenshot': 'docs/m1-qemu.png',
}, indent=2) + '\n')
print(f'QMP VGA screenshot saved: {width}x{height}', flush=True)
command('quit')
log.close()
