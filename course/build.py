#!/usr/bin/env python3
"""Genera el sitio estático de DevOps Roadmap (GitHub Pages)."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from content import BOOKS, COURSE, DRILLS, PEDAGOGY, TOOLS, WEEKS

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "docs"
STATIC = ROOT / "static"

TOOL_CAT = {
    "Seguimiento del trabajo": ("semana-12.html", "Prácticas"),
    "Control de versiones": ("semana-01.html", "Git"),
    "CI/CD": ("semana-09.html", "CI/CD"),
    "Análisis de código": ("semana-13.html", "DevSecOps"),
    "Artefactos": ("semana-09.html", "CI/CD"),
    "Infraestructura como código": ("semana-08.html", "IaC"),
    "Contenedores y orquestación": ("semana-06.html", "Contenedores"),
    "Observabilidad": ("semana-10.html", "Monitoreo"),
    "Nube": ("semana-11.html", "Cloud"),
    "Seguridad": ("semana-13.html", "DevSecOps"),
}


def e(text: str) -> str:
    return html.escape(text, quote=True)


def slugify(text: str) -> str:
    trans = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    s = text.translate(trans).lower()
    out: list[str] = []
    dash = False
    for ch in s:
        if ch.isalnum():
            out.append(ch)
            dash = False
        elif not dash:
            out.append("-")
            dash = True
    return "".join(out).strip("-") or "s"


def render_block(block: tuple) -> str:
    kind = block[0]
    if kind == "h2":
        return f'<h2 id="{e(slugify(block[1]))}">{e(block[1])}</h2>'
    if kind == "h3":
        return f"<h3>{e(block[1])}</h3>"
    if kind == "p":
        return f"<p>{e(block[1])}</p>"
    if kind == "callout":
        return f'<div class="callout"><strong>{e(block[1])}</strong><span>{e(block[2])}</span></div>'
    if kind == "ul":
        items = "".join(f"<li>{e(i)}</li>" for i in block[1])
        return f"<ul>{items}</ul>"
    if kind == "ol":
        items = "".join(f"<li>{e(i)}</li>" for i in block[1])
        return f"<ol>{items}</ol>"
    if kind == "code":
        lang = e(block[1]) if len(block) > 1 else ""
        lang_tag = f'<span class="code-lang">{lang}</span>' if lang else ""
        return f'<pre class="codeblock">{lang_tag}<code>{e(block[2])}</code></pre>'
    return ""


def drill_html(key: str, title: str, prompt: str, hint: str, kicker: str = "Practica ahora") -> str:
    return f"""<aside class="drill" data-drill="{e(key)}">
      <p class="n">{e(kicker)}</p>
      <h3>{e(title)}</h3>
      <p>{e(prompt)}</p>
      <textarea data-drill-note rows="4" placeholder="Escribe aquí. Se borra al cerrar el navegador."></textarea>
      <p class="drill-actions"><button type="button" class="btn btn-ghost" data-hint-open aria-expanded="false">Me atoré</button></p>
      <div class="hint-body" hidden>
        <p class="n">Pista</p>
        <p>{e(hint)}</p>
      </div>
    </aside>"""


def render_lecture(w: dict) -> str:
    lookup = {title: (title, prompt, hint) for title, prompt, hint in DRILLS.get(w["id"], {}).get("lecture", [])}
    parts: list[str] = []
    current = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf, current
        parts.extend(buf)
        if current and current in lookup:
            title, prompt, hint = lookup[current]
            parts.append(drill_html(slugify(title), title, prompt, hint))
        buf = []

    for block in w["lecture"]:
        if block[0] == "h2":
            flush()
            current = block[1]
            buf.append(render_block(block))
        else:
            buf.append(render_block(block))
    flush()
    return "".join(parts)


def task_html(item: tuple, index: int, hint: str = "") -> str:
    t, b = item[0], item[1]
    help_html = ""
    if hint:
        help_html = f"""<p class="drill-actions"><button type="button" class="btn btn-ghost" data-hint-open aria-expanded="false">Me atoré</button></p>
        <div class="hint-body" hidden><p class="n">Pista</p><p>{e(hint)}</p></div>"""
    return f"""<div class="task">
      <input type="checkbox" data-task="{index}"/>
      <div class="task-body"><strong>{e(t)}</strong><p>{e(b)}</p>{help_html}</div>
    </div>"""


def mark() -> str:
    return """<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
  <rect width="32" height="32" rx="8" fill="#c8102e"/>
  <path d="M8 16c0-4 3-7 8-7s8 3 8 7-3 7-8 7" fill="none" stroke="#f4efe6" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M24 16c0 4-3 7-8 7s-8-3-8-7 3-7 8-7" fill="none" stroke="#f4efe6" stroke-width="2.2" stroke-linecap="round" opacity=".55"/>
