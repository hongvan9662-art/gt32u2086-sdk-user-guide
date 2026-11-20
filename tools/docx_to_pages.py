"""GT32U2086 SDK User Guide: Word (.docx) -> Doxygen Markdown pages.

Usage:  python3 tools/docx_to_pages.py <GT32U2086_SDK_User_Guide.docx>
Writes README.md (home page), pages/partN.md, pages/NN_chapter_N.md, pages/_structure.json
and theme/gt32u2086_nav.js (data for the breadcrumb bar).

Rules: text is copied verbatim from Word; only markup is added.
 - one page per chapter (Heading 2), grouped under one page per PART (Heading 1)
 - Heading 3/4/5 -> sections; style "Code" -> code blocks; "List Bullet" -> bullets
 - tables: header row = first Word row; short-value columns (<= 12 characters) centred, others left
 - characters Doxygen would treat as markup are escaped (\\ @ < > % -- _ * # and "1." at line start);
   text inside double quotes is left as typed (Doxygen shows quoted text literally)
"""
import json, os, re, sys
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, 'pages')
CENTER_MAX = 12

os.makedirs(PAGES, exist_ok=True)
for f in os.listdir(PAGES):
    if f.endswith('.md') or f == '_structure.json':
        os.remove(os.path.join(PAGES, f))

d = docx.Document(SRC)

# Chip name used on the website. The Word file may still say FU2; every occurrence (text, tables,
# code, commands, folder names) is shown with the new name. Set RENAME = [] to keep the Word wording.
RENAME = [('FU2', 'GT32U2086'), ('fu2', 'gt32u2086')]
from docx.oxml.ns import qn
for _t in d.element.body.iter(qn('w:t')):
    if _t.text:
        for _a, _b in RENAME:
            _t.text = _t.text.replace(_a, _b)


# ------------------------------------------------------------------ escaping
def _esc_plain(t):
    t = t.replace('\\', '\\\\').replace('@', '\\@')
    t = re.sub(r'(?<![\w`])%', r'\\%', t)
    t = re.sub(r'(?<!\\)(---?)(?!-)', lambda m: '\\' + m.group(1), t)
    t = re.sub(r'(?<![\w\\])_|_(?![\w])', r'\\_', t)
    t = t.replace('*', '\\*').replace('#', '\\#')
    return t


def esc(t):
    """Escape a run of Word text for Doxygen Markdown (quoted spans kept literal)."""
    out = []
    for i, part in enumerate(re.split(r'("[^"]*")', t)):
        out.append(part if i % 2 else _esc_plain(part))
    s = ''.join(out)
    return s.replace('<', '&lt;').replace('>', '&gt;')


def para_text(p):
    parts = []
    for item in p.iter_inner_content():
        if hasattr(item, 'url') and item.url:
            parts.append(f'[{esc(item.text)}]({item.url})')
        else:
            parts.append(esc(item.text))
    s = ''.join(parts).strip()
    return re.sub(r'^(\d+)\. ', r'\1\\. ', s)


def slug(t):
    return re.sub(r'[^a-z0-9]+', '_', t.lower()).strip('_')[:60]


def guess_lang(lines):
    s = '\n'.join(lines)
    return 'c' if re.search(r'#include|;\s*$|\bvoid\b|\buint\d+_t\b|neon_\w+\(', s, re.M) else ''


def table_md(t):
    rows, raw = [], []
    for r in t.rows:
        cells, rc = [], []
        for c in r.cells:
            ps = [para_text(p) for p in c.paragraphs]
            cells.append('<br>'.join(x for x in ps if x).replace('|', '\\|'))
            rc.append(c.text.strip())
        rows.append(cells)
        raw.append(rc)
    if not rows:
        return ''
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    raw = [r + [''] * (n - len(r)) for r in raw]
    widest = [max((max((len(x) for x in r[c].split('\n')), default=0) for r in raw[1:]), default=0) for c in range(n)]
    sep = '|' + ''.join(':---:|' if w <= CENTER_MAX else ':---|' for w in widest)
    return '\n'.join(['| ' + ' | '.join(rows[0]) + ' |', sep] + ['| ' + ' | '.join(r) + ' |' for r in rows[1:]])


# ------------------------------------------------------------------ captions, notes, pictures
# Table / figure names: Word style "Caption", or a paragraph that starts "Table 1-2." / "Figure 3-1.".
# They are always shown centred ABOVE their table or picture (a name written below is moved up).
CAPTION_RE = re.compile(r'^(Table|Figure)\s+[A-Z]?\d+(?:[-.]\d+)*\.?\s', re.I)
# Notes: a paragraph that starts "NOTE:", "IMPORTANT:", "CAUTION:" or "WARNING:", a paragraph in a Word
# style whose name contains one of those words, or a one-column table whose first row is that word.
CALLOUT_WORDS = ('note', 'important', 'caution', 'warning')
CALLOUT_RE = re.compile(r'^(NOTE|IMPORTANT|CAUTION|WARNING)\s*[:：]\s*(.*)$', re.I | re.S)
IMG_DIR = os.path.join(ROOT, 'images')
for f in os.listdir(IMG_DIR):
    if f.startswith('word_'):
        os.remove(os.path.join(IMG_DIR, f))
