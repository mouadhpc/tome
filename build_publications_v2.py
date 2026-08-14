#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère la publication du Tome 1 « La vie belle » à partir de la version
corrigée de l'auteur (Roman_tome_1_corrige.docx extrait).

- Source nettoyée  : roman_tome1_corrige_clean.txt (en-têtes harmonisés, fixes)
- HTML interactif  : La_vie_belle_Tome1.html  (livre vivant : thèmes, recherche,
  sommaire flottant, navigation clavier, extrait au hasard, reprise de lecture)
- PDF              : La_vie_belle_Tome1.pdf   (liminaires + corps numéroté)
"""
import re
from html import escape
from urllib.parse import quote

from weasyprint import HTML

SRC = '/tmp/opencode/roman_corrige.txt'
CLEAN_SRC = 'roman_tome1_corrige_clean.txt'
HTML_OUT = 'La_vie_belle_Tome1.html'
PDF_OUT = 'La_vie_belle_Tome1.pdf'

BOOK_TITLE = 'La vie belle'
BOOK_SUBTITLE = 'Tome 1 — Les Racines de l’espoir'
AUTHOR = 'Anais REJEB'
TAGLINE = 'Un roman sur la lumière, même quand la vie semble l’avoir éteinte.'
RUNNING_HEAD = f'{BOOK_TITLE} — {BOOK_SUBTITLE}'

# ---------------------------------------------------------------------------
# 1) Nettoyage de la source corrigée
# ---------------------------------------------------------------------------

# Sous-titres tout en majuscules : casse harmonisée (titre français).
TITLE_FIX = {
    'LE MEILLEUR INVESTISSEMENT': 'Le meilleur investissement',
    'LA REINE DU MARCHÉ': 'La reine du marché',
    'LE TOUR DE SIMON': 'Le tour de Simon',
    'CEUX QUI ÉTAIENT LÀ AVANT MOI': 'Ceux qui étaient là avant moi',
}
PROPER = {'simon', 'léa', 'émilie', 'alma', 'thomas', 'claire', 'rose',
          'romain', 'dalpond', 'camille', 'manon', 'vance', 'maurice'}


def french_title(s):
    if s != s.upper():
        return s
    words = [w for w in s.lower().split(' ') if w]
    if not words:
        return s
    out = [words[0][0].upper() + words[0][1:]]
    for w in words[1:]:
        out.append(w.capitalize() if w in PROPER else w)
    return ' '.join(out)


def clean_source(text):
    lines = text.split('\n')
    out = []
    in_ch22 = False
    for raw in lines:
        line = raw
        s = line.strip()
        if re.match(r'^CHAPITRE 22\b', s, re.I):
            in_ch22 = True
        elif re.match(r'^CHAPITRE 23\b', s, re.I):
            in_ch22 = False

        if in_ch22:
            # Camille (éducatrice du centre de Léa, Ch.22) → Manon
            # (la Camille de Vance & Co aux autres chapitres est conservée)
            line = line.replace('Camille', 'Manon')

        # coquilles typographiques
        line = line.replace("'", '’')                     # apostrophes courbes
        line = line.replace('Romain— une', 'Romain — une')

        # en-tête de chapitre : casse normalisée
        m = re.match(r'^(CHAPITRE|Chapitre)\s+(\d+)\s*', line)
        if m:
            line = re.sub(r'^(CHAPITRE|Chapitre)\s+(\d+)',
                          lambda mm: f'CHAPITRE {mm.group(2)}', line, count=1)
            # sous-titre accolé : casse harmonisée
            mm = re.match(r'^(CHAPITRE \d+)\s*[—-]\s*(.*)$', line)
            if mm:
                t = mm.group(2).strip()
                line = f'{mm.group(1)} — {french_title(t)}'
        out.append(line)

    # Fusion des sous-titres sur ligne dédiée : « CHAPITRE N » + ligne courte
    merged = []
    for i, line in enumerate(out):
        if re.match(r'^CHAPITRE \d+$', line.strip()):
            nxt = out[i + 1].strip() if i + 1 < len(out) else ''
            if nxt and len(nxt.split(' ')) <= 8 and not re.search(r'[.!?]$', nxt):
                merged.append(f'{line.strip()} — {nxt}')
                out[i + 1] = '\u0000'  # ligne consommée comme sous-titre
                continue
        merged.append(line)
    return '\n'.join(m for m in merged if m != '\u0000')


raw = open(SRC, encoding='utf-8').read()
clean = clean_source(raw)
open(CLEAN_SRC, 'w', encoding='utf-8').write(clean)
print('OK source nettoyée:', CLEAN_SRC)

# ---------------------------------------------------------------------------
# 2) Parsing des chapitres
# ---------------------------------------------------------------------------
lines = clean.split('\n')
chap_re = re.compile(r'^CHAPITRE (\d+)(?:\s*—\s*(.*))?$')

chapters = []
cur = None
blocks = []


def flush():
    global cur, blocks
    if cur is not None and blocks:
        cur['blocks'] = blocks
    blocks = []


for raw_line in lines:
    line = raw_line.strip()
    if not line:
        continue
    m = chap_re.match(line)
    if m:
        flush()
        num = int(m.group(1))
        title = (m.group(2) or '').strip()
        cur = {'num': num, 'title': title, 'blocks': []}
        chapters.append(cur)
        blocks = cur['blocks']
        continue
    if line == 'ÉPILOGUE':
        flush()
        cur = {'num': None, 'title': None, 'blocks': []}
        chapters.append(cur)
        blocks = cur['blocks']
        continue
    if line == '✦':
        blocks.append(('sep', ''))
    else:
        blocks.append(('p', line))
flush()

print(f'Chapitres parsés : {sum(1 for c in chapters if c["num"])} '
      f'({len(chapters)} sections dont épilogue)')

# ---------------------------------------------------------------------------
# 3) HTML — corps des chapitres
# ---------------------------------------------------------------------------
CH_ORNAMENT = '☀'


def chap_blocks_html(c):
    out = []
    first_p = True
    for kind, text in c['blocks']:
        if kind == 'sep':
            out.append('<div class="separator">' + CH_ORNAMENT + '</div>')
            first_p = True
            continue
        if first_p and text[:1].isalpha():
            out.append(f'<p class="first"><span class="dropcap">{escape(text[:1])}</span>{escape(text[1:])}</p>')
        else:
            out.append(f'<p>{escape(text)}</p>')
        first_p = False
    return '\n'.join(out)


def chap_section_html(c, interactive):
    if c['num'] is not None:
        head = (f'<div class="chap-ornament">{CH_ORNAMENT}</div>'
                f'<h1 class="chap-num">CHAPITRE {c["num"]}</h1>')
        if c['title']:
            head += f'<h2 class="chap-title">{escape(c["title"])}</h2>'
        anchor = f'chapitre-{c["num"]}'
    else:
        head = (f'<div class="chap-ornament">{CH_ORNAMENT}</div>'
                f'<h1 class="chap-num">ÉPILOGUE</h1>')
        anchor = 'epilogue'
    return f'<section class="chapter" id="{anchor}" data-num="{c["num"] or "epi"}">\n' \
           f'  <header class="chap-head">{head}<div class="chap-rule"></div></header>\n' \
           f'  <div class="chap-body">\n{chap_blocks_html(c)}\n  </div>\n</section>'


chapters_html = '\n'.join(chap_section_html(c, True) for c in chapters)

# ---------------------------------------------------------------------------
# 4) Illustration de couverture (SVG)
# ---------------------------------------------------------------------------
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

<g class="stars">
<g class="star" style="animation-delay:.2s"><path d="M110 140 v10 M105 145 h10" stroke="#ffe9a4" stroke-width="3"/></g>
<g class="star" style="animation-delay:1.1s"><path d="M500 110 v10 M495 115 h10" stroke="#ffe9a4" stroke-width="3"/></g>
<g class="star" style="animation-delay:.6s"><path d="M540 300 v10 M535 305 h10" stroke="#ffe9a4" stroke-width="3"/></g>
<g class="star" style="animation-delay:1.6s"><path d="M70 330 v10 M65 335 h10" stroke="#ffe9a4" stroke-width="3"/></g>
<g class="star" style="animation-delay:.9s"><path d="M120 470 v10 M115 475 h10" stroke="#ffe9a4" stroke-width="3"/></g>
<g class="star" style="animation-delay:1.4s"><path d="M500 470 v10 M495 475 h10" stroke="#ffe9a4" stroke-width="3"/></g>
</g>

<circle class="halo" cx="300" cy="340" r="185" fill="url(#halo)"/>
<circle class="sun" cx="300" cy="340" r="100" fill="#ffe9a4"/>

<g class="rays" stroke="#ffdf8a" stroke-width="5" opacity="0.6" stroke-linecap="round">
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

<g class="motes">
<circle class="mote" cx="160" cy="560" r="2.4" fill="#ffe9a4"/>
<circle class="mote" cx="430" cy="540" r="3" fill="#ffd97a"/>
<circle class="mote" cx="250" cy="590" r="2" fill="#fff4c8"/>
<circle class="mote" cx="360" cy="570" r="2.6" fill="#ffe9a4"/>
<circle class="mote" cx="505" cy="600" r="2" fill="#ffdf8a"/>
<circle class="mote" cx="95" cy="610" r="2.8" fill="#ffe9a4"/>
<circle class="mote" cx="320" cy="530" r="2" fill="#fff4c8"/>
<circle class="mote" cx="205" cy="560" r="2.4" fill="#ffd97a"/>
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

# ---------------------------------------------------------------------------
# 5) HTML interactif
# ---------------------------------------------------------------------------

CSS = r"""
:root{
  --fs: 1.06rem;
  --lh: 1.75;
}
html[data-theme="aube"]{
  --bg:#fdf7ea; --ink:#2b2118; --paper:#fdf7ea; --line:#e3d3b0;
  --accent:#a35b24; --gold:#b8862e; --muted:#7a6a52; --panel:#fffdf5;
  --bar:#fff8ea; --shadow:0 10px 34px rgba(90,60,25,.16);
}
html[data-theme="sepia"]{
  --bg:#f2e6cf; --ink:#3a2f23; --paper:#f4ead8; --line:#d6c39a;
  --accent:#8a5a2b; --gold:#a0702a; --muted:#6b5b45; --panel:#f7efdd;
  --bar:#efe2c8; --shadow:0 10px 34px rgba(70,48,20,.18);
}
html[data-theme="nuit"]{
  --bg:#171210; --ink:#e8dcc4; --paper:#221a12; --line:#4a3a28;
  --accent:#d9a05f; --gold:#c8963e; --muted:#a08a6a; --panel:#2a2117;
  --bar:#201a13; --shadow:0 10px 34px rgba(0,0,0,.5);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; padding:0; background:var(--bg); color:var(--ink);
  font-family:"EB Garamond","DejaVu Serif",Georgia,"Times New Roman",serif;
  font-size:var(--fs); line-height:var(--lh);
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
a{color:inherit;text-decoration:none}
button{font-family:inherit;cursor:pointer;background:none;border:none;color:inherit}
::selection{background:rgba(184,134,46,.35)}

/* ---------- barre de progression ---------- */
#progress-bar{
  position:fixed; top:0; left:0; height:3px; width:0%;
  background:linear-gradient(90deg,var(--gold),#ffd97a,var(--gold));
  z-index:120; box-shadow:0 0 12px rgba(184,134,46,.6);
}

/* ---------- barre supérieure ---------- */
.topbar{
  position:fixed; top:0; left:0; right:0; z-index:110;
  display:flex; align-items:center; gap:.9rem;
  padding:.55rem 1.1rem;
  background:transparent; color:var(--ink);
  transition:background .35s, box-shadow .35s, backdrop-filter .35s;
}
.topbar.scrolled{
  background:var(--bar); box-shadow:var(--shadow);
  backdrop-filter:blur(8px);
}
.brand{display:flex;align-items:center;gap:.5rem;font-family:"Vollkorn",serif;font-weight:600;letter-spacing:.02em;white-space:nowrap}
.brand .sun{color:var(--gold);animation:pulse 4s ease-in-out infinite;display:inline-block}
.spacer{flex:1}
.tb-group{display:flex;align-items:center;gap:.2rem}
.tb-btn{
  display:inline-flex;align-items:center;justify-content:center;
  min-width:2.1rem; height:2.1rem; padding:0 .5rem; border-radius:999px;
  font-size:.95rem; color:var(--muted); transition:background .2s,color .2s;
}
.tb-btn:hover{background:rgba(184,134,46,.16);color:var(--accent)}
.tb-btn.active{background:rgba(184,134,46,.22);color:var(--accent)}
.tb-label{font-size:.78rem;color:var(--muted);letter-spacing:.04em;white-space:nowrap}
.chap-indicator{font-family:"Vollkorn",serif;font-size:.9rem;color:var(--muted);white-space:nowrap}
.chap-indicator b{color:var(--accent);font-weight:600}
@media (max-width:760px){
  .tb-label,.brand .sub{display:none}
  .tb-group.grow{order:3;width:100%;justify-content:center;margin-top:.15rem}
}

/* ---------- couverture ---------- */
.cover{
  position:relative; min-height:100svh; overflow:hidden;
  display:flex; flex-direction:column; justify-content:center;
  isolation:isolate;
}
.cover-svg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-2}
.cover-svg .star{animation:twinkle 3.4s ease-in-out infinite}
.cover-svg .sun{transform-origin:300px 340px;animation:pulse 5.5s ease-in-out infinite}
.cover-svg .halo{transform-origin:300px 340px;animation:pulse 5.5s ease-in-out infinite}
.cover-svg .rays{transform-origin:300px 340px;animation:rayspin 90s linear infinite}
.cover-svg .mote{animation:mote 11s linear infinite}
.cover-svg .mote:nth-child(2){animation-duration:13s}
.cover-svg .mote:nth-child(3){animation-duration:9s}
.cover-svg .mote:nth-child(4){animation-duration:15s}
.cover-svg .mote:nth-child(5){animation-duration:10s}
.cover-svg .mote:nth-child(6){animation-duration:14s}
.cover-svg .mote:nth-child(7){animation-duration:12s}
.cover-svg .mote:nth-child(8){animation-duration:9.5s}
.cover-inner{text-align:center;padding:6rem 1.5rem;color:#fff4dc}
.cover-author{
  margin:0;text-transform:uppercase;letter-spacing:.42em;font-size:.8rem;
  color:#f3d9a4;font-family:"Vollkorn",serif;animation:rise 1.2s ease both;
}
.cover-title{
  margin:1.1rem 0 0;font-size:clamp(2.6rem,8vw,4.4rem);font-weight:600;
  color:#fff7e4;font-family:"Vollkorn",serif;letter-spacing:.02em;
  text-shadow:0 2px 30px rgba(26,13,5,.6);
  background:linear-gradient(100deg,#fff7e4,#ffd97a 40%,#fff7e4 70%);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  animation:rise 1.2s .1s ease both;
}
.cover-subtitle{
  margin:.5rem 0 0;font-style:italic;font-size:clamp(1.05rem,2.6vw,1.4rem);
  color:#ffdd94;font-family:"Vollkorn",serif;letter-spacing:.05em;animation:rise 1.2s .2s ease both;
}
.cover-tagline{
  margin:2.2rem auto 0;max-width:34rem;font-style:italic;font-size:1rem;color:#fff0c9;
  text-shadow:0 1px 14px rgba(26,13,5,.6);animation:rise 1.2s .3s ease both;
}
.cover-tagline::before,.cover-tagline::after{
  content:"";display:inline-block;vertical-align:middle;width:2.4rem;height:1px;
  background:rgba(255,240,201,.75);margin:0 .8rem;
}
.cover-stats{
  margin:1.4rem auto 0;font-size:.82rem;letter-spacing:.22em;text-transform:uppercase;
  color:#ffd7a0;animation:rise 1.2s .4s ease both;
}
.scroll-hint{
  position:absolute;bottom:1.4rem;left:50%;transform:translateX(-50%);
  color:#fff0c9;font-size:.82rem;letter-spacing:.3em;text-transform:uppercase;
  animation:floaty 2.6s ease-in-out infinite;
}
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.95}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
@keyframes rayspin{to{transform:rotate(360deg)}}
@keyframes mote{0%{transform:translateY(0);opacity:0}15%{opacity:.8}100%{transform:translateY(-52vh);opacity:0}}
@keyframes floaty{0%,100%{transform:translate(-50%,0)}50%{transform:translate(-50%,-8px)}}

/* ---------- page d'emprunt & sommaire ---------- */
.imprint{
  max-width:44rem;margin:0 auto;padding:5rem 1.5rem;text-align:center;color:var(--muted);
  display:flex;flex-direction:column;justify-content:center;min-height:70vh;
}
.imprint .ornament{color:var(--gold);font-size:1.15rem;margin:0 0 1.8rem}
.imprint-title{font-family:"Vollkorn",serif;font-size:1.18rem;color:var(--ink);margin:0}
.imprint-rule{width:4.5rem;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:1.1rem auto}
.imprint-copy{margin:.4rem 0 0;font-size:.95rem}
.imprint-fiction{margin:1.6rem auto 0;max-width:34rem;font-size:.88rem}

.toc{max-width:44rem;margin:0 auto;padding:2rem 1.5rem 5rem}
.toc h2{
  font-family:"Vollkorn",serif;font-size:1.3rem;font-weight:600;text-align:center;
  letter-spacing:.26em;text-transform:uppercase;color:var(--accent);margin:0 0 .4rem;
}
.toc h2::after{content:"";display:block;width:5rem;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:.9rem auto 1.8rem}
.toc ol{list-style:none;padding:0;margin:0;columns:2;column-gap:2.2rem}
@media(max-width:640px){.toc ol{columns:1}}
.toc li{break-inside:avoid}
.toc li a{
  display:flex;align-items:baseline;gap:.55rem;padding:.42rem .2rem;
  border-bottom:1px dotted var(--line);color:var(--ink);
  transition:color .2s, padding-left .2s;
}
.toc li a:hover{color:var(--accent);padding-left:.35rem}
.toc li a.active{color:var(--accent)}
.toc-num{font-family:"Vollkorn",serif;font-weight:600;color:var(--gold);min-width:1.9rem}
.toc-tit{flex:1}

/* ---------- chapitres ---------- */
.chapter{max-width:44rem;margin:0 auto;padding:3.2rem 1.5rem 1rem}
.chapter{opacity:0;transform:translateY(16px);transition:opacity .9s ease,transform .9s ease}
.chapter.visible{opacity:1;transform:none}
.chap-head{text-align:center;margin:0 0 1.6rem}
.chap-ornament{color:var(--gold);font-size:1.05rem;margin:0 0 .7rem;animation:pulse 4s ease-in-out infinite;display:inline-block}
h1.chap-num{
  font-family:"Vollkorn",serif;font-size:1rem;font-weight:600;letter-spacing:.4em;
  text-indent:.4em;color:var(--accent);margin:0;text-transform:uppercase;
}
h2.chap-title{
  font-family:"Vollkorn",serif;font-size:clamp(1.4rem,4vw,1.8rem);font-weight:500;
  color:var(--ink);margin:.45rem 0 0;
}
.chap-rule{
  width:6.5rem;height:2px;margin:1.1rem auto 0;
  background:linear-gradient(90deg,transparent,var(--gold),transparent);
}
.chap-body p{margin:0 0 .75rem;text-align:justify;hyphens:auto}
.chap-body p.first .dropcap{
  font-family:"Vollkorn",serif;font-size:3.3em;line-height:.82;float:left;
  padding:.05em .12em 0 0;color:var(--accent);transition:text-shadow .3s;
}
.chap-body p.first .dropcap:hover{text-shadow:0 0 18px rgba(184,134,46,.5)}
.separator{
  text-align:center;margin:2.4rem 0;color:var(--gold);font-size:.85rem;letter-spacing:.25em;
  display:flex;align-items:center;justify-content:center;gap:.8rem;
}
.separator::before,.separator::after{content:"";display:inline-block;width:3rem;height:1px;background:var(--line)}

/* ---------- panneaux (recherche, sommaire, citation) ---------- */
.panel{
  position:fixed;top:3.4rem;right:1rem;z-index:115;width:min(24rem,92vw);
  background:var(--panel);color:var(--ink);border:1px solid var(--line);
  border-radius:14px;box-shadow:var(--shadow);padding:1rem 1.1rem;
  transform:translateY(-8px);opacity:0;pointer-events:none;
  transition:opacity .25s,transform .25s;max-height:70vh;display:flex;flex-direction:column;
}
.panel.open{transform:none;opacity:1;pointer-events:auto}
.panel h3{margin:0 0 .6rem;font-family:"Vollkorn",serif;font-size:.95rem;letter-spacing:.18em;text-transform:uppercase;color:var(--accent)}
.search-input{
  width:100%;padding:.55rem .7rem;border-radius:9px;border:1px solid var(--line);
  background:var(--paper);color:var(--ink);font-family:inherit;font-size:.98rem;
  outline:none;transition:border-color .2s,box-shadow .2s;
}
.search-input:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(184,134,46,.15)}
#search-results{list-style:none;margin:.6rem 0 0;padding:0;overflow-y:auto}
#search-results li{padding:.45rem .3rem;border-bottom:1px dotted var(--line);cursor:pointer;border-radius:6px}
#search-results li:hover{background:rgba(184,134,46,.12)}
#search-results .sn{display:block;font-family:"Vollkorn",serif;font-size:.78rem;color:var(--gold);letter-spacing:.1em;text-transform:uppercase;margin-bottom:.15rem}
#search-results .sx{font-size:.92rem;line-height:1.45}
mark{background:rgba(255,213,102,.55);color:inherit;border-radius:3px;padding:0 .1em}
.panel-close{
  position:absolute;top:.55rem;right:.6rem;width:1.8rem;height:1.8rem;border-radius:50%;
  color:var(--muted);font-size:1rem;
}
.panel-close:hover{background:rgba(184,134,46,.18);color:var(--accent)}
.toc-panel ol{list-style:none;margin:0;padding:0;overflow-y:auto}
.toc-panel li a{display:flex;gap:.5rem;padding:.32rem .15rem;border-bottom:1px dotted var(--line);font-size:.95rem}
.toc-panel li a:hover{color:var(--accent)}

