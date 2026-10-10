#!/usr/bin/env python3
"""Resolve arXiv identifiers/titles or preserve a local PDF; keep provenance."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from common import atomic_write

ATOM={'a':'http://www.w3.org/2005/Atom'}
ID_RE=re.compile(r'(?<!\d)(\d{4}\.\d{4,5}(?:v\d+)?)(?!\d)')

def http(url, timeout=45, limit=80*1024*1024):
    request=Request(url,headers={'User-Agent':'PaperArbor/0.1 (research reading; public sources)'})
    with urlopen(request,timeout=timeout) as response:
        data=response.read(limit+1)
    if len(data)>limit: raise ValueError(f'response exceeds {limit} bytes')
    return data

def parse_atom(data):
    feed=ET.fromstring(data); result=[]
    for entry in feed.findall('a:entry',ATOM):
        def text(name): return ' '.join((entry.findtext('a:'+name,default='',namespaces=ATOM)).split())
        url=text('id'); match=ID_RE.search(url)
        if not match:
            if 'error' in url.lower() or text('title').lower() == 'error':
                raise ValueError('arXiv API error: '+text('summary'))
            continue
        result.append({'id':match.group(1),'title':text('title'),'authors':', '.join(a.findtext('a:name',default='',namespaces=ATOM) for a in entry.findall('a:author',ATOM)),
                       'published':text('published')[:10],'updated':text('updated')[:10], 'abstract':text('summary'),
                       'url':'https://arxiv.org/abs/'+match.group(1),'pdf_url':'https://arxiv.org/pdf/'+match.group(1),'version':'v'+match.group(1).split('v')[-1] if 'v' in match.group(1) else 'unresolved'})
    return result

class ArxivMeta(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.values = {}; self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name', '').startswith('citation_'):
            self.values.setdefault(a['name'], []).append(a.get('content', ''))


def parse_abs(data, requested):
    text = data.decode('utf-8'); meta = ArxivMeta(text).values
    base = requested.split('v')[0]
    if meta.get('citation_arxiv_id', [''])[0] != base:
        raise ValueError('arXiv fallback identity mismatch')
    selected = re.search(r'<strong>\[v(\d+)\]</strong>', text)
    if not selected:
        raise ValueError('cannot verify fallback version; inspect source in browser')
    identifier = base + 'v' + selected[1]
    if 'v' in requested and identifier != requested:
        raise ValueError('arXiv fallback version mismatch')
    def get(key):
        values = meta.get('citation_' + key)
        if not values: raise ValueError(f'arXiv fallback missing {key}')
        return values[0]
    return {'id': identifier, 'title': get('title'), 'authors': ', '.join(meta.get('citation_author', [])),
            'published': get('date').replace('/', '-'), 'updated': get('online_date').replace('/', '-'),
            'abstract': get('abstract'), 'url': 'https://arxiv.org/abs/' + identifier,
            'pdf_url': 'https://arxiv.org/pdf/' + identifier, 'version': 'v' + selected[1]}

def lookup(query, limit=5):
    match=ID_RE.fullmatch(query) or (ID_RE.search(query) if urlsplit(query).hostname in ('arxiv.org','www.arxiv.org','export.arxiv.org') else None)
    params={'id_list':match.group(1)} if match else {'search_query':'ti:"'+query.replace('"','')+'"','max_results':limit}
    try:
        entries=parse_atom(http('https://export.arxiv.org/api/query?'+urlencode(params)))
    except Exception as exc:
        if not match:
            raise ValueError(f'title search unavailable: {exc}; resolve a verified ID in browser') from exc
        record=parse_abs(http('https://arxiv.org/abs/'+match.group(1)),match.group(1))
        record['retrieval_note']=f'arXiv API unavailable ({exc}); resolved from primary abs metadata'
        return record
    if match and entries and entries[0]['id'].split('v')[0] != match.group(1).split('v')[0]:
        raise ValueError('arXiv API identity mismatch')
    if match and 'v' in match.group(1) and entries and entries[0]['id'] != match.group(1):
        raise ValueError('arXiv API version mismatch')
    if not entries: raise ValueError('no arXiv match; use browsing to verify a primary source')
    if not match and len(entries)!=1:
        raise ValueError('ambiguous title; select a verified arXiv ID: '+json.dumps([{'id':e['id'],'title':e['title']} for e in entries],ensure_ascii=False))
    return entries[0]

def fetch(query: str, out: Path, metadata_only=False):
    source=Path(query).expanduser()
    out.mkdir(parents=True,exist_ok=True)
    if source.is_file():
        content=source.read_bytes()
        if not content.startswith(b'%PDF-'): raise ValueError('local input is not a PDF')
        record={'id':'local-'+hashlib.sha256(content).hexdigest()[:16], 'title':source.stem,'status':'local-unverified',
                'original_filename':source.name,'note':'Read title page and verify author/date/primary URL before publication.'}
        stem=record['id']
    else:
        record=lookup(query); record['status']='resolved'; stem=record['id']
        content=None if metadata_only else http(record['pdf_url'])
        if content is not None and not content.startswith(b'%PDF-'): raise ValueError('arXiv returned non-PDF content')
    targets=[out/(stem+'.json')]+([out/(stem+'.pdf')] if content is not None else [])
    if any(p.exists() for p in targets): raise FileExistsError('source cache already exists; use another output directory')
    record['retrieved_at']=datetime.now(timezone.utc).isoformat()
    if content is not None:
        record['sha256']=hashlib.sha256(content).hexdigest(); record['pdf_file']=stem+'.pdf'
        with targets[-1].open('xb') as f: f.write(content)
    atomic_write(targets[0],json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('-o','--output',type=Path,required=True);p.add_argument('--metadata-only',action='store_true');a=p.parse_args()
    try: result=fetch(a.source,a.output,a.metadata_only)
    except Exception as exc: p.exit(1,f'fetch failed: {exc}\nUse browser/primary PDF fallback; do not invent unavailable content.\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
