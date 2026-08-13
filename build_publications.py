#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère la version prête à publier du Tome 1 (HTML + PDF).
Design inspiré du roman : aube, lumière, espoir, racines.
"""
import re
from html import escape
from urllib.parse import quote
from weasyprint import HTML

SRC = 'roman_tome1_extracted.txt'
HTML_OUT = 'La_vie_belle_Tome1.html'
PDF_OUT = 'La_vie_belle_Tome1.pdf'

BOOK_TITLE = 'La vie belle'
BOOK_SUBTITLE = 'Tome 1 — Les Racines de l’espoir'
AUTHOR = 'Mouadh P. Chibani'
TAGLINE = 'Un roman sur la lumière, même quand la vie semble l’avoir éteinte.'
RUNNING_HEAD = f'{BOOK_TITLE} — {BOOK_SUBTITLE}'

# ---------- illustration de couverture (soleil levant, arbre aux racines) ----------
COVER_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 850" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Soleil levant sur un arbre aux racines profondes">
<defs>
<linearGradient id="ciel" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#3a2012"/>
<stop offset="0.30" stop-color="#7c4124"/>
<stop offset="0.52" stop-color="#cf7c33"/>
<stop offset="0.72" stop-color="#efb25f"/>
<stop offset="0.88" stop-color="#fdeec0"/>
<stop offset="1" stop-color="#fff6dc"/>
</linearGradient>
<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
<stop offset="0%" stop-color="#fff4c8" stop-opacity="0.95"/>
<stop offset="0.45" stop-color="#ffdf8a" stop-opacity="0.55"/>
<stop offset="1" stop-color="#ffd97a" stop-opacity="0"/>
</radialGradient>
<linearGradient id="sol" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#5d3a20"/>
<stop offset="0.12" stop-color="#4a2d17"/>
<stop offset="1" stop-color="#241103"/>
</linearGradient>
<radialGradient id="scrim" cx="0.5" cy="0.40" r="0.58">
<stop offset="0%" stop-color="#160a03" stop-opacity="0.42"/>
<stop offset="1" stop-color="#160a03" stop-opacity="0"/>
</radialGradient>
</defs>

<rect width="600" height="850" fill="url(#ciel)"/>

<circle cx="300" cy="340" r="185" fill="url(#halo)"/>
<circle cx="300" cy="340" r="100" fill="#ffe9a4"/>

<g stroke="#ffdf8a" stroke-width="5" opacity="0.6" stroke-linecap="round">
<line x1="300" y1="120" x2="300" y2="70"/>
<line x1="420" y1="178" x2="458" y2="142"/>
<line x1="462" y1="340" x2="520" y2="340"/>
<line x1="420" y1="502" x2="458" y2="538"/>
<line x1="180" y1="178" x2="142" y2="142"/>
<line x1="138" y1="340" x2="80" y2="340"/>
<line x1="180" y1="502" x2="142" y2="538"/>
<line x1="300" y1="560" x2="300" y2="610"/>
</g>

<g stroke="#3a2012" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.6">
<path d="M150 230 q10 -9 20 0 M168 222 q10 -9 20 0"/>
<path d="M440 260 q10 -9 20 0 M458 252 q10 -9 20 0"/>
</g>

<g stroke="#ffe9a4" stroke-width="3" stroke-linecap="round" opacity="0.9">
<path d="M110 140 v10 M105 145 h10"/>
<path d="M500 110 v10 M495 115 h10"/>
<path d="M540 300 v10 M535 305 h10"/>
<path d="M70 330 v10 M65 335 h10"/>
<path d="M120 470 v10 M115 475 h10"/>
<path d="M500 470 v10 M495 475 h10"/>
</g>

<path d="M0 640 Q150 565 320 620 T600 610 L600 850 L0 850 Z" fill="#6b3f20" opacity="0.55"/>

<path d="M0 668 L600 668 L600 850 L0 850 Z" fill="url(#sol)"/>

<g fill="#241205">
<circle cx="300" cy="370" r="100"/>
<circle cx="244" cy="425" r="66"/>
<circle cx="356" cy="425" r="66"/>
<circle cx="278" cy="335" r="62"/>
<circle cx="324" cy="335" r="62"/>
</g>

<path d="M288 470 C286 520 284 560 281 612 C278 646 278 664 280 678 L320 678 C322 664 322 646 319 612 C316 560 314 520 312 470 Z" fill="#241205"/>

<g fill="none" stroke="#241205" stroke-linecap="round">
<path d="M282 676 C266 706 240 742 210 776" stroke-width="8"/>
<path d="M286 668 C266 696 248 716 220 736" stroke-width="5.5"/>
<path d="M282 678 C258 702 240 718 222 730" stroke-width="3.5"/>
<path d="M318 676 C334 706 360 742 390 776" stroke-width="8"/>
<path d="M314 668 C334 696 352 716 380 736" stroke-width="5.5"/>
<path d="M318 678 C342 702 360 718 378 730" stroke-width="3.5"/>
<path d="M290 678 C286 718 290 754 296 786" stroke-width="4"/>
<path d="M310 678 C314 718 310 754 304 786" stroke-width="4"/>
</g>

<g fill="none" stroke="#a8c47c" stroke-width="4" stroke-linecap="round">
<path d="M96 700 C92 676 90 658 92 640"/>
</g>
<g fill="#a8c47c">
<ellipse cx="94" cy="638" rx="9" ry="5" transform="rotate(-35 94 638)"/>
<ellipse cx="104" cy="650" rx="9" ry="5" transform="rotate(25 104 650)"/>
</g>

<rect width="600" height="850" fill="url(#scrim)"/>
</svg>'''

COVER_DATA = 'data:image/svg+xml;charset=utf-8,' + quote(COVER_SVG)

# ---------- parsing ----------
lines = open(SRC, encoding='utf-8').read().split('\n')
chapters = []          # list of dict(num, title, blocks)
blocks = []
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

# ---------- HTML des chapitres ----------
def chap_block_html(c):
    out = []
    if c['num'] is not None:
        out.append(f'<h1 class="chap-num" id="chapitre-{c["num"]}">CHAPITRE {c["num"]}</h1>')
        if c['title']:
            out.append(f'<h2 class="chap-title">{escape(c["title"])}</h2>')
    else:
        out.append('<h1 class="chap-num" id="epilogue">ÉPILOGUE</h1>')
    first_p = True
    for kind, text in c['blocks']:
        if kind == 'sep':
            out.append('<div class="separator">☀</div>')
        else:
            if first_p and text[:1].isalpha():
                out.append(f'<p class="first"><span class="dropcap">{escape(text[:1])}</span>{escape(text[1:])}</p>')
            else:
                out.append(f'<p{"" if first_p else ""}>{escape(text)}</p>')
            first_p = False
    return '\n'.join(out)

toc_items = []
for c in chapters:
    if c['num'] is not None:
        anchor = f'chapitre-{c["num"]}'
        num = c['num']
        title = c['title'] or ''
    else:
        anchor = 'epilogue'
        num = ''
        title = 'Épilogue'
    toc_items.append(
        f'<li><a href="#{anchor}"><span class="toc-num">{num}</span>{escape(title)}</a></li>'
    )

chapters_html = '\n'.join(chap_block_html(c) for c in chapters)

# ---------- CSS ----------
TYPO_CSS = """
  :root {
    --ink: #2b2118;
    --accent: #a35b24;
    --gold: #b8862e;
    --gold-soft: #d9b96a;
    --green: #6f8a52;
    --paper: #fdf7ea;
    --line: #e3d3b0;
    --font-body: "EB Garamond", "DejaVu Serif", Georgia, "Times New Roman", serif;
    --font-display: "Vollkorn", "EB Garamond", "DejaVu Serif", Georgia, serif;
  }
  * { box-sizing: border-box; }
  html { -webkit-font-smoothing: antialiased; }
  body {
    font-family: var(--font-body);
    color: var(--ink);
    background: var(--paper);
    margin: 0 auto;
    max-width: 46rem;
    padding: 2rem 1.5rem;
    line-height: 1.7;
    font-size: 1.06rem;
    text-align: justify;
    hyphens: auto;
  }
  a { color: inherit; text-decoration: none; }