#quote-modal{
  position:fixed;inset:0;z-index:130;display:flex;align-items:center;justify-content:center;
  background:rgba(20,12,5,.55);backdrop-filter:blur(3px);
  opacity:0;pointer-events:none;transition:opacity .3s;
}
#quote-modal.open{opacity:1;pointer-events:auto}
.quote-card{
  width:min(36rem,92vw);background:var(--panel);color:var(--ink);border-radius:18px;
  box-shadow:var(--shadow);padding:2.4rem 2.2rem 1.8rem;text-align:center;
  border:1px solid var(--line);transform:translateY(10px);transition:transform .3s;
}
#quote-modal.open .quote-card{transform:none}
.quote-card .qo{color:var(--gold);font-size:1.3rem;margin:0 0 .8rem}
.quote-card blockquote{margin:0;font-size:1.12rem;font-style:italic;line-height:1.6}
.quote-card .qc{margin:.9rem 0 0;font-family:"Vollkorn",serif;font-size:.82rem;letter-spacing:.2em;text-transform:uppercase;color:var(--accent)}
.quote-card .qb{display:flex;justify-content:center;gap:.6rem;margin-top:1.5rem}
.quote-card .qb button{
  padding:.5rem 1rem;border-radius:999px;border:1px solid var(--line);color:var(--muted);font-size:.9rem;
  transition:background .2s,color .2s;
}
.quote-card .qb button:hover{background:rgba(184,134,46,.18);color:var(--accent)}

