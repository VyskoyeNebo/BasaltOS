#!/usr/bin/env python3
"""Build the BasaltOS homepage and Markdown documentation with local assets."""
import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote, unquote, urlsplit

import markdown
from markdown.extensions.toc import slugify_unicode

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT/'docs'
REPOSITORY = 'https://github.com/VyskoyeNebo/BasaltOS'
RELEASE = REPOSITORY+'/releases/tag/v0.1.0'
SHA256 = '0fd12156f204a6b6535c19aca1ae0f229e8e8b02579772602e68530034a27281'
GROUPS = [
    ('开始使用', [('QUICKSTART','下载与安装'),('GAMING','游戏与 Proton'),('RELEASE-NOTES-0.1.0','0.1.0 发行说明')]),
    ('安全与维护', [('SECURITY','防火墙、更新与恢复'),('PRIVACY','隐私与联网'),('SECUREBOOT','Secure Boot'),('RELEASE','签名与仓库基础（M6）'),('PUBLISHING','官网与公开发版')]),
    ('构建文档', [('BUILD','M1 构建'),('BUILD-M2','M2 KDE 桌面'),('BUILD-M3','M3 安装器'),('BUILD-M4','M4 游戏套件'),('BUILD-M5','M5 安全加固'),('ENV-NOTES','构建环境记录'),('UPSTREAM','上游来源')]),
    ('验证记录', [(f'M{i}-RESULTS',f'M{i} 验收结果') for i in range(1,8)])
]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--base-path', default='/BasaltOS/')
args = parser.parse_args()
output = args.output.resolve()
if not output.is_relative_to(ROOT/'out'):
    parser.error('Output must be a new directory inside this project out/')
if output.exists():
    parser.error('Output already exists; choose a new directory')
base = '/'+args.base_path.strip('/')+'/' if args.base_path.strip('/') else '/'
output.mkdir(parents=True)
(output/'docs').mkdir()
(output/'downloads').mkdir()
shutil.copytree(DOCS/'site/assets', output/'assets')
sources = {p.resolve(): 'docs/'+p.stem+'.html' for p in sorted(DOCS.glob('*.md'))}
allowed = set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'], cwd=ROOT, text=True).splitlines())
fingerprint = (ROOT/'packaging/basaltos-key.fingerprint').read_text(encoding='ascii').strip()
download_source = ROOT/'out/releases/0.1.0-m6'
for name in ('basaltos-key.asc','SHA256SUMS','SHA256SUMS.asc'):
    source = download_source/name if (download_source/name).exists() else ROOT/'packaging'/name
    if not source.exists():
        raise SystemExit(f'Missing verified release metadata: {name}')
    shutil.copyfile(source, output/'downloads'/name)
shutil.copyfile(ROOT/'scripts/join-iso.py', output/'downloads/join-iso.py')
(output/'downloads/basaltos-0.1.0-m6-x86_64.iso.sha256').write_text(SHA256+'  basaltos-0.1.0-m6-x86_64.iso\n', encoding='ascii')

def head():
    return f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'">
