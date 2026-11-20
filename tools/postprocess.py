"""Replace Doxygen's <object> SVG embeds with <img> so diagrams display everywhere (incl. sandboxed hosts)."""
import glob, re, sys
root = sys.argv[1] if len(sys.argv) > 1 else 'build/html'
for f in glob.glob(root + '/*.html'):
    s = open(f, encoding='utf-8').read()
    def rep(m):
        cap = re.search(r'<div class="caption">\s*(.*?)</div>', s[m.end():m.end() + 400], re.S)
        alt = re.sub(r'<[^>]+>', '', cap.group(1)).strip() if cap else ''
        return f'<img src="{m.group(1)}" alt="{alt}"/>'
    n = re.sub(r'<object type="image/svg\+xml" data="([^"]+)"[^>]*></object>', rep, s)
    if n != s:
        open(f, 'w', encoding='utf-8').write(n)

# strip DTD declarations from Doxygen's icon SVGs (not needed for display)
for f in glob.glob(root + '/**/*.svg', recursive=True):
    s = open(f, encoding='utf-8').read()
    n = re.sub(r'<!DOCTYPE[^>\[]*(\[[^\]]*\])?\s*>', '', s)
    if n != s:
        open(f, 'w', encoding='utf-8').write(n)

# write the U+FFFD literal in Doxygen's bundled jquery.js as an escape (same meaning in JS)
for f in glob.glob(root + '/*.js'):
    s = open(f, encoding='utf-8').read()
    if '�' in s:
        open(f, 'w', encoding='utf-8').write(s.replace('�', '\\uFFFD'))

# embed logos and diagrams directly in the pages (data URIs) so they show on any host, even ones that block separate image files
import base64, os
def data_uri(path):
    mime = 'image/png' if path.lower().endswith('.png') else 'image/svg+xml'
    return 'data:' + mime + ';base64,' + base64.b64encode(open(path, 'rb').read()).decode()
cache = {}
for f in glob.glob(root + '/*.html'):
    s = open(f, encoding='utf-8').read()
    def rep(m):
        name = m.group(2)
        p = os.path.join(root, name)
        if not os.path.exists(p):
            return m.group(0)
        if name not in cache:
            cache[name] = data_uri(p)
        return m.group(1) + cache[name] + '"'
    n = re.sub(r'(<img[^>]*?\ssrc=")(logo_gtinx(?:_white)?\.png|[a-z0-9_]+\.drawio\.svg)"', rep, s)
    if n != s:
        open(f, 'w', encoding='utf-8').write(n)

# left menu: chevron arrows (same shape as the contents cards) and tree label "User Guide v1.0"
CHEV = ('<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M4 2l4 4-4 4" fill="none" stroke="currentColor" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
CHEV_DOWN = CHEV.replace('<path', '<path transform="rotate(90 6 6)"')
p = os.path.join(root, 'navtree.js')
if os.path.exists(p):
    s = open(p, encoding='utf-8').read()
    s = s.replace("var arrowDown = '&#9660;';", "var arrowDown = '" + CHEV_DOWN + "';")
    s = s.replace("var arrowRight = '&#9658;';", "var arrowRight = '" + CHEV + "';")
    open(p, 'w', encoding='utf-8').write(s)
p = os.path.join(root, 'navtreedata.js')
if os.path.exists(p):
    s = open(p, encoding='utf-8').read()
    s = s.replace('[ "GT32U2086 SDK User Guide", "index.html"', '[ "User Guide v1.0", "index.html"')
    open(p, 'w', encoding='utf-8').write(s)