/* ---------- reprise de lecture ---------- */
#resume-btn{
  position:fixed;bottom:1.4rem;left:50%;transform:translateX(-50%) translateY(20px);
  z-index:125;opacity:0;pointer-events:none;transition:opacity .35s,transform .35s;
  padding:.6rem 1.3rem;border-radius:999px;font-size:.92rem;letter-spacing:.06em;
  color:#fff4dc;background:linear-gradient(135deg,#b3762e,#8a5a2b);box-shadow:0 8px 24px rgba(70,40,10,.4);
}
#resume-btn.show{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}
#resume-btn:hover{filter:brightness(1.08)}

/* ---------- retour haut / bas ---------- */
#to-top{
  position:fixed;right:1.1rem;bottom:1.1rem;z-index:125;width:2.6rem;height:2.6rem;
  border-radius:50%;background:var(--panel);border:1px solid var(--line);color:var(--gold);
  font-size:1.05rem;box-shadow:var(--shadow);opacity:0;pointer-events:none;transition:opacity .3s;
}
#to-top.show{opacity:1;pointer-events:auto}
#to-top:hover{color:var(--accent)}

footer.pagefoot{
  max-width:44rem;margin:0 auto;padding:3rem 1.5rem 4rem;text-align:center;
  color:var(--muted);font-size:.9rem;font-style:italic;
}
footer.pagefoot .ornament{color:var(--gold);display:block;margin:0 0 .7rem}

