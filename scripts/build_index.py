#!/usr/bin/env python3
"""Generate a portable, progressively enhanced catalog from papers.json."""
import argparse
import html
import json
from pathlib import Path
from common import ROOT, CATEGORIES, atomic_write, load_records

def render_index(records: list, root: Path = ROOT) -> str:
    def e(s): return html.escape(str(s), quote=True)
    cards = []
    for r in sorted(records, key=lambda r: (r['added'], r['id']), reverse=True):
        cards.append(f'''<article class="paper-card" data-id="{e(r['id'])}">
<div class="card-meta"><span>{e(r['category'])}</span><span>{e(r['type'])} / {len(r['sources']):02} papers</span></div>
<h3><a href="{e(r['path'])}">{e(r['title'])}<span aria-hidden="true"> ↗</span></a></h3>
<p>{e(r['summary'])}</p><div class="tags">{''.join('<span>'+e(t)+'</span>' for t in r['tags'])}</div>
<div class="card-foot"><span>论文发布 <time datetime="{e(r['published'])}">{e(r['published'])}</time></span><span>收录 {e(r['added'])}</span></div></article>''')
    payload = json.dumps(records, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (root / 'templates/index.html').read_text(encoding='utf-8')
    return template.replace('{{CARDS}}', '\n'.join(cards)).replace('{{DATA}}', payload).replace('{{COUNT}}', str(len(records))).replace('{{CATEGORIES}}', ''.join(f'<button type="button" data-category="{c}" aria-pressed="false">{c}</button>' for c in CATEGORIES))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--check', action='store_true', help='fail if generated index is stale')
    a = p.parse_args(); result = render_index(load_records(a.root), a.root)
    target = a.root / 'index.html'
    if a.check:
        if not target.exists() or target.read_text(encoding='utf-8') != result:
            p.exit(1, 'index.html is stale; run build_index.py\n')
    else:
        atomic_write(target, result)
    print('OK: index.html synchronized')
if __name__ == '__main__': main()