</svg>"""


def week_label(w: dict) -> str:
    return "Bonus" if w["num"] == 13 else f"Semana {w['num']}"


def week_num(w: dict) -> str:
    return "B" if w["num"] == 13 else f"{w['num']:02d}"


def nav(active: str) -> str:
    links = [
        ("index.html", "Portada", "inicio"),
        ("temario.html", "Índice", "temario"),
        ("metodo.html", "Prólogo", "metodo"),
        ("repaso.html", "Repaso", "repaso"),
        ("proyecto.html", "Proyecto", "proyecto"),
    ]
    items = []
    for href, label, key in links:
        cls = ' class="is-active"' if key == active else ""
        items.append(f'<a href="{href}"{cls}>{e(label)}</a>')
    return f'<nav class="nav" id="nav">{"".join(items)}</nav>'


def pages_nav() -> str:
    return """
      <a href="index.html">Portada</a>
      <a href="temario.html">Índice completo</a>
      <a href="metodo.html">Prólogo</a>
      <a href="repaso.html">Repaso</a>
      <a href="proyecto.html">Proyecto</a>
      <a href="temario.html#modulos">Módulos</a>
      <a href="temario.html#herramientas">Herramientas</a>
      <a href="temario.html#biblioteca">Biblioteca</a>
      <a href="temario.html#glosario">Glosario</a>
      <a href="temario.html#recursos">Recursos</a>
    """


def index_items_html(compact: bool = False) -> str:
    rows = []
    for w in WEEKS:
        href = f"semana-{w['id']}.html"
        skills = "".join(
            f'<a class="chip" href="{href}#conferencia">{e(s)}</a>' for s in w["skills"]
        )
        shorts = ""
        if not compact:
            shorts = "".join(
                f'<a class="index-sub" href="{href}#cortos">{e(t)}</a>' for t, _ in w["shorts"]
            )
            shorts = f"""<p class="index-subs">{shorts}
      <a class="index-sub" href="{href}#pset">Problem set</a>
      <a class="index-sub" href="{href}#quiz">Quiz</a>
      <a class="index-sub" href="{href}#recursos">Recursos</a>
    </p>"""
        heads = [b[1] for b in w["lecture"] if b[0] == "h2"]
        hay = " ".join(
            [
                w["title"],
                w["goal"],
                *w["skills"],
                *[t for t, _ in w["shorts"]],
                *[t for t, _, _ in w["resources"]],
                *heads,
                *[q for q, _ in w["flash"]],
            ]
        )
        goal = "" if compact else f"<p>{e(w['goal'])}</p>"
        rows.append(
            f"""<article class="spine-item" data-index-item data-index-kind="semana" data-week-progress="{w['id']}" data-tasks="{len(w['pset_std'])}" data-hay="{e(hay.lower())}">
  <a class="spine-dot" href="{href}" aria-hidden="true"><span>{e(week_num(w))}</span></a>
  <div class="spine-body">
    <p class="n">{e(week_label(w))} · {e(w['hours'])} · <span data-pct>0%</span></p>
    <h3><a href="{href}">{e(w['title'])}</a></h3>
    {goal}
    <div class="chip-row">{skills}</div>
    {shorts}
    <div class="bar"><i></i></div>
  </div>
</article>"""
        )
    return "".join(rows)


def tool_items_html() -> str:
    parts = []
    for cat, items in TOOLS:
        href, label = TOOL_CAT.get(cat, ("temario.html#herramientas", cat))
        chips = "".join(f'<a class="chip" href="{href}">{e(t)}</a>' for t in items)
        hay = " ".join([cat, *items, label])
        parts.append(
            f"""<article class="atlas-card" data-index-item data-index-kind="herramienta" data-hay="{e(hay.lower())}">
  <p class="n">Herramienta · {e(label)}</p>
  <h3><a href="{href}">{e(cat)}</a></h3>
  <div class="chip-row">{chips}</div>
</article>"""
        )
    return "".join(parts)


def book_items_html() -> str:
    parts = []
    for title, author in BOOKS:
        hay = f"{title} {author}"
        parts.append(
            f"""<article class="atlas-card" data-index-item data-index-kind="libro" data-hay="{e(hay.lower())}">
  <p class="n">Biblioteca</p>
  <h3>{e(title)}</h3>
  <p>{e(author)}</p>
</article>"""
        )
    return "".join(parts)


def glossary_items() -> list[tuple[str, str, str, str]]:
    rows = []
    for w in WEEKS:
        for q, a in w["flash"]:
            rows.append((q, a, week_label(w), w["id"]))
    rows.sort(key=lambda x: x[0].lower())
    return rows


def glossary_items_html(compact: bool = False) -> str:
    parts = []
    last_letter = ""
    for q, a, src, wid in glossary_items():
        letter = q[:1].upper()
        if not compact and letter != last_letter:
            parts.append(f'<p class="letter" aria-hidden="true">{e(letter)}</p>')
            last_letter = letter
        parts.append(
            f"""<article class="gloss" data-index-item data-index-kind="glosario" data-hay="{e((q + " " + a).lower())}">
  <h3>{e(q)}</h3>
  <p>{e(a)}</p>
  <a class="tiny" href="semana-{wid}.html">{e(src)}</a>