img_count = [0]


def is_caption(b):
    return isinstance(b, Paragraph) and (b.style.name.lower() == 'caption' or bool(CAPTION_RE.match(b.text.strip())))


def pictures(p):
    return p._p.xpath('.//a:blip/@r:embed')


def is_object(b):
    return isinstance(b, Table) or (isinstance(b, Paragraph) and bool(pictures(b)))


def callout_of_paragraph(p):
    name = p.style.name.lower()
    for w in CALLOUT_WORDS:
        if w in name.split() or name == w:
            return w, [p]
    m = CALLOUT_RE.match(p.text.strip())
    if m:
        return m.group(1).lower(), None
    return None


def callout_of_table(t):
    if len(t.columns) != 1 or len(t.rows) < 2:
        return None
    head = t.rows[0].cells[0].text.strip().lower().rstrip(':')
    return head if head in CALLOUT_WORDS else None


def callout_md(kind, paragraphs_md):
    # one line of HTML: Doxygen splits a <div> that spans blank lines, so the whole box stays on one line
    body = ''.join(f'<div class="gt32u2086-callout-body">{t}</div>' for t in paragraphs_md if t)
    return ['', f'<div class="gt32u2086-callout gt32u2086-callout-{kind}"><div class="gt32u2086-callout-title">'
            f'{kind.upper()}</div>{body}</div>', '']


def save_pictures(p, chapter_label):
    out = []
    for rid in pictures(p):
        part = d.part.related_parts.get(rid)
        if part is None:
            continue
        ext = os.path.splitext(part.partname)[1] or '.png'
        img_count[0] += 1
        name = f'word_{chapter_label}_{img_count[0]}{ext}'
        open(os.path.join(IMG_DIR, name), 'wb').write(part.blob)
        out.append(f'![]({name})')
    return out


def put_captions_above(items):
    """Move a caption that sits right after its table/picture to just before it."""
    items = list(items)
    i = 0
    while i < len(items):
        if is_caption(items[i]):
            j = i - 1
            while j >= 0 and isinstance(items[j], Paragraph) and not items[j].text.strip() and not pictures(items[j]):
                j -= 1
            k = j - 1
            while k >= 0 and isinstance(items[k], Paragraph) and not items[k].text.strip() and not pictures(items[k]):
                k -= 1
            prev_has_caption = k >= 0 and is_caption(items[k])
            nxt = next((x for x in items[i + 1:] if not (isinstance(x, Paragraph) and not x.text.strip()
                                                           and not pictures(x))), None)
            if j >= 0 and is_object(items[j]) and not prev_has_caption and not (nxt is not None and is_object(nxt)):
                cap = items.pop(i)
                items.insert(j, cap)
        i += 1
    return items


# ------------------------------------------------------------------ walk the document
body = []
for el in d.element.body.iterchildren():
    tag = el.tag.split('}')[1]
    if tag == 'p':
        body.append(Paragraph(el, d))
    elif tag == 'tbl':
        body.append(Table(el, d))
start = next(i for i, b in enumerate(body) if isinstance(b, Paragraph) and b.style.name == 'Heading 1')
front, body = body[:start], put_captions_above(body[start:])

parts, chapters = [], []
cur, lines, code, seen = None, [], [], set()


def label_for(text, prefix):
    base = prefix + '_' + slug(text)
    lab, n = base, 2
    while lab in seen:
        lab, n = f'{base}_{n}', n + 1
    seen.add(lab)
    return lab


def flush_code():
    global code
    if code:
        while code and not code[-1].strip():
            code.pop()
        lines.extend(['', '```' + guess_lang(code)] + code + ['```', ''])
        code = []


def close_chapter():
    flush_code()
    if cur is not None:
        txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip() + '\n'
        open(os.path.join(PAGES, cur['file']), 'w').write(txt)


