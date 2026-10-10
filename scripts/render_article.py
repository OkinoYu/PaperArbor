#!/usr/bin/env python3
"""Wrap an agent-authored HTML body in a self-contained reading layout."""
import argparse
import html
from html.parser import HTMLParser
from pathlib import Path
from common import ROOT

class Headings(HTMLParser):
    def __init__(self, body):
        super().__init__(); self.entries=[]; self.current=None; self.feed(body)
    def handle_starttag(self, tag, attrs):
        if tag == 'h2': self.current=[dict(attrs).get('id'), '']
    def handle_data(self, data):
        if self.current: self.current[1] += data
    def handle_endtag(self, tag):
        if tag == 'h2' and self.current:
            if not self.current[0]: raise ValueError('every h2 needs a stable id')
            self.entries.append(self.current); self.current=None

def render(body, title, subtitle, category, mode, root=ROOT):
    e=html.escape
    entries=Headings(body).entries
    if not entries: raise ValueError('article needs h2 sections')
    toc=''.join(f'<a href="#{e(i,quote=True)}">{e(t)}</a>' for i,t in entries)
    css=(root/'assets/article.css').read_text(encoding='utf-8')
    js=(root/'assets/article.js').read_text(encoding='utf-8')
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{e(subtitle,quote=True)}"><title>{e(title)} · PaperArbor</title><style>{css}</style></head>
<body><a class="skip" href="#article">跳到正文</a><header class="reading-bar"><a href="../../index.html">↖ PaperArbor</a><span>{e(category)} / {e(mode)} / RESEARCH NOTE</span><button id="print" type="button">打印 / 保存 PDF</button></header><div id="progress" aria-hidden="true"></div>
<div class="reading-layout"><aside class="toc" aria-label="文章目录"><p>ON THIS PAGE</p>{toc}<a href="#top">回到顶部 ↑</a></aside><main id="article"><header id="top" class="article-head"><p class="eyebrow">PAPERARBOR / {e(mode.upper())}</p><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p><p class="meta">中文技术解读 · 原始论文核实 · 离线可读</p></header><details class="mobile-toc"><summary>目录 / 跳转到章节</summary><nav>{toc}</nav></details>{body}<footer class="article-footer"><a href="../../index.html">← 返回知识库</a><span>Where Papers Grow into Knowledge.</span></footer></main></div><script>{js}</script></body></html>'''

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('body',type=Path);p.add_argument('--title',required=True);p.add_argument('--subtitle',required=True);p.add_argument('--category',required=True);p.add_argument('--type',required=True,choices=['Single','Series','Digest','Radar']);p.add_argument('-o','--output',type=Path,required=True)
    a=p.parse_args(); result=render(a.body.read_text(encoding='utf-8'),a.title,a.subtitle,a.category,a.type)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f: f.write(result)
    print(a.output)
if __name__=='__main__': main()