</article>"""
        )
    return "".join(parts)


def resource_items_html() -> str:
    parts = []
    for w in WEEKS:
        for title, url, kind in w["resources"]:
            hay = f"{title} {kind} {w['title']}"
            parts.append(
                f"""<a class="atlas-card atlas-link" data-index-item data-index-kind="recurso" data-hay="{e(hay.lower())}" href="{e(url)}" rel="noopener" target="_blank">
  <p class="n">{e(week_label(w))} · {e(kind)}</p>
  <h3>{e(title)}</h3>
  <p>{e(w['title'])}</p>
</a>"""
            )
    return "".join(parts)


def index_panel() -> str:
    return f"""
<div class="index-overlay" id="indice" hidden>
  <div class="index-sheet" role="dialog" aria-modal="true" aria-labelledby="indice-title">
    <div class="index-masthead">
      <div>
        <p class="kicker">Documento · 12 semanas + bonus</p>
        <h2 id="indice-title">Índice del curso</h2>
      </div>
      <button class="btn btn-ghost" type="button" data-index-close>Cerrar</button>
    </div>
    <div class="index-sheet-body">
      <label class="index-search">
        <span class="sr-only">Buscar en el índice</span>
        <input type="search" data-index-q placeholder="Buscar Git, DNS, Terraform, Scrum, Prometheus…" autocomplete="off"/>
      </label>
      <div class="index-tabs" role="tablist" aria-label="Filtrar el índice">
        <button type="button" role="tab" data-index-tab="todo" class="is-on" aria-selected="true">Todo</button>
        <button type="button" role="tab" data-index-tab="semana" aria-selected="false">Semanas</button>
        <button type="button" role="tab" data-index-tab="herramienta" aria-selected="false">Herramientas</button>
        <button type="button" role="tab" data-index-tab="libro" aria-selected="false">Libros</button>
        <button type="button" role="tab" data-index-tab="glosario" aria-selected="false">Glosario</button>
        <button type="button" role="tab" data-index-tab="recurso" aria-selected="false">Recursos</button>
      </div>
      <p class="tiny index-count" data-index-count></p>
      <nav class="index-pages index-pages-mobile" aria-label="Páginas">{pages_nav()}</nav>
      <div class="index-body">
        <section data-index-section="semana">
          <h3 class="index-sec">Semanas</h3>
          <div class="spine">{index_items_html(compact=True)}</div>
        </section>
        <section data-index-section="herramienta">
          <h3 class="index-sec">Caja de herramientas</h3>
          <div class="atlas-grid">{tool_items_html()}</div>
        </section>
        <section data-index-section="libro">
          <h3 class="index-sec">Biblioteca corta</h3>
          <div class="atlas-grid">{book_items_html()}</div>
        </section>
        <section data-index-section="glosario">
          <h3 class="index-sec">Glosario</h3>
          <div class="gloss-list">{glossary_items_html(compact=True)}</div>
        </section>
        <section data-index-section="recurso">
          <h3 class="index-sec">Recursos del documento</h3>
          <div class="atlas-grid">{resource_items_html()}</div>
        </section>
      </div>
      <p class="index-empty" data-index-empty hidden>Nada coincide con esa búsqueda.</p>
    </div>
  </div>
</div>
"""


def footer() -> str:
    weeks = "".join(
        f'<a href="semana-{w["id"]}.html">{e(week_num(w))} {e(w["title"])}</a>' for w in WEEKS
    )
    return f"""
  <footer class="site-footer">
    <div class="wrap footer-grid">
      <div>
        <p class="brand-name">{e(COURSE['title'])} <span>{COURSE['year']}</span></p>
        <p>{e(COURSE['authors'])}</p>
      </div>
      <nav class="footer-nav" aria-label="Sitio">
        <a href="index.html">Portada</a>
        <a href="temario.html">Índice</a>
        <a href="temario.html#herramientas">Herramientas</a>
        <a href="temario.html#glosario">Glosario</a>
        <a href="metodo.html">Prólogo</a>
        <a href="repaso.html">Repaso</a>
        <a href="proyecto.html">Proyecto</a>
      </nav>
      <nav class="footer-weeks" aria-label="Semanas">{weeks}</nav>
    </div>
  </footer>
