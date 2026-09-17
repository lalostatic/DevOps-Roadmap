#!/usr/bin/env python3
"""Genera el sitio estático de DevOps Roadmap (GitHub Pages)."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from content import BOOKS, COURSE, PEDAGOGY, WEEKS

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "docs"
STATIC = ROOT / "static"


def e(text: str) -> str:
    return html.escape(text, quote=True)


def render_block(block: tuple) -> str:
    kind = block[0]
    if kind == "h2":
        return f"<h2>{e(block[1])}</h2>"
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
        return f"<pre><code>{e(block[2])}</code></pre>"
    return ""


def mark() -> str:
    return """<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
  <rect width="32" height="32" rx="8" fill="#c8102e"/>
  <path d="M8 16c0-4 3-7 8-7s8 3 8 7-3 7-8 7" fill="none" stroke="#f4efe6" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M24 16c0 4-3 7-8 7s-8-3-8-7 3-7 8-7" fill="none" stroke="#f4efe6" stroke-width="2.2" stroke-linecap="round" opacity=".55"/>
</svg>"""


def nav(active: str) -> str:
    links = [
        ("index.html", "Inicio", "inicio"),
        ("temario.html", "Temario", "temario"),
        ("metodo.html", "Método", "metodo"),
        ("repaso.html", "Repaso", "repaso"),
        ("proyecto.html", "Proyecto", "proyecto"),
    ]
    items = []
    for href, label, key in links:
        cls = ' class="is-active"' if key == active else ""
        items.append(f'<a href="{href}"{cls}>{e(label)}</a>')
    return f'<nav class="nav" id="nav">{"".join(items)}</nav>'


def layout(title: str, active: str, body: str, extra_head: str = "") -> str:
    page_title = f"{title} · {COURSE['title']}" if title != COURSE["title"] else f"{COURSE['title']} {COURSE['year']}"
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
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
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="assets/app.css"/>
  {extra_head}
</head>
<body>
  <a class="skip" href="#contenido">Saltar al contenido</a>
  <header class="site-header">
    <div class="wrap">
      <a class="brand" href="index.html">{mark()}<span class="brand-name">{e(COURSE['title'])} <span>{COURSE['year']}</span></span></a>
      <button class="menu-btn" type="button" aria-label="Abrir menú"><svg width="18" height="12" viewBox="0 0 18 12" fill="none" aria-hidden="true"><path d="M0 1h18M0 6h18M0 11h18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>
      {nav(active)}
    </div>
  </header>
  <main id="contenido">{body}</main>
  <footer class="site-footer">
    <div class="wrap">
      <p>{e(COURSE['authors'])} Sitio generado con Python. Compatible con GitHub Pages.</p>
      <p>Pedagogía inspirada en CS50 (Harvard): accesibilidad con rigor, conferencias, cortos, problem sets y rúbrica de correctitud, diseño y estilo.</p>
    </div>
  </footer>
  <script src="assets/app.js" defer></script>
</body>
</html>
"""


def week_cards() -> str:
    cards = []
    for w in WEEKS:
        n = f"{w['num']:02d}" if w["num"] < 13 else "B"
        label = "Bonus" if w["num"] == 13 else f"Semana {w['num']}"
        cards.append(
            f"""<a class="week-card" href="semana-{w['id']}.html">
  <span class="n">{e(label)}</span>
  <h3>{e(w['title'])}</h3>
  <p>{e(w['goal'])}</p>
  <div class="bar" data-week-progress="{w['id']}" data-tasks="{len(w['pset_std'])}"><i></i></div>
  <span class="tiny" data-pct>0%</span>
</a>"""
        )
    return f'<div class="week-grid">{"".join(cards)}</div>'


