"""Shared manifest contracts and durable writes (Python standard library only)."""
from __future__ import annotations
import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ('LLM', 'VLM', 'Multimodal', 'Reasoning', 'Agent', 'RL', 'Others')
MODES = ('Single', 'Series', 'Digest', 'Radar')

def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def site_path(root: Path, value: str) -> Path:
    p = PurePosixPath(value)
    if not value or p.is_absolute() or '..' in p.parts or '\\' in value or urlsplit(value).scheme or '?' in value or '#' in value:
        raise ValueError(f'unsafe site path: {value}')
    target = (root / value).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'path escapes site: {value}')
    return target

def validate_records(records: list, root: Path, require_files: bool = True) -> None:
    if not isinstance(records, list):
        raise ValueError('manifest must be a JSON array')
    ids, paths, signatures = set(), set(), set()
    for r in records:
        for key in ('id', 'title', 'summary', 'category', 'type', 'published', 'added', 'path', 'tags', 'sources'):
            if key not in r:
                raise ValueError(f'missing {key}')
        for key in ('id', 'title', 'summary', 'category', 'type', 'published', 'added', 'path'):
            if not isinstance(r[key], str) or not r[key].strip():
                raise ValueError(f'invalid {key}')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', r['id']):
            raise ValueError('id must be a safe slug')
        if r['category'] not in CATEGORIES or r['type'] not in MODES:
            raise ValueError('unknown category or type')
        for field in ('published', 'added'):
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', r[field]):
                raise ValueError(f'{field} must be YYYY-MM-DD')
            date.fromisoformat(r[field])
        if not isinstance(r['tags'], list) or not r['tags'] or any(not isinstance(t, str) or not t.strip() for t in r['tags']):
            raise ValueError('tags must be a nonempty string array')
        if not isinstance(r['sources'], list) or not r['sources']:
            raise ValueError('at least one primary source is required')
        keys = []
        for source in r['sources']:
            for field in ('id', 'title', 'authors', 'url', 'version', 'published'):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    raise ValueError(f'source missing {field}')
            if urlsplit(source['url']).scheme != 'https':
                raise ValueError('primary sources must use HTTPS')
            date.fromisoformat(source['published'])
            keys.append(re.sub(r'v\d+$', '', source['id']).casefold())
        if len(set(keys)) != len(keys):
            raise ValueError('duplicate sources within one record')
        signature = (r['type'], tuple(sorted(keys)))
        if r['id'].casefold() in ids or r['path'].casefold() in paths or signature in signatures:
            raise ValueError('duplicate record id, path, or same-mode source set')
        ids.add(r['id'].casefold()); paths.add(r['path'].casefold()); signatures.add(signature)
        target = site_path(root, r['path'])
        expected = f"examples/{r['category']}/"
        if not r['path'].startswith(expected) or target.suffix != '.html':
            raise ValueError(f'expected {expected}*.html')
        if require_files and not target.is_file():
            raise ValueError(f'missing article: {r["path"]}')

def load_records(root: Path = ROOT) -> list:
    records = json.loads((root / 'data/papers.json').read_text(encoding='utf-8'))
    validate_records(records, root)
    return records
