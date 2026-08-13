#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère la version prête à publier du Tome 1 (HTML + PDF)."""
import re
from html import escape
from weasyprint import HTML

SRC = 'roman_tome1_extracted.txt'
HTML_OUT = 'La_vie_belle_Tome1.html'
PDF_OUT = 'La_vie_belle_Tome1.pdf'

BOOK_TITLE = 'La vie belle'
BOOK_SUBTITLE = 'Tome 1 — Les Racines de l’espoir'
AUTHOR = 'Mouadh P. Chibani'
TAGLINE = 'Un roman sur la lumière, même quand la vie semble l’avoir éteinte.'
RUNNING_HEAD = f'{BOOK_TITLE} — {BOOK_SUBTITLE}'

lines = open(SRC, encoding='utf-8').read().split('\n')

# ---------- parsing ----------
chapters = []          # list of (num, title, blocks)
blocks = []            # list of ('p', text) | ('sep', '') | ('head', label)
current = None

chap_re = re.compile(r'^CHAPITRE (\d+)$')

def flush():
    global blocks, current
    if current is not None and blocks:
        current['blocks'] = blocks
    blocks = []

def new_chap(num):
    global current, blocks
    flush()
    current = {'num': num, 'title': None, 'blocks': []}
    chapters.append(current)
    blocks = current['blocks']

i = 0
n = len(lines)
started = False
while i < n:
    line = lines[i].rstrip('\n')
    if not started:
        if line == 'LA VIE BELLE':
            started = True
        i += 1
        continue
    if not line.strip():
        i += 1
        continue
    m = chap_re.match(line)
    if m:
        num = int(m.group(1))
        new_chap(num)
        # subtitle on next line
        if i + 1 < n and lines[i + 1].strip() and not chap_re.match(lines[i + 1]):
            current['title'] = lines[i + 1].strip()
            i += 2
            continue
        i += 1
        continue
    if line == 'ÉPILOGUE':
        flush()
        current = {'num': None, 'title': None, 'blocks': []}
        chapters.append(current)
        blocks = current['blocks']
        i += 1
        continue
    if line == '✦':
        blocks.append(('sep', ''))
    else:
        blocks.append(('p', line))
    i += 1
flush()

# ---------- HTML ----------
def chap_block_html(c):
    out = []
    if c['num'] is not None:
        out.append(f'<h1 class="chap-num" id="chapitre-{c["num"]}">CHAPITRE {c["num"]}</h1>')
        if c['title']:
            out.append(f'<h2 class="chap-title">{escape(c["title"])}</h2>')
    else:
        out.append('<h1 class="chap-num" id="epilogue">ÉPILOGUE</h1>')
    for kind, text in c['blocks']:
        if kind == 'sep':
            out.append('<div class="separator">✦</div>')
        else:
            out.append(f'<p>{escape(text)}</p>')
    return '\n'.join(out)

toc_items = []
for c in chapters:
    if c['num'] is not None:
        anchor = f'chapitre-{c["num"]}'
        label = f'{c["num"]}. {c["title"]}' if c['title'] else str(c['num'])
    else:
        anchor = 'epilogue'
        label = 'Épilogue'
    toc_items.append(f'<li><a href="#{anchor}">{escape(label)}</a></li>')

chapters_html = '\n'.join(chap_block_html(c) for c in chapters)

# ---------- CSS ----------
TYPO_CSS = """
  :root {{ --ink: #222; --accent: #8a4b2a; --paper: #fffdf8; }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-font-smoothing: antialiased; }}
  body {{
    font-family: "DejaVu Serif", "Liberation Serif", Georgia, "Times New Roman", serif;
    color: var(--ink);
    background: var(--paper);
    margin: 0 auto;
    max-width: 46rem;
    padding: 2rem 1.5rem;
    line-height: 1.7;
    font-size: 1.05rem;
    text-align: justify;
    hyphens: auto;
  }}
  a {{ color: inherit; text-decoration: none; }}
"""

COVER_CSS = """
  .cover {{
    text-align: center;
    min-height: 88vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-bottom: 1px solid #ddd;
    margin-bottom: 2.5rem;
  }}
  .cover .rule {{ border-top: 1px solid var(--accent); width: 6rem; margin: 1.5rem auto; }}
  .cover h1 {{ font-size: 3rem; margin: 0; letter-spacing: .04em; }}
  .cover .subtitle {{ font-size: 1.3rem; color: #555; font-style: italic; margin-top: .5rem; }}
  .cover .author {{ margin-top: 2.5rem; font-size: 1.05rem; letter-spacing: .2em; text-transform: uppercase; }}
  .cover-page {{ break-after: page; }}
"""

