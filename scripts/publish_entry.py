#!/usr/bin/env python3
"""Validate an isolated site candidate, then publish HTML, evidence, manifest, index."""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from common import ROOT, atomic_write, load_records, site_path, validate_records
from build_index import render_index
from validate_site import validate
from article_paths import redirect_html, rewrite_links

def publish(root: Path, entry: dict, article: Path, evidence: Path, replace=False, dry_run=False, move=False):
    root=root.resolve(); lock=root/'.publish.lock'
    fd=os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd);fd=None
        records=load_records(root)
        previous=next((r for r in records if r['id'].casefold()==entry['id'].casefold()),None)
        if previous and not replace: raise ValueError('record exists; review it and use --replace only for an intended revision')
        if replace and not previous: raise ValueError('--replace requires an existing id')
        if move and not replace: raise ValueError('--move requires --replace')
        moving = previous is not None and entry['path'] != previous['path']
        if previous and (entry['evidence']!=previous['evidence'] or (moving and not move)):
            raise ValueError('revision must preserve paths; an explicit article move needs --move')
        if moving and previous['path'] not in entry.get('aliases', []):
            raise ValueError('move must register the previous article path as an alias')
        if previous and not set(previous.get('aliases', [])).issubset(entry.get('aliases', [])):
            raise ValueError('revision must preserve existing aliases')
        if previous and entry['added'] != previous['added']:
            raise ValueError('revision must preserve original added date')
        dest=site_path(root,entry['path']); evdest=site_path(root,entry['evidence'])
        if not entry['evidence'].startswith('data/evidence/') or evdest.suffix!='.json': raise ValueError('evidence must be data/evidence/*.json')
        if dest==evdest: raise ValueError('HTML and evidence paths collide')
        if not previous and (dest.exists() or evdest.exists()): raise ValueError('refusing to overwrite an existing file')
        if moving and dest.exists(): raise ValueError('move refuses an existing destination')
        alias_paths = {site_path(root, a) for a in entry.get('aliases', [])}
        owned = {site_path(root, a) for a in previous.get('aliases', [])} if previous else set()
        if moving: owned.add(site_path(root, previous['path']))
        if any(p.exists() and p not in owned for p in alias_paths):
            raise ValueError('refusing to overwrite an existing alias file')
        records=[r for r in records if not previous or r['id']!=previous['id']]+[entry]
        validate_records(records,root,require_files=False)
        text=article.read_text(encoding='utf-8'); ledger=evidence.read_text(encoding='utf-8'); json.loads(ledger)
        with tempfile.TemporaryDirectory(prefix='paperarbor-stage-') as td:
            stage=Path(td)
            for name in ('templates','assets','data','examples'):
                shutil.copytree(root/name,stage/name)
            if (root/'articles').is_dir():
                shutil.copytree(root/'articles',stage/'articles')
            atomic_write(stage/entry['path'],text);atomic_write(stage/entry['evidence'],ledger)
            extras = {}
            for alias in entry.get('aliases', []):
                value = redirect_html(stage/alias, stage/entry['path'], entry['title'])
                atomic_write(stage/alias, value);extras[root/alias] = value
            if moving:
                for path in (stage/'examples').rglob('*.html'):
                    value = path.read_text(encoding='utf-8')
                    revised = rewrite_links(value, path, (stage/previous['path']).resolve(), (stage/entry['path']).resolve())
                    if revised != value:
                        atomic_write(path, revised)
                        extras[root/path.relative_to(stage)] = revised
            manifest=json.dumps(records,ensure_ascii=False,indent=2)+'\n'
            atomic_write(stage/'data/papers.json',manifest)
            index=render_index(records,stage);atomic_write(stage/'index.html',index)
            report=validate(stage)
            if not report['ok']: raise ValueError('\n'.join(report['errors']))
            if dry_run: return report
            updates={dest:(stage/entry['path']).read_text(encoding='utf-8'),evdest:ledger,root/'data/papers.json':manifest,root/'index.html':index,**extras}
            old={p:p.read_bytes() if p.exists() else None for p in updates}
            try:
                for path,content in updates.items(): atomic_write(path,content)
            except Exception:
                for path,content in old.items():
                    if content is None: path.unlink(missing_ok=True)
                    else: atomic_write(path,content.decode('utf-8'))
                raise
            return report
    finally:
        if fd is not None: os.close(fd)
        lock.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('entry',type=Path);p.add_argument('--html',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--replace',action='store_true');p.add_argument('--dry-run',action='store_true');p.add_argument('--move',action='store_true',help='explicit move, preserve evidence/added and register the old path in aliases');a=p.parse_args()
    try: report=publish(a.root,json.loads(a.entry.read_text(encoding='utf-8')),a.html,a.evidence,a.replace,a.dry_run,a.move)
    except (ValueError,OSError,KeyError,TypeError) as exc: p.exit(1,f'publish failed: {exc}\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