@media print{
  .topbar,#progress-bar,.scroll-hint,#to-top,#resume-btn,.panel,#quote-modal{display:none !important}
  .chapter{opacity:1;transform:none;break-before:page}
  .cover{min-height:auto;break-after:page}
  body{font-size:1.05rem}
}
"""

JS = r"""
(function(){
  'use strict';
  var $ = function(s,c){return (c||document).querySelector(s);};
  var $$ = function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s));};
  var doc = document, html = doc.documentElement, body = doc.body;
  var store = {
    get:function(k){ try{return localStorage.getItem(k);}catch(e){return null;} },
    set:function(k,v){ try{localStorage.setItem(k,v);}catch(e){} }
  };

  /* ---------- thèmes ---------- */
  var THEMES=['aube','sepia','nuit'];
  if(THEMES.indexOf(store.get('lvb_theme'))>-1) html.setAttribute('data-theme',store.get('lvb_theme'));
  $$('[data-theme-btn]').forEach(function(btn){
    if(btn.getAttribute('data-theme-btn')===html.getAttribute('data-theme')) btn.classList.add('active');
    btn.addEventListener('click',function(){
      html.setAttribute('data-theme',btn.getAttribute('data-theme-btn'));
      store.set('lvb_theme',html.getAttribute('data-theme'));
      $$('[data-theme-btn]').forEach(function(b){b.classList.toggle('active',b===btn);});
    });
  });

  /* ---------- taille de police ---------- */
  var fs = parseFloat(store.get('lvb_font')) || 1.06;
  fs = Math.max(0.92,Math.min(1.42,fs));
  var applyFont=function(){ html.style.setProperty('--fs',fs+'rem'); };
  applyFont();
  $('#font-minus').addEventListener('click',function(){fs=Math.max(0.92,fs-0.06);store.set('lvb_font',fs);applyFont();});
  $('#font-plus').addEventListener('click',function(){fs=Math.min(1.42,fs+0.06);store.set('lvb_font',fs);applyFont();});

  /* ---------- plein écran ---------- */
  var fsBtn=$('#fullscreen');
  fsBtn.addEventListener('click',function(){
    if(!doc.fullscreenElement){
      (doc.documentElement.requestFullscreen||doc.documentElement.webkitRequestFullscreen).call(doc.documentElement);
    } else {
      (doc.exitFullscreen||doc.webkitExitFullscreen).call(doc);
    }
  });

  /* ---------- barre de progression + topbar ---------- */
  var bar=$('#progress-bar'), topbar=$('.topbar');
  var lastSave=0;
  function onScroll(){
    var st=html.scrollTop||body.scrollTop;
    var max=(html.scrollHeight-html.clientHeight)||1;
    var pct=Math.min(100,Math.max(0,st/max*100));
    bar.style.width=pct+'%';
    topbar.classList.toggle('scrolled',st>40);
    $('#to-top').classList.toggle('show',st>900);
    if(Date.now()-lastSave>800){lastSave=Date.now();store.set('lvb_pos',String(st));}
  }
  doc.addEventListener('scroll',onScroll,{passive:true});
  onScroll();
  $('#to-top').addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});

  /* ---------- navigation chapitres ---------- */
  var chapters=$$('section.chapter');
  function chapIndex(){
    var st=html.scrollTop||body.scrollTop;
    for(var i=chapters.length-1;i>=0;i--){
      if(chapters[i].getBoundingClientRect().top<window.innerHeight*0.5) return i;
    }
    return 0;
  }
  function gotoChapter(i){
    i=Math.max(0,Math.min(chapters.length-1,i));
    chapters[i].scrollIntoView({behavior:'smooth',block:'start'});
  }
  $('#nav-prev').addEventListener('click',function(){gotoChapter(chapIndex()-1);});
  $('#nav-next').addEventListener('click',function(){gotoChapter(chapIndex()+1);});
  doc.addEventListener('keydown',function(e){
    if($('.panel.open')||$('#quote-modal.open')) return;
    if(e.key==='ArrowRight'){gotoChapter(chapIndex()+1);}
    if(e.key==='ArrowLeft'){gotoChapter(chapIndex()-1);}
  });

  /* ---------- scroll-spy : sommaire + indicateur ---------- */
  var tocLinks=$$('.toc li a'), indicator=$('#cur-chap');
  var spy=new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(!en.isIntersecting) return;
      var id=en.target.id;
      tocLinks.forEach(function(a){
        a.classList.toggle('active',a.getAttribute('href')==='#'+id);
      });
      var n=en.target.getAttribute('data-num');
      if(indicator && n!=='epi'){
        indicator.textContent=n+' / '+chapters.length;
      } else if(indicator){
        indicator.textContent='Épilogue';
      }
    });
  },{rootMargin:'-45% 0px -50% 0px'});
  chapters.forEach(function(c){spy.observe(c);});

  /* ---------- révélation des chapitres ---------- */
  var reveal=new IntersectionObserver(function(entries){
    entries.forEach(function(en){if(en.isIntersecting){en.target.classList.add('visible');reveal.unobserve(en.target);}});
  },{threshold:0.04});
  chapters.forEach(function(c){reveal.observe(c);});

  /* ---------- panneaux ---------- */
  function closePanels(){$$('.panel').forEach(function(p){p.classList.remove('open');});}
  $('#btn-sommaire').addEventListener('click',function(e){
    e.stopPropagation();
    var p=$('#sommaire-panel');var open=p.classList.toggle('open');
    $('#search-panel').classList.remove('open');
    if(open)p.querySelector('ol').scrollTop=0;
  });
  $('#btn-search').addEventListener('click',function(e){
    e.stopPropagation();
    var p=$('#search-panel');var open=p.classList.toggle('open');
    $('#sommaire-panel').classList.remove('open');
    if(open){$('#search-input').focus();}
  });
  $$('.panel-close').forEach(function(b){
    b.addEventListener('click',function(){b.closest('.panel').classList.remove('open');});
  });
  doc.addEventListener('click',function(e){
    if(!e.target.closest('.panel')&&!e.target.closest('#btn-sommaire')&&!e.target.closest('#btn-search'))closePanels();
  });
  doc.addEventListener('keydown',function(e){if(e.key==='Escape'){closePanels();$('#quote-modal').classList.remove('open');}});

  /* ---------- recherche ---------- */
  var paragraphs=$$('.chap-body p');
  function norm(s){return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
  var searchInput=$('#search-input'), results=$('#search-results'), empty=$('#search-empty');
  function doSearch(){
    var q=norm(searchInput.value).trim();
    results.innerHTML='';empty.textContent='';
    if(q.length<3){empty.textContent='Tapez au moins 3 lettres.';return;}
    var hits=[];
    for(var i=0;i<paragraphs.length;i++){
      var txt=paragraphs[i].textContent, n=norm(txt);
      var idx=n.indexOf(q);
      if(idx>-1){
        var sec=paragraphs[i].closest('.chapter');
        var num=sec?sec.getAttribute('data-num'):'';
        hits.push({el:paragraphs[i],txt:txt,num:num});
        if(hits.length>=60) break;
      }
    }
    if(!hits.length){empty.textContent='Aucune occurrence trouvée.';return;}
    hits.forEach(function(h){
      var li=doc.createElement('li');
      var lab=doc.createElement('span');lab.className='sn';
      lab.textContent=(h.num==='epi')?'Épilogue':'Chapitre '+h.num;
      var sn=doc.createElement('span');sn.className='sx';
      var t=h.txt.length>140?h.txt.slice(0,140)+'…':h.txt;
      sn.textContent=t;
      li.appendChild(lab);li.appendChild(sn);
      li.addEventListener('click',function(){
        closePanels();
        h.el.scrollIntoView({behavior:'smooth',block:'center'});
        flash(h.el,q);
      });
      results.appendChild(li);
    });
  }
  function flash(par,query){
    var nq=norm(query);
    $$('mark').forEach(function(m){var w=doc.createTextNode(m.textContent);m.parentNode.replaceChild(w,m);});
    var walker=doc.createTreeWalker(par,NodeFilter.SHOW_TEXT,null,false);
    var nodes=[];var node;
    while((node=walker.nextNode())){ if(norm(node.textContent).indexOf(nq)>-1) nodes.push(node); }
    nodes.forEach(function(nd){
      var t=nd.textContent, nt=norm(t);
      var pieces=[],pos=0,k;
      while((k=nt.indexOf(nq,pos))>-1){
        if(k>pos)pieces.push(t.slice(pos,k));
        var mk=doc.createElement('mark');mk.textContent=t.slice(k,k+query.length);
        pieces.push(mk.outerHTML);
        pos=k+query.length;
      }
      if(pos<t.length)pieces.push(t.slice(pos));
      var span=doc.createElement('span');span.innerHTML=pieces.join('');
      nd.parentNode.replaceChild(span,nd);
    });
  }
  var debounce;
  searchInput.addEventListener('input',function(){clearTimeout(debounce);debounce=setTimeout(doSearch,240);});
  searchInput.addEventListener('keydown',function(e){if(e.key==='Enter'){clearTimeout(debounce);doSearch();}});

  /* ---------- extrait au hasard ---------- */
  var quoteModal=$('#quote-modal');
  function randomQuote(){
    var pool=paragraphs.filter(function(p){return p.textContent.trim().length>110;});
    var p=pool[Math.floor(Math.random()*pool.length)];
    var sec=p.closest('.chapter');
    $('#quote-text').textContent='« '+p.textContent.trim()+' »';
    $('#quote-chap').textContent=(sec&&sec.getAttribute('data-num')!=='epi')?'Chapitre '+sec.getAttribute('data-num')+' — La vie belle':'Épilogue — La vie belle';
  }
  $('#btn-quote').addEventListener('click',function(e){e.stopPropagation();randomQuote();quoteModal.classList.add('open');});
  $('#quote-new').addEventListener('click',randomQuote);
  $('#quote-close').addEventListener('click',function(){quoteModal.classList.remove('open');});
  quoteModal.addEventListener('click',function(e){if(e.target===quoteModal)quoteModal.classList.remove('open');});

  /* ---------- reprise de lecture ---------- */
  var saved=parseInt(store.get('lvb_pos')||'0',10);
  if(saved>400){
    var rb=$('#resume-btn');
    rb.classList.add('show');
    rb.addEventListener('click',function(){
      window.scrollTo({top:saved,behavior:'smooth'});
      rb.classList.remove('show');
    });
  }
})();
"""


def toc_links_html(c):
    if c['num'] is not None:
        anchor, num, title = f'chapitre-{c["num"]}', c['num'], c['title'] or ''
    else:
        anchor, num, title = 'epilogue', '', 'Épilogue'
    return (f'<li><a href="#{anchor}">'
            f'<span class="toc-num">{num}</span>'
            f'<span class="toc-tit">{escape(title)}</span></a></li>')


def toc_section_html(cls='toc'):
    items = '\n'.join(toc_links_html(c) for c in chapters)
    return f'''<section class="{cls}">
  <h2>Sommaire</h2>
  <ol>{items}</ol>
</section>'''


words_total = sum(len(b[1].split()) for c in chapters for b in c['blocks'])
read_min = round(words_total / 200)
read_h, read_m = divmod(read_min, 60)
stat_line = (f'{sum(1 for c in chapters if c["num"])} chapitres · '
             f'{words_total:,} mots · ≈ {read_h} h {read_m:02d} de lecture'.replace(',', ' '))

def short_link_html(c):
    if c['num'] is not None:
        anchor = f'chapitre-{c["num"]}'
        num = str(c['num'])
        title = c['title'] or ''
    else:
        anchor = 'epilogue'
        num = ''
        title = 'Épilogue'
    return (f'<li><a href="#{anchor}">'
            f'<span class="toc-num">{num}</span>'
            f'<span class="toc-tit">{escape(title)}</span></a></li>')


toc_short_items = '\n'.join(short_link_html(c) for c in chapters)

html_doc = f"""<!DOCTYPE html>
<html lang="fr" data-theme="aube">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{BOOK_TITLE} — {escape(BOOK_SUBTITLE)}</title>
<meta name="author" content="{escape(AUTHOR)}">
<meta name="description" content="{escape(BOOK_TITLE)} — {escape(BOOK_SUBTITLE)}. Roman. Version interactive.">
<style>{CSS}</style>
</head>
<body>
<div id="progress-bar"></div>