def home() -> str:
    return f"""
<section class="hero">
  <div class="wrap">
    <p class="kicker">Curso abierto · Español</p>
    <h1>{e(COURSE['tagline'])}</h1>
    <p class="lede">{e(COURSE['lede'])}</p>
    <div class="actions">
      <a class="btn" href="semana-01.html">Empezar semana 1</a>
      <a class="btn btn-ghost" href="metodo.html">Cómo se enseña</a>
    </div>
    <div class="stats">
      <div class="stat"><b>12+1</b><span>semanas y un bonus</span></div>
      <div class="stat"><b>Estándar / Hacker</b><span>dos vías, un temario</span></div>
      <div class="stat"><b data-total-progress>0%</b><span>tu progreso en este navegador</span></div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>El año, semana a semana</h2>
    <p class="muted">No es un mural de logos. Es un curso: cada módulo tiene conferencia, cortos, recorrido, problem set, recuerdo activo y tarjetas espaciadas.</p>
    {week_cards()}
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>Antes de entrar</h2>
    <p class="muted">Como en CS50, elige tu comodidad. No bloquea contenido: solo sugiere la vía del problem set.</p>
    <div class="comfort" style="margin-top:18px;max-width:720px">
      <button type="button" data-comfort="standard"><strong>Menos cómodo</strong><br/><span class="tiny">Vía estándar. Pasos guiados, un concepto a la vez.</span></button>
      <button type="button" data-comfort="hacker"><strong>Más cómodo</strong><br/><span class="tiny">Vía hacker. Más filo, menos andamio.</span></button>
    </div>
  </div>
</section>
"""


def temario() -> str:
    rows = []
    for w in WEEKS:
        skills = " · ".join(w["skills"])
        label = "Bonus" if w["num"] == 13 else f"Semana {w['num']:02d}"
        rows.append(
            f"""<a class="week-card" href="semana-{w['id']}.html">
  <span class="n">{e(label)} · {e(w['hours'])}</span>
  <h3>{e(w['title'])}</h3>
  <p>{e(skills)}</p>
</a>"""
        )
    books = "".join(f"<li><strong>{e(t)}</strong> — {e(a)}</li>" for t, a in BOOKS)
    return f"""
<section class="page-head"><div class="wrap">
  <p class="kicker">Syllabus</p>
  <h1>Temario</h1>
  <p class="lede">Doce oficios y un bonus de seguridad. El orden importa: Git y un lenguaje antes de orquestar el mundo.</p>
</div></section>
<section class="section"><div class="wrap">{''.join(rows)}</div></section>
<section class="section"><div class="wrap">
  <h2>Biblioteca corta</h2>
  <p class="muted">No son obligatorios. Sí son el canon que el roadmap original recomienda alrededor del oficio.</p>
  <ul>{books}</ul>
</div></section>
"""


def metodo() -> str:
    cards = "".join(
        f'<article class="panel"><h3>{e(t)}</h3><p>{e(b)}</p></article>' for t, b in PEDAGOGY
    )
    return f"""
<section class="page-head"><div class="wrap">
  <p class="kicker">Pedagogía</p>
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
  <p class="muted" style="margin-top:24px">Después: quiz de recuerdo, Feynman (cerrar y enseñar) y tarjetas Leitner (1-3-7-14-30 días). El progreso vive en este navegador, sin cuentas.</p>
</div></section>
"""