FRONT_CSS = """
  .imprint {{ font-size: .85rem; color: #666; text-align: center; margin: 2.5rem 0; line-height: 1.8; }}
  .imprint-page {{ break-after: page; }}
  .toc {{ margin: 2rem 0 3rem; }}
  .toc h2 {{ font-size: 1.4rem; text-align: center; border-bottom: 1px solid #ccc; padding-bottom: .5rem; }}
  .toc ol {{ list-style: none; padding: 0; }}
  .toc li {{ padding: .35rem 0; border-bottom: 1px dotted #ccc; text-align: right; }}
  .toc li a {{ text-align: left; display: block; }}
  .toc li a::after {{ content: " →"; color: var(--accent); }}
"""

CHAP_CSS = """
  h1.chap-num {{
    font-size: 1.15rem;
    letter-spacing: .35em;
    text-align: center;
    margin: 3.5rem 0 .4rem;
    color: var(--accent);
  }}
  h2.chap-title {{ font-size: 1.5rem; text-align: center; margin: 0 0 1.8rem; font-weight: normal; }}
  .separator {{ text-align: center; color: var(--accent); margin: 1.6rem 0; letter-spacing: .2em; }}
  p {{ margin: 0 0 .7rem; }}
"""

FRONT_PAGE_CSS = """
  @page {{ size: A4; margin: 22mm 20mm 20mm; }}
  @page cover {{ margin: 0; }}
"""

BODY_PAGE_CSS = f"""
  @page {{
    size: A4;
    margin: 22mm 20mm 20mm;
    @bottom-center {{ content: counter(page); font-size: 9pt; color: #888; font-family: "DejaVu Serif", serif; }}
    @top-center {{ content: "{escape(RUNNING_HEAD)}"; font-size: 8pt; color: #aaa; font-style: italic; }}
  }}
"""

SCREEN_PAGE_CSS = f"""
  @page {{
    size: A4;
    margin: 22mm 20mm 20mm;
    @bottom-center {{ content: counter(page); font-size: 9pt; color: #888; font-family: "DejaVu Serif", serif; }}
    @top-center {{ content: "{escape(RUNNING_HEAD)}"; font-size: 8pt; color: #aaa; font-style: italic; }}
  }}
  @page cover {{ @top-center {{ content: none; }} @bottom-center {{ content: none; }} margin: 0; }}
  .cover {{ page: cover; }}
"""

# ---------- assemblage HTML (écran / web) ----------
screen_css = TYPO_CSS + COVER_CSS + FRONT_CSS + CHAP_CSS + SCREEN_PAGE_CSS

front_sections = f"""
  <section class="cover cover-page">
    <p class="author">{escape(AUTHOR)}</p>
    <div class="rule"></div>
    <h1>{BOOK_TITLE}</h1>
    <p class="subtitle">{escape(BOOK_SUBTITLE)}</p>
    <div class="rule"></div>
    <p style="margin-top:2.5rem;font-style:italic;color:#777;">{escape(TAGLINE)}</p>
  </section>

  <section class="imprint imprint-page">
    <p><strong>{BOOK_TITLE}</strong> — {escape(BOOK_SUBTITLE)}</p>
    <p>Texte corrigé et harmonisé. Version prête à publier.</p>
    <p>© 2026 {escape(AUTHOR)}. Tous droits réservés.</p>
    <p>Ceci est une œuvre de fiction. Toute ressemblance avec des personnes réelles ou des situations existantes serait purement fortuite.</p>
  </section>

  <section class="toc toc-page">
    <h2>Sommaire</h2>
    <ol>
      {chr(10).join(toc_items)}
    </ol>
  </section>
"""

html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{BOOK_TITLE} — {escape(BOOK_SUBTITLE)}</title>
<meta name="author" content="{escape(AUTHOR)}">
<meta name="description" content="{escape(BOOK_TITLE)} — {escape(BOOK_SUBTITLE)}. Roman, version prête à publier.">
<style>
{screen_css}
</style>
</head>
<body>

  {front_sections}

  <div class="chapter">
    {chapters_html}
  </div>

</body>
</html>
"""

open(HTML_OUT, 'w', encoding='utf-8').write(html)
print('OK HTML:', HTML_OUT, f'({len(html)} octets)')

# ---------- PDF : liminaires + corps, fusionnés, corps numéroté à partir de 1 ----------
def page_doc(body_css, body):
    css = TYPO_CSS + CHAP_CSS + body_css
    return HTML(string=f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><style>
{css}
</style></head>
<body>
{body}
</body></html>""").render()

front_doc = page_doc(COVER_CSS + FRONT_CSS + FRONT_PAGE_CSS, front_sections)
body_doc = page_doc(BODY_PAGE_CSS, f'<div class="chapter">\n{chapters_html}\n</div>')

merged = front_doc.copy(front_doc.pages + body_doc.pages)
merged.write_pdf(PDF_OUT)
print('OK PDF:', PDF_OUT, f'({len(front_doc.pages)}+{len(body_doc.pages)} pages)')