"""

COVER_CSS = """
  .cover {
    position: relative;
    page: cover;
    break-after: page;
    overflow: hidden;
  }
  .cover-art {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .cover-text { position: absolute; left: 0; right: 0; top: 12%; text-align: center; }
  .cover-author {
    margin: 0;
    text-transform: uppercase;
    letter-spacing: .38em;
    font-size: .82rem;
    color: #f3d9a4;
    font-family: var(--font-display);
  }
  .cover-title {
    margin: 1.1rem 0 0;
    font-size: 3.4rem;
    font-weight: 600;
    color: #fff4dc;
    font-family: var(--font-display);
    letter-spacing: .03em;
    text-shadow: 0 2px 24px rgba(26, 13, 5, .55);
  }
  .cover-subtitle {
    margin: .4rem 0 0;
    font-style: italic;
    font-size: 1.25rem;
    color: #ffdd94;
    font-family: var(--font-display);
    letter-spacing: .06em;
  }
  .cover-tagline {
    position: absolute;
    left: 0; right: 0; top: 58%;
    text-align: center;
    margin: 0;
    font-style: italic;
    font-size: 1.02rem;
    color: #fff0c9;
    padding: 0 3rem;
    text-shadow: 0 1px 14px rgba(26, 13, 5, .6);
  }
  .cover-tagline::before, .cover-tagline::after {
    content: "";
    display: inline-block;
    vertical-align: middle;
    width: 2.6rem;
    height: 1px;
    background: rgba(255, 240, 201, .7);
    margin: 0 .9rem;
  }
  @media print {
    .cover { width: 210mm; height: 297mm; }
  }
  @media screen {
    .cover { min-height: 100vh; }
  }
"""

FRONT_CSS = """
  .imprint {
    text-align: center;
    color: #5c4a36;
    font-size: .92rem;
    line-height: 2;
    margin: 0;
    padding: 2.2rem 1rem;
  }
  .imprint .ornament { color: var(--gold); font-size: 1.1rem; margin-bottom: 1.6rem; }
  .imprint-page { break-after: page; }
  .imprint-title { font-family: var(--font-display); font-size: 1.15rem; color: var(--ink); }
  .imprint-rule { width: 4.5rem; height: 2px; background: linear-gradient(90deg, transparent, var(--gold), transparent); margin: 1.1rem auto; }

  .toc { margin: 0; padding: 1.5rem 1rem 3rem; }
  .toc h2 {
    font-family: var(--font-display);
    font-size: 1.35rem;
    font-weight: 600;
    text-align: center;
    letter-spacing: .24em;
    text-transform: uppercase;
    color: var(--accent);
    margin: 0 0 .4rem;
  }
  .toc h2::after {
    content: "";
    display: block;
    width: 5rem;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    margin: .9rem auto 1.6rem;
  }
  .toc ol { list-style: none; padding: 0; margin: 0; }
  .toc li { border-bottom: 1px dotted var(--line); }
  .toc li a { display: block; text-align: left; padding: .34rem .2rem; color: var(--ink); }
  .toc li a:hover { color: var(--accent); }
  .toc-num {
    display: inline-block;
    min-width: 2.2rem;
    color: var(--gold);
    font-family: var(--font-display);
    font-weight: 600;
  }
"""

CHAP_CSS = """
  .chapter { padding: 0; }
  h1.chap-num {
    font-family: var(--font-display);
    font-size: 1.02rem;
    font-weight: 600;
    letter-spacing: .4em;
    text-align: center;
    margin: 3.4rem 0 .35rem;
    color: var(--accent);
    break-before: page;
  }
  .chapter h1.chap-num:first-child { break-before: auto; }
  h1.chap-num::before {
    content: "☀";
    display: block;
    font-size: .9rem;
    color: var(--gold);
    letter-spacing: 0;
    margin-bottom: 1rem;
    font-family: var(--font-body);
  }
  h2.chap-title {
    font-family: var(--font-display);
    font-size: 1.55rem;
    font-weight: 500;
    text-align: center;
    margin: 0 0 1rem;
    color: var(--ink);
  }
  h2.chap-title::after {
    content: "";
    display: block;
    width: 5rem;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    margin: .85rem auto 2rem;
  }
  .separator {
    text-align: center;
    margin: 2.2rem 0;
    color: var(--gold);
    font-size: .85rem;
    letter-spacing: .25em;
  }
  .separator::before, .separator::after {
    content: "";
    display: inline-block;
    vertical-align: middle;
    width: 3rem;
    height: 1px;
    background: var(--line);
    margin: 0 .7rem;
  }
  .chapter p { margin: 0 0 .72rem; }
  .chapter p.first .dropcap {
    font-family: var(--font-display);
    font-size: 3.2em;
    line-height: .8;
    float: left;
    padding: .04em .1em 0 0;
    color: var(--accent);
  }
"""

FRONT_PAGE_CSS = """
  @page { size: A4; margin: 24mm 21mm 21mm; }
  @page cover { margin: 0; }
"""

BODY_PAGE_CSS = f"""
  @page {{
    size: A4;
    margin: 22mm 20mm 20mm;
    @top-center {{
      content: "{RUNNING_HEAD}";
      font-family: "Vollkorn", serif;
      font-style: italic;
      font-size: 8.5pt;
      color: #a8792f;
      letter-spacing: .06em;
    }}
    @bottom-center {{
      content: counter(page);
      font-family: "Vollkorn", serif;
      font-size: 10pt;
      color: #a8792f;
    }}
  }}
"""

SCREEN_PAGE_CSS = BODY_PAGE_CSS + """
  @page cover { @top-center { content: none; } @bottom-center { content: none; } margin: 0; }
  .cover { page: cover; }
"""

# ---------- assemblage HTML (écran / web) ----------
screen_css = TYPO_CSS + COVER_CSS + FRONT_CSS + CHAP_CSS + SCREEN_PAGE_CSS

front_sections = f"""
  <section class="cover">
    <img class="cover-art" alt="" src="{COVER_DATA}">
    <div class="cover-text">
      <p class="cover-author">{escape(AUTHOR)}</p>
      <h1 class="cover-title">{BOOK_TITLE}</h1>
      <p class="cover-subtitle">{escape(BOOK_SUBTITLE)}</p>
    </div>
    <p class="cover-tagline">{escape(TAGLINE)}</p>
  </section>

  <section class="imprint imprint-page">
    <p class="ornament">☀</p>
    <p class="imprint-title"><strong>{BOOK_TITLE}</strong> — {escape(BOOK_SUBTITLE)}</p>
    <div class="imprint-rule"></div>
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
    css = TYPO_CSS + body_css
    return HTML(string=f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><style>
{css}
</style></head>
<body>
{body}
</body></html>""").render()

front_doc = page_doc(COVER_CSS + FRONT_CSS + FRONT_PAGE_CSS, front_sections)
body_doc = page_doc(BODY_PAGE_CSS + CHAP_CSS, f'<div class="chapter">\n{chapters_html}\n</div>')

merged = front_doc.copy(front_doc.pages + body_doc.pages)
merged.write_pdf(PDF_OUT)
print('OK PDF:', PDF_OUT, f'({len(front_doc.pages)}+{len(body_doc.pages)} pages)')