"""


def layout(title: str, active: str, body: str, extra_head: str = "", body_class: str = "") -> str:
    page_title = f"{title} · {COURSE['title']}" if title != COURSE["title"] else f"{COURSE['title']} {COURSE['year']}"
    body_attr = f' class="{e(body_class)}"' if body_class else ""
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
  <title>{e(page_title)}</title>
  <meta name="description" content="{e(COURSE['lede'])}"/>
  <meta name="theme-color" content="#0b0f14"/>
  <meta property="og:title" content="{e(page_title)}"/>
  <meta property="og:description" content="{e(COURSE['lede'])}"/>
  <meta property="og:type" content="website"/>
  <meta property="og:image" content="assets/og.jpg"/>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Mono:wght@400&family=Source+Sans+3:wght@400;600;700&display=swap" onload="this.onload=null;this.rel='stylesheet'"/>
  <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=IBM+Plex+Mono:wght@400&family=Source+Sans+3:wght@400;600;700&display=swap"/></noscript>
  <link rel="stylesheet" href="assets/app.css?v=4"/>
  {extra_head}
</head>
<body{body_attr}>
  <a class="skip" href="#contenido">Saltar al contenido</a>
  <header class="site-header">
    <div class="wrap">
      <a class="brand" href="index.html">{mark()}<span class="brand-name">{e(COURSE['title'])} <span>{COURSE['year']}</span></span></a>
      <div class="header-tools">
        {nav(active)}
        <button class="menu-btn" type="button" data-index-open aria-controls="indice" aria-expanded="false" aria-label="Abrir índice y buscar en el temario">
          <svg class="icon-menu" width="18" height="12" viewBox="0 0 18 12" fill="none" aria-hidden="true"><path d="M0 1h18M0 6h18M0 11h18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          <svg class="icon-search" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="4.2" stroke="currentColor" stroke-width="1.6"/><path d="M10.2 10.2L14 14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          <span class="menu-short">Menú</span>
          <span class="menu-long">Buscar temario</span>
          <kbd>/</kbd>
        </button>
        <button class="sound-btn" type="button" data-sound-toggle aria-pressed="true" aria-label="Activar o silenciar sonido">
          <svg class="icon-sound-on" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M2.5 6.2v3.6h2.2L8 13V3L4.7 6.2H2.5z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M10.2 5.4a3.2 3.2 0 010 5.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <svg class="icon-sound-off" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M2.5 6.2v3.6h2.2L8 13V3L4.7 6.2H2.5z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M10.4 6.2l3.2 3.6M13.6 6.2l-3.2 3.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  </header>
  {index_panel()}
  <main id="contenido">{body}</main>
  {footer()}
  <script src="assets/app.js?v=4" defer></script>
</body>
</html>
"""


def week_cards() -> str:
    cards = []
    for w in WEEKS:
        skills = "".join(f'<span class="chip">{e(s)}</span>' for s in w["skills"][:3])
        cards.append(
            f"""<a class="week-card" href="semana-{w['id']}.html">
  <span class="week-num">{e(week_num(w))}</span>
  <span class="n">{e(week_label(w))} · {e(w['hours'])}</span>
  <h3>{e(w['title'])}</h3>
  <p>{e(w['goal'])}</p>
  <div class="chip-row">{skills}</div>
  <div class="bar" data-week-progress="{w['id']}" data-tasks="{len(w['pset_std'])}"><i></i></div>
  <span class="tiny" data-pct>0%</span>
</a>"""
        )
    return f'<div class="week-grid">{"".join(cards)}</div>'


def home() -> str:
    return f"""
<section class="cover">
  <div class="wrap cover-wrap">
    <article class="cover-book">
      <span class="cover-spine" aria-hidden="true"></span>
      <p class="kicker">Vol. I · {e(COURSE['year'])}</p>
      <p class="cover-vol">Doce capítulos y un bonus</p>
      <h1>{e(COURSE['tagline'])}</h1>
      <p class="lede">{e(COURSE['lede'])}</p>
      <div class="actions">
        <a class="btn" href="semana-01.html">Abrir el capítulo 1</a>
        <a class="btn btn-ghost" href="temario.html">Leer el índice</a>
      </div>
      <p class="cover-meta">{e(COURSE['authors'])}</p>
    </article>
    <div class="cover-side">
      <div class="stats">
        <div class="stat"><b>12+1</b><span>capítulos</span></div>
        <div class="stat"><b>Estándar / Hacker</b><span>dos vías, un temario</span></div>
        <div class="stat"><b data-total-progress>0%</b><span>tu progreso en este navegador</span></div>
      </div>
      <p class="muted" style="margin:22px 0 10px">Antes de entrar, como en CS50: elige comodidad. No bloquea páginas; sugiere la vía del problem set.</p>
      <div class="comfort">
        <button type="button" data-comfort="standard"><strong>Menos cómodo</strong><br/><span class="tiny">Vía estándar. Pasos guiados, un concepto a la vez.</span></button>
        <button type="button" data-comfort="hacker"><strong>Más cómodo</strong><br/><span class="tiny">Vía hacker. Más filo, menos andamio.</span></button>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>El mapa del oficio</h2>
    <p class="muted">El mismo orden del roadmap original. Cada placa abre la semana completa. Pulsa <strong>Buscar temario</strong> o <kbd>/</kbd> para el índice.</p>
    {week_cards()}
  </div>
</section>
"""