<header class="topbar" id="topbar">
  <a class="brand" href="#couverture"><span class="sun">{CH_ORNAMENT}</span> <span>La vie belle</span><span class="sub">&nbsp;· {escape(BOOK_SUBTITLE)}</span></a>
  <span class="spacer"></span>
  <span class="chap-indicator">Chapitre <b id="cur-chap">1 / {len(chapters)}</b></span>
  <div class="tb-group">
    <button class="tb-btn" id="nav-prev" title="Chapitre précédent (←)">‹</button>
    <button class="tb-btn" id="nav-next" title="Chapitre suivant (→)">›</button>
  </div>
  <div class="tb-group">
    <button class="tb-btn" data-theme-btn="aube" title="Thème aube">☀</button>
    <button class="tb-btn" data-theme-btn="sepia" title="Thème sépia">☖</button>
    <button class="tb-btn" data-theme-btn="nuit" title="Thème nuit">☾</button>
  </div>
  <div class="tb-group">
    <button class="tb-btn" id="font-minus" title="Réduire le texte">A−</button>
    <button class="tb-btn" id="font-plus" title="Agrandir le texte">A+</button>
  </div>
  <div class="tb-group">
    <button class="tb-btn" id="btn-quote" title="Un rayon de lumière au hasard">✶</button>
    <button class="tb-btn" id="btn-search" title="Rechercher dans le roman">⌕</button>
    <button class="tb-btn" id="btn-sommaire" title="Sommaire">☰</button>
    <button class="tb-btn" id="fullscreen" title="Plein écran">⛶</button>
  </div>
