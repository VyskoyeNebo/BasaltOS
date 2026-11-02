#!/usr/bin/env python3
"""Validate generated internal links, anchors and local-only web resources."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--base-path', default='/BasaltOS/')
args = parser.parse_args()
root = args.site.resolve()
base = '/'+args.base_path.strip('/')+'/' if args.base_path.strip('/') else '/'

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.title = False
        self.h1 = 0
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'): self.ids.add(values['id'])
        if tag == 'title': self.title = True
        if tag == 'h1': self.h1 += 1
        for attribute in ('href','src','data-search'):
            if values.get(attribute):
                resource = attribute != 'href' or tag == 'link'
                self.links.append((values[attribute], resource))

pages = {}
errors = []
for path in root.rglob('*.html'):
    page = Page()
    page.feed(path.read_text(encoding='utf-8'))
    pages[path] = page
    if not page.title: errors.append(f'{path.name}: missing title')
    if page.h1 != 1: errors.append(f'{path.name}: expected one h1, got {page.h1}')

for path, page in pages.items():
    for value, resource in page.links:
        url = urlsplit(value)
        if url.scheme or url.netloc:
            if resource: errors.append(f'{path.name}: external resource {value}')
            continue
        if url.path.startswith(base):
            target = root/unquote(url.path[len(base):])
        elif url.path.startswith('/'):
            errors.append(f'{path.name}: escapes Pages base {value}')
            continue
        elif not url.path:
            target = path
        else:
            target = path.parent/unquote(url.path)
        target = target.resolve()
        if target.is_dir(): target /= 'index.html'
        if not target.is_relative_to(root) or not target.is_file():
            errors.append(f'{path.relative_to(root)}: missing {value}')
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f'{path.name}: missing anchor {value}')

for stylesheet in root.rglob('*.css'):
    text = stylesheet.read_text(encoding='utf-8')
    if re.search(r'@import|url\(\s*["\x27]?(?:https?:)?//', text, re.I):
        errors.append(f'External stylesheet/font import: {stylesheet.name}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(pages)} HTML pages, internal links/anchors and local resources verified.')