def week_page(w: dict) -> str:
    lecture = "".join(render_block(b) for b in w["lecture"])
    shorts = "".join(f'<article class="short"><h3>{e(t)}</h3><p>{e(b)}</p></article>' for t, b in w["shorts"])
    walk = "".join(f"<li>{e(s)}</li>" for s in w["walkthrough"])
    skills = "".join(f'<span class="chip">{e(s)}</span>' for s in w["skills"])

    def tasks(items, prefix):
        out = []
        for i, (t, b) in enumerate(items):
            out.append(
                f'<label class="task"><input type="checkbox" data-task="{prefix}{i}"/><span><strong>{e(t)}</strong><p>{e(b)}</p></span></label>'
            )
        return "".join(out)

    # unique task indexes: standard 0..n-1, hacker continues
    std = []
    for i, (t, b) in enumerate(w["pset_std"]):
        std.append(
            f'<label class="task"><input type="checkbox" data-task="{i}"/><span><strong>{e(t)}</strong><p>{e(b)}</p></span></label>'
        )
    hack = []
    offset = len(w["pset_std"])
    for i, (t, b) in enumerate(w["pset_hack"]):
        hack.append(
            f'<label class="task"><input type="checkbox" data-task="{offset + i}"/><span><strong>{e(t)}</strong><p>{e(b)}</p></span></label>'
        )

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
    label = "Bonus" if w["num"] == 13 else f"Semana {w['num']}"
    prev_n = w["num"] - 1
    next_n = w["num"] + 1
    prev = ""
    nxt = ""
    if prev_n >= 1:
        pid = f"{prev_n:02d}"
        prev = f'<a class="btn btn-ghost" href="semana-{pid}.html">Semana anterior</a>'
    if next_n <= 13:
        nid = f"{next_n:02d}"
        nxt = f'<a class="btn" href="semana-{nid}.html">Siguiente</a>'
    else:
        nxt = '<a class="btn" href="proyecto.html">Proyecto final</a>'

    c, d, s = w["rubric"]
    return f"""
<div class="wrap week-layout" data-week="{w['id']}" data-tasks="{len(w['pset_std']) + len(w['pset_hack'])}">
  <aside class="toc">
    <a href="#resumen">Resumen</a>
    <a href="#conferencia">Conferencia</a>
    <a href="#cortos">Cortos</a>
    <a href="#recorrido">Recorrido</a>
    <a href="#pset">Problem set</a>
    <a href="#quiz">Recuerdo</a>
    <a href="#feynman">Feynman</a>
    <a href="#tarjetas">Tarjetas</a>
    <a href="#recursos">Recursos</a>
  </aside>
  <div>
    <section class="page-head" id="resumen">
      <p class="kicker">{e(label)} · {e(w['hours'])}</p>
      <h1>{e(w['title'])}</h1>
      <p class="lede">{e(w['goal'])}</p>
      <div class="chip-row">{skills}</div>
      <div class="progress-box">
        <span class="tiny" data-week-pct>0% completado</span>
      </div>
      <div class="bar"><i data-week-bar></i></div>
      <p style="margin-top:18px">{e(w['why'])}</p>
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
      <div class="shorts" style="margin-top:12px">{shorts}</div>
    </section>

    <section id="recorrido">
      <h2>Recorrido</h2>
      <p class="muted">Como el walkthrough de CS50: solo para arrancar, no para sustituir el problem set.</p>
      <ol>{walk}</ol>
    </section>

    <section id="pset">
      <h2>Problem set</h2>
      <p class="muted">Rúbrica: <strong>correctitud</strong> — {e(c)} · <strong>diseño</strong> — {e(d)} · <strong>estilo</strong> — {e(s)}</p>
      <div class="tabs">
        <button class="tab is-on" type="button" data-tab="std">Estándar</button>
        <button class="tab" type="button" data-tab="hacker">Hacker</button>
      </div>
      <div data-pane="std">{''.join(std)}</div>
      <div data-pane="hacker" hidden>{''.join(hack)}</div>
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
      <p class="muted">Toca la carta para ver la respuesta. «Otra vez» la devuelve a la caja 1. «La sé» la aleja 1, 3, 7, 14 o 30 días.</p>
      <div class="flash" data-flash data-cards="{cards_json}">
        <div>
          <p data-q></p>
          <p data-a hidden></p>
          <p class="hint">Toca para revelar · <span data-box></span></p>
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
  </div>
</div>
"""


def repaso() -> str:
    all_cards = []
    for w in WEEKS:
        src = f"Semana {w['num']}: {w['title']}" if w["num"] != 13 else f"Bonus: {w['title']}"
        for q, a in w["flash"]:
            all_cards.append({"q": q, "a": a, "src": src})
    payload = e(json.dumps(all_cards, ensure_ascii=False))
    return f"""
<section class="page-head"><div class="wrap">
  <p class="kicker">Leitner</p>
  <h1>Repaso espaciado</h1>
  <p class="lede">Todas las tarjetas del curso en un mazo. Recuerdo activo, no relectura. El algoritmo simple: fallar acerca; acertar aleja.</p>
</div></section>
<section class="section"><div class="wrap" style="max-width:720px">
  <div class="flash" data-global-flash data-cards="{payload}">
    <div>
      <p class="tiny" data-src></p>
      <p data-q></p>
      <p data-a hidden></p>
      <p class="hint">Toca para revelar</p>
    </div>
  </div>
  <p style="margin-top:16px"><button class="btn" type="button" data-next-card>Siguiente carta</button></p>
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
    write(OUT / "index.html", layout(COURSE["title"], "inicio", home()))
    write(OUT / "temario.html", layout("Temario", "temario", temario()))
    write(OUT / "metodo.html", layout("Método", "metodo", metodo()))
    write(OUT / "repaso.html", layout("Repaso", "repaso", repaso()))
    write(OUT / "proyecto.html", layout("Proyecto final", "proyecto", proyecto()))
    for w in WEEKS:
        title = f"Semana {w['num']}: {w['title']}" if w["num"] != 13 else w["title"]
        write(OUT / f"semana-{w['id']}.html", layout(title, "temario", week_page(w)))
    print(f"Wrote {len(list(OUT.rglob('*')))} paths to {OUT}")


if __name__ == "__main__":
    main()
