#!/usr/bin/env python3
"""Embed local img/SVG image/CSS references. Remote downloads are explicit source work."""
import argparse
import base64
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from common import atomic_write
from validate_site import data_image

ATTR=re.compile(r'(<(?:img|image)\b[^>]*?\b(?:src|href|xlink:href)\s*=\s*)([\"\'])(.*?)(\2)',re.I|re.S)
CSS=re.compile(r'url\(\s*([\"\']?)(.*?)\1\s*\)',re.I)

def embed(text, directory):
    def uri(value):
        if value.startswith('#'): return value
        if value.startswith('data:'):
            if not data_image(value):raise ValueError('invalid existing image data')
            return value
        parsed=urlsplit(value)
        if parsed.scheme or parsed.netloc:raise ValueError('download and inspect remote figures first')
        p=Path(unquote(parsed.path))
        if not p.is_absolute():p=directory/p
        raw=p.read_bytes()
        for mime in ('png','jpeg','webp','gif','svg+xml'):
            candidate=f'data:image/{mime};base64,'+base64.b64encode(raw).decode()
            if data_image(candidate):return candidate
        raise ValueError(f'unsupported or invalid image: {p}')
    text=ATTR.sub(lambda m:m[1]+m[2]+uri(m[3])+m[2],text)
    text=CSS.sub(lambda m:m[0] if m[2].startswith('#') else 'url('+uri(m[2])+')',text)
    if re.search(r'\bsrcset\s*=',text,re.I):raise ValueError('replace srcset with a single compressed image')
    return text

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('html',type=Path);p.add_argument('-o','--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.exit(1,'output exists; choose a staging path\n')
    text=embed(a.html.read_text(encoding='utf-8'),a.html.parent);atomic_write(a.output,text);print(a.output)
if __name__=='__main__':main()
