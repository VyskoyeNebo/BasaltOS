#!/usr/bin/env python3
"""Operate a real QEMU VGA console over a local QMP connection."""
import argparse
import json
import socket
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=['status', 'snapshot', 'type', 'key', 'quit'])
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=4444)
parser.add_argument('--filename', default='/root/BasaltOS/out/m1-qemu.png')
parser.add_argument('--text')
parser.add_argument('--key', help='QEMU key chord, for example ctrl-alt-t or ctrl-spc')
parser.add_argument('--no-enter', action='store_true')
args = parser.parse_args()
connection = socket.create_connection((args.host, args.port), timeout=10)
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