</header>

<aside class="panel" id="sommaire-panel">
  <button class="panel-close" aria-label="Fermer">×</button>
  <h3>Sommaire</h3>
  <ol>{toc_short_items}</ol>
</aside>

<aside class="panel" id="search-panel">
  <button class="panel-close" aria-label="Fermer">×</button>
  <h3>Recherche</h3>
  <input class="search-input" id="search-input" type="search" placeholder="Rechercher dans le roman…" autocomplete="off">
  <ul id="search-results"></ul>
  <p id="search-empty" style="margin:.5rem .1rem 0;color:var(--muted);font-size:.9rem"></p>
</aside>

<section class="cover" id="couverture">
  <svg class="cover-svg" viewBox="0 0 600 850" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Soleil levant sur un arbre aux racines profondes">{{COVER_SVG_INLINE}}</svg>
  <div class="cover-inner">
    <p class="cover-author">{escape(AUTHOR)}</p>
    <h1 class="cover-title">{BOOK_TITLE}</h1>
    <p class="cover-subtitle">{escape(BOOK_SUBTITLE)}</p>
    <p class="cover-tagline">{escape(TAGLINE)}</p>
    <p class="cover-stats">{stat_line}</p>
  </div>
  <div class="scroll-hint">Déroulez&nbsp;&nbsp;↓</div>
