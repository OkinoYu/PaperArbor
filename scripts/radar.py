#!/usr/bin/env python3
"""One-shot date-bounded arXiv discovery. Produces candidates, not fabricated reviews."""
import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from fetch_sources import http, parse_atom
from common import atomic_write

def discover(query, start, end, limit=60):
    if start>end: raise ValueError('start date must not follow end date')
    if not 1<=limit<=200: raise ValueError('limit must be 1..200')
    bounded=f'({query}) AND submittedDate:[{start:%Y%m%d}0000 TO {end:%Y%m%d}2359]'
    url='https://export.arxiv.org/api/query?'+urlencode({'search_query':bounded,'sortBy':'submittedDate','sortOrder':'descending','start':0,'max_results':limit})
    payload={'query':query,'start':str(start),'end':str(end),'timezone':'UTC (arXiv submittedDate)', 'retrieved_at':datetime.now(timezone.utc).isoformat(),'sources':[],'candidates':[]}
    try:
        items=parse_atom(http(url))
        unique={e['id'].split('v')[0]:e for e in items if start<=date.fromisoformat(e['published'])<=end}
        payload['candidates']=list(unique.values())
        payload['sources'].append({'name':'arXiv','url':url,'status':'ok','returned':len(items),'limit':limit,'possibly_truncated':len(items)>=limit})
    except Exception as exc:
        payload['sources'].append({'name':'arXiv','url':url,'status':'failed','error':str(exc)})
    return payload

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--query',required=True,help='arXiv syntax, e.g. cat:cs.CV AND all:multimodal');p.add_argument('--start',type=date.fromisoformat,required=True);p.add_argument('--end',type=date.fromisoformat,required=True);p.add_argument('--limit',type=int,default=60);p.add_argument('-o','--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.exit(1,'refusing to overwrite an existing report\n')
    payload=discover(a.query,a.start,a.end,a.limit);atomic_write(a.output,json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print(a.output)
    raise SystemExit(0 if payload['sources'][0]['status']=='ok' else 1)
if __name__=='__main__':main()
