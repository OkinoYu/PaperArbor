#!/usr/bin/env python3
"""Check manifest, index freshness, local links and standalone article assets."""
from __future__ import annotations
import argparse
import base64
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from common import ROOT, load_records
from build_index import render_index

CSS_URL = re.compile(r'url\(\s*[\"\']?(.*?)[\"\']?\s*\)', re.I)

def contained_svg(raw: bytes) -> bool:
    svg = ET.fromstring(raw)
    if not svg.tag.endswith('svg'):
        return False
    for node in svg.iter():
        if node.tag.rsplit('}', 1)[-1].lower() == 'script':
            return False
        for key, value in node.attrib.items():
            if key.rsplit('}', 1)[-1] in ('href', 'src') and not value.startswith('#'):
                return False
        css = (node.text or '') if node.tag.rsplit('}', 1)[-1] == 'style' else ''
        css += node.get('style', '')
        if re.search(r'@import', css, re.I) or any(not m[1].startswith('#') for m in CSS_URL.finditer(css)):
            return False
    return True


def data_image(value: str) -> bool:
    try:
        header, body = value.split(',', 1)
        raw = base64.b64decode(body, validate=True)
        signatures = {
            'data:image/png;base64': lambda b: b.startswith(b'\x89PNG\r\n\x1a\n'),
            'data:image/jpeg;base64': lambda b: b.startswith(b'\xff\xd8\xff'),
            'data:image/webp;base64': lambda b: b.startswith(b'RIFF') and b[8:12] == b'WEBP',
            'data:image/gif;base64': lambda b: b.startswith((b'GIF87a', b'GIF89a')),
            'data:image/svg+xml;base64': contained_svg,
        }
        return bool(raw) and header in signatures and signatures[header](raw)
    except (ValueError, ET.ParseError):
        return False

class Document(HTMLParser):
    def __init__(self, text: str, standalone: bool):
        super().__init__(convert_charrefs=True)
        self.ids = set(); self.links = []; self.errors = []; self.images = 0
        self.labels = []; self.h1 = 0; self.title = False; self.viewport = False; self.lang = False
        self.standalone = standalone
        self.feed(text)
        for label in self.labels:
            if label not in self.ids:
                self.errors.append(f'aria-labelledby references missing id: {label}')
        if not re.match(r'\s*<!doctype html>', text, re.I): self.errors.append('missing HTML doctype')
        if not self.title or self.h1 != 1 or not self.viewport or not self.lang:
            self.errors.append('require title, one h1, viewport, and lang')
        for match in re.finditer(r'<(svg|math)\b.*?</\1>', text, re.S | re.I):
            markup = match.group(0)
            try: ET.fromstring(markup)
            except ET.ParseError as exc: self.errors.append(f'invalid {match.group(1)} XML: {exc}')
        if text.count('<svg') != len(re.findall(r'</svg\s*>', text)) or text.count('<math') != len(re.findall(r'</math\s*>', text)):
            self.errors.append('unclosed SVG or MathML')
        if re.search(r'\$\$|\\\[|\\\(', text): self.errors.append('unrendered LaTeX delimiter')
        if standalone:
            if re.search(r'@import\b', text, re.I): self.errors.append('CSS import is not standalone')
            for match in CSS_URL.finditer(text):
                self.asset(match.group(1), 'CSS url')
    def asset(self, value: str, label: str):
        if value.startswith('#'):
            self.links.append(value)
        elif not data_image(value):
            self.errors.append(f'{label} must be a valid embedded image: {value[:70]}')
        else: self.images += 1
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids: self.errors.append(f'duplicate id: {a["id"]}')
            self.ids.add(a['id'])
        if a.get('aria-labelledby'): self.labels.extend(a['aria-labelledby'].split())
        if tag == 'html': self.lang = bool(a.get('lang'))
        if tag == 'title': self.title = True
        if tag == 'h1': self.h1 += 1
        if tag == 'meta' and a.get('name') == 'viewport': self.viewport = True
        if tag == 'svg' and (not a.get('viewbox') or a.get('role') != 'img' or not a.get('aria-labelledby')):
            # Home decorative tree uses its own title; articles require explicit labels.
            if self.standalone: self.errors.append('SVG requires viewBox, role=img and aria-labelledby')
        if tag == 'math' and not a.get('aria-label'): self.errors.append('MathML needs a readable aria-label')
        if tag == 'a' or tag == 'use':
            value = a.get('href') or a.get('xlink:href')
            if value: self.links.append(value)
        if tag == 'img' and not a.get('alt'): self.errors.append('image needs meaningful alt text') if self.standalone else None
        if tag in ('img','image','source'):
            for attr in ('src','href','xlink:href'):
                if a.get(attr):
                    if self.standalone: self.asset(a[attr], f'{tag} {attr}')
                    else: self.links.append(a[attr])
            if not any(a.get(k) for k in ('src','href','xlink:href','srcset')):
                self.errors.append(f'{tag} needs an image source')
            # Deliberately prohibit srcset in portable articles; a single compressed image is sufficient.
            if a.get('srcset'):
                if self.standalone: self.errors.append('srcset is unsupported; embed a single img src')
                else: self.errors.append('srcset requires explicit validation')
        if tag in ('script','link','iframe','audio','video','object','embed'):
            values = [a.get(k) for k in ('src','href','data','poster') if a.get(k)]
            if self.standalone and (values or tag in ('iframe','audio','video','object','embed')):
                self.errors.append(f'{tag} creates a runtime dependency')
            else: self.links.extend(values)
        if a.get('style') and self.standalone:
            for match in CSS_URL.finditer(a['style']): self.asset(match.group(1), 'inline CSS')
    handle_startendtag = handle_starttag