def document_toc() -> str:
    items = []
    for w in WEEKS:
        chips = " · ".join(w["skills"][:4])
        items.append(
            f'<li><a href="semana-{w["id"]}.html"><b>{e(week_num(w))}</b><span><strong>{e(w["title"])}</strong> <em>{e(chips)}</em></span></a></li>'
        )
    extras = [
        ("H", "temario.html#herramientas", "Caja de herramientas", "Git, Docker, Terraform, Prometheus…"),
        ("L", "temario.html#biblioteca", "Biblioteca corta", "Handbook, Accelerate, SRE, Phoenix…"),
        ("G", "temario.html#glosario", "Glosario", "Todas las ideas de las tarjetas"),
        ("R", "temario.html#recursos", "Recursos", "Enlaces del documento original"),
        ("M", "metodo.html", "Método", "CS50 + recuerdo activo + Leitner"),
        ("P", "proyecto.html", "Proyecto final", "Un sistema pequeño que existe"),
    ]
    for num, href, title, hint in extras:
        items.append(
            f'<li><a href="{href}"><b>{num}</b><span><strong>{e(title)}</strong> <em>{e(hint)}</em></span></a></li>'
        )
    return f'<ol class="doc-toc">{"".join(items)}</ol>'


def temario() -> str:
    jump = """
    <nav class="jump" aria-label="Secciones del índice">
      <a href="#documento">Documento</a>
      <a href="#modulos">Módulos</a>
      <a href="#herramientas">Herramientas</a>
      <a href="#biblioteca">Biblioteca</a>
      <a href="#glosario">Glosario</a>
      <a href="#recursos">Todos los recursos</a>
    </nav>
    """
    tools = "".join(
        f"""<article class="panel" data-index-item data-index-kind="herramienta" data-hay="{e((cat + ' ' + ' '.join(items)).lower())}">
  <h3>{e(cat)}</h3>
  <div class="chip-row">{''.join(f'<a class="chip" href="{TOOL_CAT.get(cat, ("temario.html#herramientas",))[0]}">{e(t)}</a>' for t in items)}</div>
</article>"""
        for cat, items in TOOLS
    )
    books = book_items_html()
    gloss = glossary_items_html()
    res_blocks = []
    for w in WEEKS:
        links = "".join(
            f'<a href="{e(u)}" rel="noopener" target="_blank" data-index-item data-index-kind="recurso" data-hay="{e((t + " " + k + " " + w["title"]).lower())}">{e(t)}<small>{e(k)}</small></a>'
            for t, u, k in w["resources"]
        )
        res_blocks.append(
            f'<div class="resource-group"><h3>{e(week_label(w))}. {e(w["title"])}</h3><div class="resources">{links}</div></div>'
        )
    return f"""
<section class="page-head"><div class="wrap">
  <p class="kicker">Documento original · traducido</p>
  <h1>Índice</h1>
  <p class="lede">Toda la información del DevOps Roadmap 2026: módulos, temas, herramientas, libros, glosario y recursos. El orden es el del documento.</p>
  {jump}
  <label class="index-search page-search">
    <span class="sr-only">Filtrar el índice</span>
    <input type="search" data-index-q placeholder="Filtrar: DNS, Docker, Scrum, Prometheus…"/>
  </label>
</div></section>
<section class="section" id="documento"><div class="wrap">
  <h2>El documento, de un vistazo</h2>
  <p class="muted">Tabla de contenidos del curso. Cada fila abre el módulo o la sección.</p>
  {document_toc()}
</div></section>
<section class="section" id="modulos"><div class="wrap">
  <h2>Módulos</h2>
  <p class="muted">Cada nodo es una semana. Los chips son los temas del mapa mental original.</p>
  <div class="spine">{index_items_html()}</div>
</div></section>
<section class="section" id="herramientas"><div class="wrap">
  <h2>Caja de herramientas</h2>
  <p class="muted">El catálogo que cita el roadmap: no hace falta instalarlas todas el primer día. Cada chip abre la semana donde se enseña.</p>
  <div class="three-col">{tools}</div>
</div></section>
<section class="section" id="biblioteca"><div class="wrap">
  <h2>Biblioteca corta</h2>
  <p class="muted">Canon alrededor del oficio. No son obligatorios para completar el curso.</p>
  <div class="atlas-grid">{books}</div>
</div></section>
<section class="section" id="glosario"><div class="wrap">
  <h2>Glosario</h2>
  <p class="muted">Las mismas ideas de las tarjetas, en orden alfabético. Toca la semana para volver al contexto.</p>
  <div class="gloss-list">{gloss}</div>
</div></section>
<section class="section" id="recursos"><div class="wrap">
  <h2>Recursos del documento</h2>
  <p class="muted">Enlaces de aprendizaje que trae el roadmap, agrupados por semana.</p>
  {''.join(res_blocks)}
</div></section>
"""


