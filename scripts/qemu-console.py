#!/usr/bin/env python3
"""Operate a real QEMU VGA console over a local QMP connection."""
import argparse
import json
import socket
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=['status', 'snapshot', 'type', 'key', 'click', 'reset', 'powerdown', 'quit'])
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=4444)
parser.add_argument('--filename', default='/root/BasaltOS/out/m1-qemu.png')
parser.add_argument('--text')
parser.add_argument('--key', help='QEMU key chord, for example ctrl-alt-t or ctrl-spc')
parser.add_argument('--no-enter', action='store_true')
parser.add_argument('--x', type=int)
parser.add_argument('--y', type=int)
parser.add_argument('--width', type=int, default=1280)
parser.add_argument('--height', type=int, default=800)
parser.add_argument('--double', action='store_true', help='Double-click for desktop launchers')
args = parser.parse_args()
try:
    connection = socket.create_connection((args.host, args.port), timeout=10)
except OSError as error:
    parser.exit(1, f'QMP unavailable at {args.host}:{args.port}: {error}. '
                'Check that the BasaltOS QEMU test VM is running and uses this port.\n')
stream = connection.makefile('rwb', buffering=0)
greeting = stream.readline()
if not greeting:
    raise RuntimeError('QMP closed before greeting; check that QEMU is still running')
json.loads(greeting)

def command(name, arguments=None):
    request = {'execute': name}
    if arguments:
        request['arguments'] = arguments
    stream.write(json.dumps(request).encode()+b'\n')
    while True:
        line = stream.readline()
        if not line and name == 'quit':
            return {}
        if not line:
            raise RuntimeError('QMP connection closed unexpectedly')
        response = json.loads(line)
        if 'error' in response:
            raise RuntimeError(response['error'])
        if 'return' in response:
            return response['return']

command('qmp_capabilities')
if args.action == 'status':
    print(json.dumps(command('query-status')))
elif args.action == 'snapshot':
    command('screendump', {'filename': args.filename, 'format': 'png'})
    print(f'Real VGA screenshot saved in QEMU host filesystem: {args.filename}')
elif args.action == 'quit':
    command('quit')
elif args.action in ('reset', 'powerdown'):
    command('system_reset' if args.action == 'reset' else 'system_powerdown')
elif args.action == 'click':
    if args.x is None or args.y is None or not (0 <= args.x < args.width and 0 <= args.y < args.height):
        parser.error('click requires valid --x/--y and screenshot dimensions')
    events = [{'type': 'abs', 'data': {'axis': axis, 'value': value}}
              for axis, value in [('x', round(args.x * 32767 / (args.width - 1))),
                                  ('y', round(args.y * 32767 / (args.height - 1)))]]
    command('input-send-event', {'events': events})
    for _ in range(2 if args.double else 1):
        command('input-send-event', {'events': [{'type': 'btn', 'data': {'button': 'left', 'down': True}}]})
        time.sleep(0.08)
        command('input-send-event', {'events': [{'type': 'btn', 'data': {'button': 'left', 'down': False}}]})
        time.sleep(0.08)
elif args.action == 'key':
    if not args.key:
        parser.error('key requires --key')
    command('send-key', {'keys': [{'type':'qcode','data':key} for key in args.key.split('-')], 'hold-time': 100})
else:
    if args.text is None:
        parser.error('type requires --text')
    plain = {' ': 'spc', ';': 'semicolon', '-': 'minus', '.': 'dot', '\n': 'ret',
             '=': 'equal', '/': 'slash', "'": 'apostrophe', '[': 'bracket_left',
             ']': 'bracket_right', '\\': 'backslash', ',': 'comma', '`': 'grave_accent'}
    shifted = {'_': 'minus', ':': 'semicolon', '>': 'dot', '<': 'comma', '?': 'slash',
               '"': 'apostrophe', '$': '4', '&': '7', '|': 'backslash', '!': '1',
               '(': '9', ')': '0', '%': '5', '+': 'equal', '*': '8', '#': '3', '@': '2'}
    for character in args.text+('' if args.no_enter else '\n'):
        if character.isupper():
            keys = ['shift', character.lower()]
        elif character in shifted:
            keys = ['shift', shifted[character]]
        elif character in plain:
            keys = [plain[character]]
        elif character.isascii() and character.isalnum():
            keys = [character]
        else:
            raise ValueError(f'Unsupported US keyboard character: {character!r}')
        command('send-key', {'keys': [{'type': 'qcode', 'data': key} for key in keys], 'hold-time': 20})
        time.sleep(0.05)
    print('Command typed into the real VGA console.')
stream.close()
connection.close()