<link rel="icon" href="{base}assets/mark.svg" type="image/svg+xml"><link rel="stylesheet" href="{base}assets/site.css"><script src="{base}assets/site.js" defer></script>'''

def header():
    return f'''<a class="skip" href="#main">跳到正文</a><header class="header"><div class="wrap header-inner"><a class="brand" href="{base}"><img src="{base}assets/mark.svg" alt="" width="31" height="34">BasaltOS</a><nav class="nav" aria-label="主导航"><a href="{base}#features" class="optional">系统特性</a><a href="{base}docs/QUICKSTART.html">文档</a><a href="{REPOSITORY}" class="optional">源代码 ↗</a><a href="{RELEASE}" class="nav-download">下载 0.1.0 ↗</a></nav></div></header>'''

def footer():
    return f'''<footer class="footer"><div class="wrap footer-inner"><span>BasaltOS · Arch Linux + KDE Plasma · 独立发行版项目</span><div><a href="{base}docs/PRIVACY.html">隐私</a><a href="{base}docs/RELEASE-NOTES-0.1.0.html">已知限制</a><a href="{REPOSITORY}">GitHub ↗</a></div></div></footer>'''

def sidebar(current):
    parts = [f'<aside class="sidebar" id="docs-menu" aria-label="文档目录"><div class="search-box"><label class="small" for="doc-search">搜索文档</label><input id="doc-search" type="search" placeholder="输入关键词（至少两个字符）" data-search="{base}search-index.json" autocomplete="off"><div class="search-results" aria-live="polite"></div></div>']
    for title, pages in GROUPS:
        parts.append('<h2>'+html.escape(title)+'</h2>')
        for slug, label in pages:
            if (DOCS/(slug+'.md')).resolve() not in sources:
                continue
            active = ' aria-current="page"' if slug == current else ''
            parts.append(f'<a href="{base}docs/{quote(slug)}.html"{active}>{html.escape(label)}</a>')
    return ''.join(parts)+'</aside>'

def local_url(value, source):
    url = urlsplit(html.unescape(value))
    if url.scheme or url.netloc or not url.path or url.path.startswith('/'):
        return value
    target = (source.parent/unquote(url.path)).resolve()
    if not target.is_relative_to(ROOT):
        raise RuntimeError(f'Link outside project: {source.name}: {value}')
    relative = target.relative_to(ROOT).as_posix()
    suffix = ('?'+url.query if url.query else '')+('#'+url.fragment if url.fragment else '')
    if target in sources:
        return base+quote(sources[target])+suffix
    if relative == 'README.md':
        return REPOSITORY+'/blob/main/README.md'+suffix
    if relative not in allowed or not target.is_file():
        raise RuntimeError(f'Missing/untracked linked resource: {source.name}: {value}')
    destination = 'source/'+relative
    (output/destination).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target, output/destination)
    return base+quote(destination)+suffix

class LinkRewriter(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.parts = []
    def handle_starttag(self, tag, attrs):
        attributes = []
        for key, value in attrs:
            if key in ('href','src') and value:
                value = local_url(value, self.source)
            attributes.append(' '+key if value is None else f' {key}="{html.escape(value, quote=True)}"')
        self.parts.append('<'+tag+''.join(attributes)+'>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag): self.parts.append('</'+tag+'>')
    def handle_data(self, data): self.parts.append(data)
    def handle_entityref(self, name): self.parts.append('&'+name+';')
    def handle_charref(self, name): self.parts.append('&#'+name+';')
    def handle_comment(self, data): self.parts.append('<!--'+data+'-->')

search = []
for source, destination in sources.items():
    text = source.read_text(encoding='utf-8')
    match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = match.group(1) if match else source.stem
    renderer = markdown.Markdown(extensions=['extra','toc','sane_lists'], extension_configs={'toc':{'slugify':slugify_unicode,'toc_depth':'2-3'}}, output_format='html')
    fragment = renderer.convert(text)
    rewriter = LinkRewriter(source)
    rewriter.feed(fragment)
    content = ''.join(rewriter.parts)
    historical = ''
    if re.match(r'(?:M[1-6]-RESULTS|BUILD(?:-M[2-5])?|RELEASE)$', source.stem):
        historical = f'<div class="historical">这份文档保留对应里程碑的原始记录，部分路径与地址属于当时的本地环境。当前公开版请先阅读<a href="{base}docs/QUICKSTART.html">快速开始</a>与<a href="{base}docs/RELEASE-NOTES-0.1.0.html">0.1.0 发行说明</a>。</div>'
    toc = renderer.toc if len(renderer.toc_tokens)>0 and renderer.toc != '<div class="toc">\n<ul></ul>\n</div>\n' else ''
    page = f'''<!doctype html><html lang="zh-CN"><head>{head()}<title>{html.escape(title)} · BasaltOS 文档</title></head><body>{header()}<main id="main" class="wrap docs-layout"><div><button class="docs-toggle" type="button" aria-expanded="false" aria-controls="docs-menu">文档目录与搜索</button>{sidebar(source.stem)}</div><article class="doc"><div class="doc-meta"><span>BasaltOS / 文档</span><a href="{REPOSITORY}/blob/main/docs/{quote(source.name)}">查看 Markdown 源文 ↗</a></div>{historical}{content if not toc else content.replace('</h1>','</h1>'+toc,1)}</article></main>{footer()}</body></html>'''
    (output/destination).write_text(page, encoding='utf-8', newline='\n')
    search.append({'title':title,'url':base+destination,'text':re.sub(r'[`#*\[\]<>]',' ',text)})

template = (DOCS/'site/index.html').read_text(encoding='utf-8')
for marker, value in {'HEAD':head(),'HEADER':header(),'FOOTER':footer(),'BASE':base,'RELEASE_URL':RELEASE,'SHA256':SHA256,'FINGERPRINT':fingerprint}.items():
    template = template.replace('{{'+marker+'}}', value)
assert '{{' not in template
(output/'index.html').write_text(template, encoding='utf-8', newline='\n')
for source in DOCS.glob('*.png'):
    shutil.copyfile(source, output/'docs'/source.name)
(output/'search-index.json').write_text(json.dumps(search, ensure_ascii=False), encoding='utf-8')
(output/'.nojekyll').touch()
(output/'robots.txt').write_text('User-agent: *\nAllow: /\n', encoding='ascii')
(output/'404.html').write_text(f'<!doctype html><html lang="zh-CN"><head>{head()}<title>未找到页面 · BasaltOS</title></head><body>{header()}<main id="main" class="wrap section"><h1>页面不在这里。</h1><p><a href="{base}">返回首页</a>，或从文档目录继续。</p></main>{footer()}</body></html>', encoding='utf-8')
print(f'Built {len(sources)} documentation pages and homepage: {output}')
