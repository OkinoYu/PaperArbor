"""Shared evidence contracts and safe, offline reader payloads."""
import json
from urllib.parse import urlsplit

KINDS = {'paper-fact', 'explanatory-derivation', 'editorial-analysis', 'figure'}
LABELS = {'paper-fact': '原文事实', 'explanatory-derivation': '说明式 / 推导',
          'editorial-analysis': '分析判断', 'figure': '图形证据'}


def validate_evidence(ledger, sources, anchors):
    if not isinstance(ledger, dict) or not isinstance(ledger.get('claims'), list) or not ledger['claims']:
        raise ValueError('nonempty evidence claims are required')
    if not isinstance(sources, list) or not sources:
        raise ValueError('reader needs primary sources')
    source_ids = set()
    for source in sources:
        if not isinstance(source, dict) or any(not isinstance(source.get(key), str) or not source[key].strip() for key in ('id', 'title', 'version', 'url')):
            raise ValueError('reader source needs id, title, version and URL')
        url = urlsplit(source['url'])
        if url.scheme != 'https' or not url.netloc:
            raise ValueError('reader sources must use absolute HTTPS URLs')
        if source['id'] in source_ids:
            raise ValueError('duplicate reader source id')
        source_ids.add(source['id'])
    for claim in ledger['claims']:
        if not isinstance(claim, dict):
            raise ValueError('claim must be an object')
        if claim.get('source') not in source_ids:
            raise ValueError('claim source is not in the entry')
        for key in ('locator', 'statement', 'anchor'):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise ValueError(f'claim needs {key}')
        if claim['anchor'] not in anchors:
            raise ValueError(f'missing claim anchor: {claim["anchor"]}')
        if 'kind' in claim and claim['kind'] not in KINDS:
            raise ValueError('unknown evidence kind')


def reader_payload(entry, ledger):
    for source in entry['sources']:
        if urlsplit(source['url']).scheme != 'https':
            raise ValueError('reader sources must use HTTPS')
    return {'sources': entry['sources'], 'ledger': ledger}


def json_script(value):
    # JSON script data still lives in an HTML raw-text context.
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