def check_link(value: str, file: Path, root: Path, docs: dict) -> str | None:
    u = urlsplit(value)
    if u.scheme in ('https', 'http', 'mailto'): return None
    if u.scheme or u.netloc or u.path.startswith('/') or '\\' in u.path:
        return f'nonportable link: {value[:90]}'
    target = (file.parent / unquote(u.path)).resolve() if u.path else file.resolve()
    if not target.is_relative_to(root.resolve()): return f'link escapes site: {value}'
    if not target.is_file(): return f'broken local link: {value}'
    if u.fragment and target.suffix == '.html':
        if target not in docs:
            docs[target] = Document(target.read_text(encoding='utf-8'), False)
        if unquote(u.fragment) not in docs[target].ids: return f'broken anchor: {value}'
    return None

def validate(root: Path = ROOT, check_index: bool = True) -> dict:
    root = root.resolve(); errors = []; docs = {}; images = 0
    try:
        records = load_records(root)
        if check_index and (root/'index.html').read_text(encoding='utf-8') != render_index(records, root):
            errors.append('index.html differs from manifest; rebuild it')
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {'ok': False, 'errors': [f'manifest/index: {exc}'], 'html_files': 0, 'embedded_images': 0}
    files = [root/'index.html'] + sorted((root/'examples').rglob('*.html'))
    tracked = {r['path'] for r in records}
    for f in files:
        standalone = f != root/'index.html'
        if standalone and f.relative_to(root).as_posix() not in tracked:
            errors.append(f'unregistered article: {f.relative_to(root)}')
        d = Document(f.read_text(encoding='utf-8'), standalone); docs[f.resolve()] = d
        images += d.images
        errors.extend(f'{f.relative_to(root)}: {e}' for e in d.errors)
    for f in files:
        for value in docs[f.resolve()].links:
            err = check_link(value, f, root, docs)
            if err: errors.append(f'{f.relative_to(root)}: {err}')
    for css in (root/'assets').glob('*.css'):
        text = css.read_text(encoding='utf-8')
        if '@import' in text: errors.append(f'{css.name}: external CSS import')
        for m in CSS_URL.finditer(text):
            if not m.group(1).startswith('data:'):
                err = check_link(m.group(1), css, root, docs)
                if err: errors.append(f'{css.name}: {err}')
    for r in records:
        if 'evidence' not in r:
            errors.append(f'{r["id"]}: missing evidence ledger'); continue
        try:
            from common import site_path
            ledger = json.loads(site_path(root, r['evidence']).read_text(encoding='utf-8'))
            source_ids = {s['id'] for s in r['sources']}
            if not ledger.get('claims'): raise ValueError('empty evidence ledger')
            for claim in ledger['claims']:
                if claim.get('source') not in source_ids or not claim.get('locator') or not claim.get('statement'):
                    raise ValueError('claim needs source, locator, statement')
                if claim.get('anchor') not in docs[(root/r['path']).resolve()].ids:
                    raise ValueError(f'missing claim anchor: {claim.get("anchor")}')
        except (OSError, ValueError, KeyError, TypeError) as exc: errors.append(f'{r["id"]}: evidence: {exc}')
    return {'ok': not errors, 'errors': errors, 'html_files': len(files), 'embedded_images': images,
            'external_links': 'not fetched; primary evidence requires editorial review'}

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', type=Path, default=ROOT); p.add_argument('--json', action='store_true'); a=p.parse_args()
    report=validate(a.root)
    print(json.dumps(report, ensure_ascii=False, indent=2) if a.json else ('OK' if report['ok'] else 'FAIL') + f": {report['html_files']} HTML files, {report['embedded_images']} embedded images" + ''.join('\n- '+e for e in report['errors']))
    raise SystemExit(0 if report['ok'] else 1)
if __name__ == '__main__': main()