def metodo() -> str:
    cards = "".join(
        f'<article class="panel"><h3>{e(t)}</h3><p>{e(b)}</p></article>' for t, b in PEDAGOGY
    )
    return f"""
<section class="page-head"><div class="wrap">
  <p class="kicker">Prólogo · pedagogía</p>
  <h1>Cómo se enseña aquí</h1>
  <p class="lede">Harvard CS50 baja el piso y conserva el rigor. La ciencia del aprendizaje añade recuerdo activo y repetición espaciada. Juntos, evitan el mural de herramientas que se olvida en una semana.</p>
</div></section>
<section class="section"><div class="wrap">
  <div class="method-grid">{cards}</div>
</div></section>
<section class="section"><div class="wrap">
  <h2>La semana tipo</h2>
  <div class="three-col">
    <article class="panel"><h3>1. Conferencia</h3><p>La idea grande, primero como caja negra, después por dentro. Lee con calma. No copies aún.</p></article>
    <article class="panel"><h3>2. Cortos</h3><p>Piezas de dos minutos. Un concepto, un gancho mental. Luego el recorrido guiado.</p></article>
    <article class="panel"><h3>3. Problem set</h3><p>La vía estándar o la hacker. Rúbrica: correctitud, diseño, estilo. El aprendizaje ocurre aquí.</p></article>
  </div>
  <p class="muted" style="margin-top:24px">Después: quiz de recuerdo, Feynman (cerrar y enseñar) y tarjetas. Lo que marques o escribas dura mientras no cierres el navegador. No hay cuentas.</p>
</div></section>
"""