</section>

<section class="imprint">
  <p class="ornament">{CH_ORNAMENT}</p>
  <p class="imprint-title"><strong>{BOOK_TITLE}</strong> — {escape(BOOK_SUBTITLE)}</p>
  <div class="imprint-rule"></div>
  <p class="imprint-copy">© 2026 {escape(AUTHOR)}<br>Tous droits réservés.<br>Toute reproduction, même partielle, est interdite.</p>
  <p class="imprint-fiction">Ceci est une œuvre de fiction. Toute ressemblance avec des personnes ou des situations réelles serait purement fortuite.</p>
</section>

{toc_section_html('toc')}

{chapters_html}

<footer class="pagefoot">
  <span class="ornament">{CH_ORNAMENT}</span>
  {BOOK_TITLE} — {escape(BOOK_SUBTITLE)}<br>© 2026 {escape(AUTHOR)}
</footer>

<div id="quote-modal">
  <div class="quote-card">
    <p class="qo">{CH_ORNAMENT}</p>
    <blockquote id="quote-text"></blockquote>
    <p class="qc" id="quote-chap"></p>
    <div class="qb">
      <button id="quote-new">Un autre rayon de lumière</button>
      <button id="quote-close">Fermer</button>
    </div>
  </div>
</div>

<button id="resume-btn" title="Reprendre la lecture">☀ Reprendre la lecture</button>
<button id="to-top" title="Retour en haut">↑</button>

