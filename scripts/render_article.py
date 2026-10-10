#!/usr/bin/env python3
"""Render authored HTML with stable navigation and optional offline evidence."""
import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from common import ROOT
from evidence import LABELS, json_script, reader_payload, validate_evidence


class Headings(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.entries = []; self.current = None; self.ids = set()
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            if attrs['id'] in self.ids:
                raise ValueError(f'duplicate body id: {attrs["id"]}')
            self.ids.add(attrs['id'])
        if tag == 'h1':
            raise ValueError('body must not contain h1')
        if tag in ('h2', 'h3'):
            self.current = [attrs.get('id'), '', tag]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if self.current is not None and tag == self.current[2]:
            if not self.current[0]:
                raise ValueError(f'every {tag} needs a stable id after normalization')
            self.entries.append(tuple(self.current)); self.current = None


def prepare_body(body):
    # Deterministic h3 ids belong to their parent section; explicit authored ids win.
    section = 'section'; counts = {}; used = set(re.findall(r'\bid=["\']([^"\']+)', body))
    def heading(match):
        nonlocal section
        tag, attrs = match.group(1), match.group(2)
        ident = re.search(r'\bid=["\']([^"\']+)', attrs)
        if tag == 'h2':
            if not ident: raise ValueError('every h2 needs a stable id')
            section = ident[1]
        elif not ident:
            counts[section] = counts.get(section, 0) + 1
            ident = f'{section}-part-{counts[section]}'
            while ident in used:
                counts[section] += 1; ident = f'{section}-part-{counts[section]}'
            used.add(ident)
            attrs += f' id="{html.escape(ident, quote=True)}"'
        return '<' + tag + attrs + '>'
    return re.sub(r'<(h2|h3)\b([^>]*)>', heading, body)


def evidence_notes(entry, ledger):
    e = html.escape
    sources = {s['id']: s for s in entry['sources']}
    notes = []
    for n, claim in enumerate(ledger['claims'], 1):
        source = sources[claim['source']]
        notes.append(f'<li id="evidence-claim-{n}"><span class="label">{e(LABELS.get(claim.get("kind"), "证据"))}</span>'
                     f'<p>{e(claim["statement"])}</p><p class="source">{e(source["title"])} · {e(source["version"])}<br>'
                     f'{e(claim["locator"])}</p><a href="{e(source["url"], quote=True)}">打开原始来源 ↗</a> · '
                     f'<a href="#{e(claim["anchor"], quote=True)}">返回对应正文 ↑</a></li>')
    return (f'<section class="evidence-section" aria-labelledby="evidence-heading"><h2 id="evidence-heading">证据索引</h2>'
            f'<p class="source">{e(ledger.get("coverage", "逐项来源记录；静态检查不替代科学复核。"))}</p>'
            f'<details id="evidence-notes"><summary>展开全部 {len(notes)} 条证据（断网可查）</summary><ol class="evidence-list">'
            + ''.join(notes) + '</ol></details></section>')


def link_sources(body, sources):
    urls = {s['url']: s['id'] for s in sources}
    def annotate(match):
        attrs = match[1]
        href = re.search(r'\bhref=["\']([^"\']+)', attrs)
        if not href or 'data-source=' in attrs: return match[0]
        # Explicit PDF/download links remain direct actions. Only primary citations open the reader.
        url = html.unescape(href[1]); source = urls.get(url)
        if source:
            return '<a' + attrs + f' data-source="{html.escape(source, quote=True)}">'
        return match[0]
    return re.sub(r'<a\b([^>]*)>', annotate, body)


def related_notes(entry, records):
    e = html.escape; result = []
    own = {re.sub(r'v\d+$', '', s['id']).casefold() for s in entry['sources']}
    for r in records:
        if r['id'] == entry['id']: continue
        shared = own & {re.sub(r'v\d+$', '', s['id']).casefold() for s in r['sources']}
        tags = sorted(set(entry['tags']) & set(r['tags']))
        reason = '共同原始来源' if shared else ('共同标签：' + '、'.join(tags[:3]) if tags else '')
        if reason:
            result.append((bool(shared), len(tags), r, reason))
    result.sort(key=lambda item: (item[0], item[1], item[2]['id']), reverse=True)
    if not result: return ''
    cards = ''.join(f'<li><a href="../../{e(r["path"], quote=True)}">{e(r["title"])}</a><small>{e(reason)}</small></li>'
                    for _, _, r, reason in result[:3])
    return '<aside class="related-reading" aria-label="关联阅读"><h3>关联阅读</h3><p class="source">按共同来源或标签关联，不代表已证明学术继承。</p><ul>' + cards + '</ul></aside>'


def render(body, title, subtitle, category, mode, root=ROOT, *, entry=None, ledger=None, standalone=False, records=None):
    e = html.escape
    body = prepare_body(body)
    parsed = Headings(body); entries = parsed.entries
    if not any(tag == 'h2' for _, _, tag in entries): raise ValueError('article needs h2 sections')
    reserved = {'article', 'top', 'print', 'progress', 'evidence-heading', 'evidence-notes', 'evidence-data',
                'evidence-dialog', 'evidence-dialog-title', 'evidence-search', 'evidence-results', 'evidence-count',
                'figure-dialog', 'figure-dialog-title'}
    if parsed.ids & reserved or any(i.startswith('evidence-claim-') for i in parsed.ids):
        raise ValueError('body id collides with reader layout')
    if (entry is None) != (ledger is None): raise ValueError('entry and evidence must be supplied together')
    notes = ''; payload = ''; related = ''
    if entry is not None:
        validate_evidence(ledger, entry['sources'], parsed.ids)
        body = link_sources(body, entry['sources'])
        notes = evidence_notes(entry, ledger)
        payload = f'<script id="evidence-data" type="application/json">{json_script(reader_payload(entry, ledger))}</script>'
        if not standalone and records is not None: related = related_notes(entry, records)
    toc = ''.join(f'<a class="toc-{tag}" href="#{e(i, quote=True)}">{e(t)}</a>' for i, t, tag in entries)
    if notes: toc += '<a class="toc-h2" href="#evidence-heading">证据索引</a>'
    css = (root/'assets/article.css').read_text(encoding='utf-8')
    js = (root/'assets/article.js').read_text(encoding='utf-8')
    home = '<a href="../../index.html">↖ PaperArbor</a>' if not standalone else '<a href="#top">↖ PaperArbor</a>'
    foot = '<a href="../../index.html">← 返回知识库</a>' if not standalone else '<a href="#top">↑ 返回顶部</a>'
    evidence_button = '<a class="evidence-entry" href="#evidence-heading" data-evidence="">查证</a>' if notes else ''
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{e(subtitle, quote=True)}"><title>{e(title)} · PaperArbor</title><style>{css}</style></head>
<body><a class="skip" href="#article">跳到正文</a><header class="reading-bar">{home}<span>{e(category)} / {e(mode)} / RESEARCH NOTE</span><div class="reader-actions">{evidence_button}<button id="print" type="button">打印 / 保存 PDF</button></div></header><div id="progress" aria-hidden="true"></div>
<div class="reading-layout"><aside class="toc" aria-label="文章目录"><p>ON THIS PAGE</p>{toc}<a href="#top">回到顶部 ↑</a></aside><main id="article"><header id="top" class="article-head"><p class="eyebrow">PAPERARBOR / {e(mode.upper())}</p><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p><p class="meta">中文技术解读 · 来源范围见正文 · 离线可读</p></header><details class="mobile-toc"><summary>目录 / 跳转到章节</summary><nav aria-label="移动文章目录">{toc}</nav></details>{body}{related}{notes}<footer class="article-footer">{foot}<span>Where Papers Grow into Knowledge.</span></footer></main></div>{payload}<script>{js}</script></body></html>'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('body', type=Path)
    p.add_argument('--title'); p.add_argument('--subtitle'); p.add_argument('--category'); p.add_argument('--type', choices=['Single','Series','Digest','Radar'])
    group = p.add_mutually_exclusive_group(); group.add_argument('--entry', type=Path); group.add_argument('--entry-id')
    p.add_argument('--evidence', type=Path); p.add_argument('--standalone', action='store_true')
    p.add_argument('-o', '--output', type=Path, required=True)
    a = p.parse_args()
    try:
        records = json.loads((ROOT/'data/papers.json').read_text()) if a.entry_id or (a.entry and not a.standalone) else None
        entry = json.loads(a.entry.read_text()) if a.entry else next((r for r in records or [] if r['id'] == a.entry_id), None)
        if a.entry_id and entry is None: raise ValueError('unknown entry id')
        ledger_path = a.evidence or (ROOT/entry['evidence'] if a.entry_id else None)
        ledger = json.loads(ledger_path.read_text()) if ledger_path else None
        title = a.title or (entry or {}).get('title'); subtitle = a.subtitle or (entry or {}).get('summary')
        category = a.category or (entry or {}).get('category'); mode = a.type or (entry or {}).get('type')
        if not all((title, subtitle, category, mode)): raise ValueError('supply title, subtitle, category and type, or an entry')
        result = render(a.body.read_text(encoding='utf-8'), title, subtitle, category, mode,
                        entry=entry, ledger=ledger, standalone=a.standalone, records=records)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('x', encoding='utf-8') as f: f.write(result)
    except (ValueError, OSError, KeyError, TypeError) as exc: p.exit(1, f'render failed: {exc}\n')
    print(a.output)

if __name__ == '__main__': main()