def week_page(w: dict) -> str:
    d = DRILLS.get(w["id"], {})
    lecture = render_lecture(w)
    shorts = "".join(f'<article class="short"><h3>{e(t)}</h3><p>{e(b)}</p></article>' for t, b in w["shorts"])
    walk = "".join(f"<li>{e(s)}</li>" for s in w["walkthrough"])
    skills = "".join(f'<span class="chip">{e(s)}</span>' for s in w["skills"])
    heads = "".join(
        f'<a class="toc-sub" href="#{slugify(b[1])}">{e(b[1])}</a>'
        for b in w["lecture"]
        if b[0] == "h2"
    )
    std_hints = d.get("std", [])
    hack_hints = d.get("hack", [])
    std = [task_html(item, i, std_hints[i] if i < len(std_hints) else "") for i, item in enumerate(w["pset_std"])]
    offset = len(w["pset_std"])
    hack = [task_html(item, offset + i, hack_hints[i] if i < len(hack_hints) else "") for i, item in enumerate(w["pset_hack"])]

    quiz = []
    for q, opts, ans, expl in w["quiz"]:
        choices = "".join(f'<button class="choice" type="button">{e(o)}</button>' for o in opts)
        quiz.append(
            f'<article class="q-card" data-answer="{ans}"><h3>{e(q)}</h3><div class="choices">{choices}</div><p class="explain" hidden>{e(expl)}</p></article>'
        )

    cards_json = e(json.dumps([{"q": q, "a": a} for q, a in w["flash"]], ensure_ascii=False))
    res = "".join(
        f'<a href="{e(u)}" rel="noopener" target="_blank">{e(t)}<small>{e(k)}</small></a>'
        for t, u, k in w["resources"]
    )
    label = week_label(w)
    prev_n = w["num"] - 1
    next_n = w["num"] + 1
    prev = f'<a class="btn btn-ghost" href="semana-{prev_n:02d}.html">Semana anterior</a>' if prev_n >= 1 else '<a class="btn btn-ghost" href="temario.html">Índice</a>'
    nxt = f'<a class="btn" href="semana-{next_n:02d}.html">Siguiente semana</a>' if next_n <= 13 else '<a class="btn" href="proyecto.html">Proyecto final</a>'

    course_weeks = []
    for x in WEEKS:
        cls = ' class="is-active"' if x["id"] == w["id"] else ""
        course_weeks.append(
            f'<a href="semana-{x["id"]}.html"{cls}>{e(week_num(x))} {e(x["title"])}</a>'
        )
    c, design, style = w["rubric"]

    def as_drill(item, fallback_title: str) -> tuple[str, str, str]:
        if len(item) == 2:
            return fallback_title, item[0], item[1]
        return item[0], item[1], item[2]

    shorts_drill = drill_html("shorts", *as_drill(d["shorts"], "Después de los cortos")) if d.get("shorts") else ""
    walk_drill = drill_html("walk", *as_drill(d["walk"], "Después del recorrido")) if d.get("walk") else ""
    encore_drill = drill_html("encore", *d["encore"], kicker="Ejercicio extra") if d.get("encore") else ""
    return f"""
<div class="read-progress" aria-hidden="true"><i data-read-bar></i></div>
<div class="wrap week-layout" data-week="{w['id']}" data-tasks="{len(w['pset_std']) + len(w['pset_hack'])}">
  <aside class="toc">
    <p class="n">En esta semana</p>
    <a href="#resumen">Resumen</a>
    <a href="#conferencia">Conferencia</a>
    {heads}
    <a href="#cortos">Cortos</a>
    <a href="#recorrido">Recorrido</a>
    <a href="#pset">Problem set</a>
    <a href="#refuerzo">Refuerzo</a>
    <a href="#quiz">Recuerdo</a>
    <a href="#feynman">Feynman</a>
    <a href="#tarjetas">Tarjetas</a>
    <a href="#recursos">Recursos</a>
    <p class="n toc-k">Curso</p>
    {''.join(course_weeks)}
  </aside>
  <article class="sheet">
    <section class="page-head" id="resumen">
      <p class="kicker">{e(label)} · {e(w['hours'])}</p>
      <h1>{e(w['title'])}</h1>
      <p class="lede">{e(w['goal'])}</p>
      <div class="chip-row">{skills}</div>
      <div class="progress-box">
        <span class="tiny" data-week-pct>0% completado</span>
      </div>
      <div class="bar"><i data-week-bar></i></div>
      <p class="why">{e(w['why'])}</p>
      <p class="session-note">Leer, practicar, volver a leer. Lo que escribas se queda en esta pestaña hasta que cierres el navegador. No hay cuentas.</p>
    </section>

    <section id="conferencia">
      <h2>Conferencia</h2>
      <label class="tiny"><input type="checkbox" data-mark="lecture"/> Marcar conferencia como leída</label>
      <div class="lecture">{lecture}</div>
    </section>

    <section id="cortos">
      <h2>Cortos</h2>
      <p class="muted">Un concepto por tarjeta. Léelos en voz alta si puedes.</p>
      <label class="tiny"><input type="checkbox" data-mark="shorts"/> Ya repasé los cortos</label>
      <div class="shorts">{shorts}</div>
      {shorts_drill}
    </section>

    <section id="recorrido">
      <h2>Recorrido</h2>
      <p class="muted">Como el walkthrough de CS50: solo para arrancar, no para sustituir el problem set.</p>
      <ol>{walk}</ol>
      {walk_drill}
    </section>

    <section id="pset">
      <h2>Problem set</h2>
      <p class="muted">Rúbrica: <strong>correctitud</strong> — {e(c)} · <strong>diseño</strong> — {e(design)} · <strong>estilo</strong> — {e(style)}</p>
      <div class="tabs">
        <button class="tab is-on" type="button" data-tab="std">Estándar</button>
        <button class="tab" type="button" data-tab="hacker">Hacker</button>
      </div>
      <div data-pane="std">{''.join(std)}</div>
      <div data-pane="hacker" hidden>{''.join(hack)}</div>
    </section>

    <section id="refuerzo">
      <h2>Refuerzo</h2>
      <p class="muted">Un ejercicio extra, después de haber leído y practicado. Si te atas, abre la pista. No es un examen.</p>
      {encore_drill}
    </section>

    <section id="quiz">
      <h2>Recuerdo activo</h2>
      <p class="muted">Cierra las notas. Elige. El error también enseña.</p>
      <div class="quiz">{''.join(quiz)}</div>
    </section>

    <section id="feynman">
      <h2>Cerrar y enseñar</h2>
      <p class="muted">{e(w['feynman'])}</p>
      <p><button class="btn btn-ghost" type="button" data-hide-lecture>Cerrar y enseñar</button></p>
      <div class="feynman"><textarea data-feynman placeholder="Escribe la explicación como si el otro no hubiera visto jamás un servidor."></textarea></div>
    </section>

    <section id="tarjetas">
      <h2>Tarjetas espaciadas</h2>
      <p class="muted">Toca la carta para voltearla. «Otra vez» la devuelve a la caja 1. «La sé» la aleja 1, 3, 7, 14 o 30 días.</p>
      <div class="flash" data-flash data-cards="{cards_json}">
        <div class="flash-inner">
          <div class="flash-face flash-front">
            <p data-q></p>
            <p class="hint">Toca para voltear · <span data-box></span></p>
          </div>
          <div class="flash-face flash-back">
            <p data-a></p>
          </div>
        </div>
      </div>
      <div class="rate">
        <button class="btn btn-ghost" type="button" data-rate="again">Otra vez</button>
        <button class="btn" type="button" data-rate="ok">La sé</button>
      </div>
    </section>

    <section id="recursos">
      <h2>Recursos del roadmap</h2>
      <div class="resources">{res}</div>
    </section>

    <div class="week-nav">{prev}{nxt}</div>
  </article>
</div>
"""
def repaso() -> str:
    all_cards = []
    week_btns = ['<button class="chip is-on" type="button" data-deck-week="all">Todas</button>']
    for w in WEEKS:
        label = week_label(w)
        title = w["title"].removeprefix("Bonus:").strip()
        src = f"{label} · {title}"
        for i, (q, a) in enumerate(w["flash"]):
            all_cards.append({"q": q, "a": a, "src": src, "week": w["id"], "i": i})
        week_btns.append(
            f'<button class="chip" type="button" data-deck-week="{e(w["id"])}">{e(week_num(w))} {e(title)}</button>'
        )
    payload = e(json.dumps(all_cards, ensure_ascii=False))
    return f"""
<section class="page-head"><div class="wrap">
  <p class="kicker">Recuerdo activo</p>
  <h1>Repaso</h1>
  <p class="lede">Un mazo con las ideas del curso. Cada carta es una pregunta completa, con su semana. Si fallas, vuelve enseguida; si aciertas, se aleja 1, 3, 7, 14 o 30 días.</p>
</div></section>
<section class="section"><div class="wrap deck">
  <div class="deck-stats" aria-live="polite">
    <article><p class="n">Pendientes hoy</p><strong data-due-count>0</strong></article>
    <article><p class="n">Cartas en el mazo</p><strong data-total-count>0</strong></article>
    <article><p class="n">Ya alejadas</p><strong data-known-count>0</strong></article>
  </div>
  <div class="chip-row" role="group" aria-label="Qué practicar">
    <button class="chip is-on" type="button" data-deck-mode="due">Pendientes de hoy</button>
    <button class="chip" type="button" data-deck-mode="all">Mazo completo</button>
  </div>
  <div class="chip-row deck-weeks" role="group" aria-label="Filtrar por semana">
    {''.join(week_btns)}
  </div>
  <p class="tiny" data-deck-progress></p>
  <div class="flash" data-global-flash data-cards="{payload}">
    <div class="flash-inner">
      <div class="flash-face flash-front">
        <p class="tiny" data-src></p>
        <p data-q></p>
        <p class="hint">Toca para voltear · <span data-box></span></p>
      </div>
      <div class="flash-face flash-back">
        <p class="tiny" data-src></p>
        <p data-a></p>
        <p class="hint">¿La recuperaste de memoria?</p>
      </div>
    </div>
  </div>
  <div class="rate" data-deck-tools>
    <button class="btn btn-ghost" type="button" data-rate="again">Otra vez</button>
    <button class="btn" type="button" data-rate="ok">La sé</button>
  </div>
  <p class="muted deck-empty" data-deck-empty hidden>Hoy no hay cartas pendientes en este filtro. Las que ya recuerdas vuelven más tarde. Abre el mazo completo para practicar, o sigue con una semana.</p>
</div></section>
"""