<script>{JS}</script>
</body>
</html>
"""

# SVG inline : on retire la balise xml et on garde le contenu à l'intérieur du <svg>
_svg_inner = COVER_SVG.split('>', 1)[1].rsplit('</svg>', 1)[0]
html_doc = html_doc.replace('{COVER_SVG_INLINE}', _svg_inner)

open(HTML_OUT, 'w', encoding='utf-8').write(html_doc)
print('OK HTML interactif:', HTML_OUT, f'({len(html_doc)} octets)')

# ---------------------------------------------------------------------------
# 6) PDF (WeasyPrint) — liminaires + corps fusionnés, corps numéroté à partir de 1
# ---------------------------------------------------------------------------

CSS_PDF = r"""
:root{
  --ink:#2b2118; --accent:#a35b24; --gold:#b8862e; --gold-soft:#d9b96a;
  --green:#6f8a52; --paper:#fdf7ea; --line:#e3d3b0;
  --font-body:"EB Garamond","DejaVu Serif",Georgia,"Times New Roman",serif;
  --font-display:"Vollkorn","EB Garamond","DejaVu Serif",Georgia,serif;
}
*{box-sizing:border-box}
html{-webkit-font-smoothing:antialiased}
body{
  font-family:var(--font-body);color:var(--ink);background:#fff;margin:0 auto;
  max-width:46rem;padding:0;line-height:1.7;font-size:1.05rem;text-align:justify;hyphens:auto;
}
a{color:inherit;text-decoration:none}
.cover{position:relative;page:cover;break-after:page;overflow:hidden}
.cover-art{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.cover-text{position:absolute;left:0;right:0;top:12%;text-align:center}
.cover-author{margin:0;text-transform:uppercase;letter-spacing:.38em;font-size:.82rem;color:#f3d9a4;font-family:var(--font-display)}
.cover-title{margin:1.1rem 0 0;font-size:3.4rem;font-weight:600;color:#fff4dc;font-family:var(--font-display);letter-spacing:.03em;text-shadow:0 2px 24px rgba(26,13,5,.55)}
.cover-subtitle{margin:.4rem 0 0;font-style:italic;font-size:1.25rem;color:#ffdd94;font-family:var(--font-display);letter-spacing:.06em}
.cover-tagline{position:absolute;left:0;right:0;top:58%;text-align:center;margin:0;font-style:italic;font-size:1.02rem;color:#fff0c9;padding:0 3rem;text-shadow:0 1px 14px rgba(26,13,5,.6)}
.cover-tagline::before,.cover-tagline::after{content:"";display:inline-block;vertical-align:middle;width:2.6rem;height:1px;background:rgba(255,240,201,.7);margin:0 .9rem}
@media print{.cover{width:210mm;height:297mm}}

.imprint{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;color:#5c4a36;font-size:.92rem;line-height:1.9;min-height:calc(100vh - 45mm)}
.imprint .ornament{color:var(--gold);font-size:1.1rem;margin:0 0 1.8rem}
.imprint-page{break-after:page}
.imprint-title{font-family:var(--font-display);font-size:1.15rem;color:var(--ink);margin:0}
.imprint-rule{width:4.5rem;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:1.1rem auto}
.imprint-copy{margin:.4rem 0 0}
.imprint-fiction{margin:1.5rem 0 0;max-width:34rem;font-size:.88rem}

.toc{margin:0;padding:1.5rem 1rem 3rem}
.toc h2{font-family:var(--font-display);font-size:1.35rem;font-weight:600;text-align:center;letter-spacing:.24em;text-transform:uppercase;color:var(--accent);margin:0 0 .4rem}
.toc h2::after{content:"";display:block;width:5rem;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:.9rem auto 1.6rem}
.toc ol{list-style:none;padding:0;margin:0}
.toc li{border-bottom:1px dotted var(--line)}
.toc li a{display:flex;align-items:baseline;gap:.5rem;text-align:left;padding:.34rem .2rem;color:var(--ink)}
.toc-title{flex:1}
.toc-page{color:var(--gold);font-family:var(--font-display);font-weight:600}
.toc-num{display:inline-block;min-width:2.2rem;color:var(--gold);font-family:var(--font-display);font-weight:600}

.chapter{padding:0}
h1.chap-num{font-family:var(--font-display);font-size:1.02rem;font-weight:600;letter-spacing:.4em;text-align:center;margin:3.4rem 0 .35rem;color:var(--accent);break-before:page}
.chapter h1.chap-num:first-child{break-before:auto}
h1.chap-num::before{content:"☀";display:block;font-size:.9rem;color:var(--gold);letter-spacing:0;margin-bottom:1rem;font-family:var(--font-body)}
h2.chap-title{font-family:var(--font-display);font-size:1.55rem;font-weight:500;text-align:center;margin:0 0 1rem;color:var(--ink)}
h2.chap-title::after{content:"";display:block;width:5rem;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:.85rem auto 2rem}
.separator{text-align:center;margin:2.2rem 0;color:var(--gold);font-size:.85rem;letter-spacing:.25em}
.separator::before,.separator::after{content:"";display:inline-block;vertical-align:middle;width:3rem;height:1px;background:var(--line);margin:0 .7rem}
.chapter p{margin:0 0 .72rem}
.chapter p.first .dropcap{font-family:var(--font-display);font-size:3.2em;line-height:.8;float:left;padding:.04em .1em 0 0;color:var(--accent)}
"""


def pdf_chap_html(c):
    if c['num'] is not None:
        head = (f'<h1 class="chap-num">CHAPITRE {c["num"]}</h1>'
                + (f'<h2 class="chap-title">{escape(c["title"])}</h2>' if c['title'] else ''))
    else:
        head = '<h1 class="chap-num">ÉPILOGUE</h1>'
    parts = [head]
    first_p = True
    for kind, text in c['blocks']:
        if kind == 'sep':
            parts.append('<div class="separator">☀</div>')
            first_p = True
            continue
        if first_p and text[:1].isalpha():
            parts.append(f'<p class="first"><span class="dropcap">{escape(text[:1])}</span>{escape(text[1:])}</p>')
        else:
            parts.append(f'<p>{escape(text)}</p>')
        first_p = False
    return '\n'.join(parts)


def pdf_chap_section(c):
    if c['num'] is not None:
        anchor = f'chapitre-{c["num"]}'
    else:
        anchor = 'epilogue'
    return f'<div class="chapter" id="{anchor}">\n{pdf_chap_html(c)}\n</div>'


def pdf_toc_html(c, page):
    if c['num'] is not None:
        anchor = f'chapitre-{c["num"]}'
        num = str(c['num'])
        title = c['title'] or ''
    else:
        anchor = 'epilogue'
        num = ''
        title = 'Épilogue'
    return (f'<li><a href="#{anchor}">'
            f'<span class="toc-num">{num}</span>'
            f'<span class="toc-title">{escape(title)}</span>'
            f'<span class="toc-page">{page}</span></a></li>')


body_chapters = '\n'.join(pdf_chap_section(c) for c in chapters)

PAGE_CSS = f"""
  @page {{ size: A4; margin: 24mm 21mm 21mm; }}
  @page cover {{ margin: 0; }}
  body {{ padding: 0; max-width: none; }}
"""
BODY_PAGE_CSS = f"""
  @page {{
    size: A4; margin: 22mm 20mm 20mm;
    @top-center {{
      content: "{RUNNING_HEAD}";
      font-family: "Vollkorn", serif; font-style: italic; font-size: 8.5pt;
      color: #a8792f; letter-spacing: .06em;
    }}
    @bottom-center {{
      content: counter(page);
      font-family: "Vollkorn", serif; font-size: 10pt; color: #a8792f;
    }}
  }}
"""


def render_doc(css_extra, body_html):
    return HTML(string=f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><style>
{CSS_PDF}
{css_extra}
</style></head>
<body>
{body_html}
</body></html>""").render()


# Corps rendu en premier : permet de relever la page de début de chaque chapitre
# via les ancres, pour remplir la table des matières (numéros de page littéraux).
body_doc = render_doc(BODY_PAGE_CSS, body_chapters)

page_of = {}
for idx, page in enumerate(body_doc.pages, start=1):
    for anchor in page.anchors:
        page_of.setdefault(anchor, idx)

pdf_toc_items = '\n'.join(pdf_toc_html(c, page_of.get(
    f'chapitre-{c["num"]}' if c['num'] else 'epilogue', '')) for c in chapters)

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
    <p class="imprint-copy">© 2026 {escape(AUTHOR)}<br>Tous droits réservés.<br>Toute reproduction, même partielle, est interdite.</p>
    <p class="imprint-fiction">Ceci est une œuvre de fiction. Toute ressemblance avec des personnes ou des situations réelles serait purement fortuite.</p>
  </section>

  <section class="toc toc-page">
    <h2>Sommaire</h2>
    <ol>
      {pdf_toc_items}
    </ol>
  </section>
"""

front_doc = render_doc(PAGE_CSS, front_sections)

merged = front_doc.copy(front_doc.pages + body_doc.pages)
merged.write_pdf(PDF_OUT)
print('OK PDF:', PDF_OUT, f'({len(front_doc.pages)}+{len(body_doc.pages)} pages)')