for b in body:
    if isinstance(b, Table):
        flush_code()
        kind = callout_of_table(b)
        if kind and cur is not None:
            lines += callout_md(kind, [para_text(p) for r in b.rows[1:] for c in r.cells for p in c.paragraphs])
        else:
            lines += ['', table_md(b), '']
        continue
    st, rawt = b.style.name, b.text
    if cur is not None and st != 'Code' and is_caption(b):
        flush_code()
        lines += ['', f'<div class="gt32u2086-caption">{para_text(b)}</div>', '']
        continue
    if cur is not None and pictures(b):
        flush_code()
        lines += [''] + save_pictures(b, cur['label']) + ['']
        if rawt.strip():
            lines += [para_text(b), '']
        continue
    co = callout_of_paragraph(b) if (cur is not None and st != 'Code') else None
    if co:
        flush_code()
        kind, whole = co
        if whole:
            lines += callout_md(kind, [para_text(b)])
        else:
            body_text = CALLOUT_RE.match(rawt.strip()).group(2)
            lines += callout_md(kind, [esc(body_text.strip())])
        continue
    if st == 'Code':
        code.append(rawt.rstrip())
        continue
    flush_code()
    if st == 'Heading 1':
        close_chapter()
        cur, lines = None, []
        parts.append({'title': rawt.strip(), 'label': f'part{len(parts) + 1}', 'chapters': []})
        continue
    if st == 'Heading 2':
        close_chapter()
        n = len(chapters) + 1
        lab = 'appendix_a' if rawt.lower().startswith('appendix a') else f'ch{n:02d}'
        seen.add(lab)
        cur = {'title': rawt.strip(), 'label': lab, 'file': f'{n:02d}_' + slug(rawt.split(':')[0]) + '.md',
               'sections': []}
        chapters.append(cur)
        parts[-1]['chapters'].append(cur)
        lines = [f'# {esc(rawt.strip())} {{#{lab}}}', '', '[TOC]', '']
        continue
    if cur is None:
        continue
    if st in ('Heading 3', 'Heading 4', 'Heading 5'):
        lvl = {'Heading 3': '##', 'Heading 4': '###', 'Heading 5': '####'}[st]
        lab = label_for(re.sub(r'^[A-Z]?\d+(\.\d+)*\s*', '', rawt.strip()), cur['label'])
        if st == 'Heading 3':
            cur['sections'].append({'title': rawt.strip(), 'label': lab})
        lines += ['', f'{lvl} {esc(rawt.strip())} {{#{lab}}}', '']
        continue
    t = para_text(b)
    if st == 'List Bullet':
        lines.append('- ' + t)
        continue
    if t:
        if lines and lines[-1].startswith('- '):
            lines.append('')
        lines += [t, '']
close_chapter()

# ------------------------------------------------------------------ PART pages (cards built by theme/gt32u2086.js)
for p in parts:
    md = [f'# {esc(p["title"])} {{#{p["label"]}}}', '', '<div class="gt32u2086-cards">', '']
    for c in p['chapters']:
        md.append(f'- @subpage {c["label"]}')
        md += [f'    - @ref {s["label"]}' for s in c['sections']]
    md += ['', '</div>', '']
    open(os.path.join(PAGES, p['label'] + '.md'), 'w').write('\n'.join(md))

# ------------------------------------------------------------------ home page
title = [p.text for p in front if isinstance(p, Paragraph) and p.style.name == 'Title']
subtitle = [p.text for p in front if isinstance(p, Paragraph) and p.style.name == 'Subtitle']
tagline = [p.text for p in front if isinstance(p, Paragraph) and p.style.name == 'Normal' and p.text.strip()]
contents = [p.text for p in front if isinstance(p, Paragraph) and p.style.name == 'Front Heading']
home = ['# GT32U2086 SDK User Guide', '']
home += [f'**{esc(s)}**' for s in subtitle] + ['']
home += [esc(s) + '\n' for s in tagline]
home += [f'<h2>{esc(contents[0]) if contents else "Contents"}</h2>', '', '<div class="gt32u2086-cards">', '']
for p in parts:
    home.append(f'- @subpage {p["label"]}')
    home += [f'    - @ref {c["label"]}' for c in p['chapters']]
home += ['', '</div>', '', '<h2>Downloads</h2>', '', '- <a href="GT32U2086_SDK_User_Guide.pdf">PDF manual</a>', '']
open(os.path.join(ROOT, 'README.md'), 'w').write('\n'.join(home))

# ------------------------------------------------------------------ structure (PDF) + breadcrumb data
json.dump({'title': title, 'subtitle': subtitle, 'tagline': tagline, 'parts': parts},
          open(os.path.join(PAGES, '_structure.json'), 'w'), indent=1, ensure_ascii=False)
crumbs = {'index.html': []}
for i, p in enumerate(parts, 1):
    crumbs[p['label'] + '.html'] = [[f'Part {i}', p['label'] + '.html']]
    for c in p['chapters']:
        short = c['title'].split(':')[0].strip()
        crumbs[c['label'] + '.html'] = [[f'Part {i}', p['label'] + '.html'], [short, c['label'] + '.html']]
open(os.path.join(ROOT, 'theme', 'gt32u2086_nav.js'), 'w').write(
    '/* generated by tools/docx_to_pages.py: breadcrumb trail for each page */\nwindow.GT32U2086_CRUMBS = '
    + json.dumps(crumbs, ensure_ascii=False) + ';\n')
print(len(parts), 'parts,', len(chapters), 'chapters,',
      sum(1 for b in body if isinstance(b, Table)), 'tables')