def proyecto() -> str:
    return """
<section class="page-head"><div class="wrap">
  <p class="kicker">Capstone</p>
  <h1>Proyecto final</h1>
  <p class="lede">Como en CS50: al final no hay un examen de trivia. Hay un sistema que existe. Pequeño, observable, reproducible.</p>
</div></section>
<section class="section"><div class="wrap">
  <div class="two-col">
    <article class="panel">
      <h3>El encargo</h3>
      <p>Publica una aplicación mínima (una página, una API o un bot) con: repositorio Git, Dockerfile o Compose, un pipeline que prueba y construye, un proxy o plataforma que la sirva, y un tablero o log que demuestre que está viva.</p>
    </article>
    <article class="panel">
      <h3>Restricciones</h3>
      <p>Sin secretos en el repo. Infraestructura como código o al menos un script de creación/destrucción. README que un extraño pueda seguir un sábado. Rúbrica: correctitud (corre), diseño (se puede operar), estilo (se puede leer).</p>
    </article>
  </div>
  <h2 style="margin-top:36px">Ideas si te quedas en blanco</h2>
  <div class="three-col">
    <article class="panel"><h3>Bitácora de estado</h3><p>Una página que consulta tres URLs y pinta verde/rojo. Nginx + contenedor + Actions.</p></article>
    <article class="panel"><h3>Acortador interno</h3><p>API diminuta, SQLite o Redis, Compose, métricas de peticiones.</p></article>
    <article class="panel"><h3>Laboratorio Terraform</h3><p>Red + VM + inventario documentado. Destroy es parte de la demo.</p></article>
  </div>
  <p style="margin-top:28px"><a class="btn" href="semana-01.html">Volver a la semana 1</a></p>
</div></section>
"""


def favicon() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="8" fill="#0b0f14"/>
  <rect x="0" y="0" width="4" height="32" fill="#c8102e"/>
  <path d="M10 8c4.8 0 8 2.4 8 8s-3.2 8-8 8" fill="none" stroke="#f4efe6" stroke-width="3" stroke-linecap="round"/>
  <circle cx="10" cy="16" r="2.2" fill="#c8102e"/>
</svg>
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    assets = OUT / "assets"
    assets.mkdir(parents=True)
    shutil.copyfile(STATIC / "app.css", assets / "app.css")
    shutil.copyfile(STATIC / "app.js", assets / "app.js")
    write(assets / "favicon.svg", favicon())
    og_candidates = [STATIC / "og.jpg", Path("/workspace/public/og.jpg")]
    for og in og_candidates:
        if og.exists():
            shutil.copyfile(og, assets / "og.jpg")
            break
    write(OUT / ".nojekyll", "")
    write(OUT / "index.html", layout(COURSE["title"], "inicio", home(), body_class="is-cover"))
    write(OUT / "temario.html", layout("Índice", "temario", temario(), body_class="is-front"))
    write(OUT / "metodo.html", layout("Prólogo", "metodo", metodo(), body_class="is-front"))
    write(OUT / "repaso.html", layout("Repaso", "repaso", repaso(), body_class="is-front"))
    write(OUT / "proyecto.html", layout("Proyecto final", "proyecto", proyecto(), body_class="is-front"))
    for w in WEEKS:
        title = f"Semana {w['num']}: {w['title']}" if w["num"] != 13 else w["title"]
        write(OUT / f"semana-{w['id']}.html", layout(title, "temario", week_page(w), body_class="is-read"))
    print(f"Wrote {len(list(OUT.rglob('*')))} paths to {OUT}")


if __name__ == "__main__":
    main()
