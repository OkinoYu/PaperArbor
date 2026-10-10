"""Portable article redirects and local navigation rewrites for explicit moves."""
import html
import os
import re
from urllib.parse import unquote, urlsplit, urlunsplit


def relative_target(file, target):
    return os.path.relpath(target.resolve(), file.parent.resolve()).replace(os.sep, '/')


def redirect_html(file, target, title):
    href = html.escape(relative_target(file, target), quote=True)
    label = html.escape(title)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{label} · PaperArbor</title><meta http-equiv="refresh" content="0;url={href}"><style>body{{margin:3rem auto;padding:0 1.5rem;max-width:42rem;background:#fafaf6;color:#28352e;font-family:system-ui,sans-serif;line-height:1.9}}a{{color:#345e43}}a:focus-visible{{outline:3px solid #a3743c}}</style></head>
<body><h1>论文地址已更新</h1><p><a id="redirect-target" data-redirect="article" href="{href}">{label} →</a></p><p>若未自动跳转，请打开上面的文章链接。</p><script>(() => {{const target = new URL(document.getElementById('redirect-target').href);target.search = location.search;target.hash = location.hash;location.replace(target.href);}})();</script></body></html>'''


def rewrite_links(text, file, old_target, new_target):
    def replace(match):
        url = urlsplit(html.unescape(match[3]))
        if url.scheme or url.netloc or not url.path or (file.parent/unquote(url.path)).resolve() != old_target:
            return match[0]
        href = urlunsplit(('', '', relative_target(file, new_target), url.query, url.fragment))
        return match[1] + match[2] + html.escape(href, quote=True) + match[2]
    return re.sub(r'(<a\b[^>]*?\bhref\s*=\s*)(["\'])(.*?)(\2)', replace, text, flags=re.I | re.S)
