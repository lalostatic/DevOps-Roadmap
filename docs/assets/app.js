const STORE_KEY = "devops-roadmap-2026";
const SOUND_KEY = STORE_KEY + "-sound";

const defaultState = () => ({
  comfort: null,
  weeks: {},
  cards: {},
  feynman: {},
});

function loadState() {
  try {
    return { ...defaultState(), ...JSON.parse(localStorage.getItem(STORE_KEY) || "{}") };
  } catch {
    return defaultState();
  }
}

function saveState(state) {
  localStorage.setItem(STORE_KEY, JSON.stringify(state));
  window.dispatchEvent(new Event("progress-change"));
}

const Sfx = {
  enabled: localStorage.getItem(SOUND_KEY) !== "off",
  ctx: null,
  noise: null,
  lastTap: 0,
  ensure() {
    if (!this.enabled) return null;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    if (!this.ctx) this.ctx = new AC();
    if (this.ctx.state === "suspended") this.ctx.resume();
    if (!this.noise && this.ctx) {
      const n = Math.floor(this.ctx.sampleRate * 0.5);
      const buf = this.ctx.createBuffer(1, n, this.ctx.sampleRate);
      const d = buf.getChannelData(0);
      let last = 0;
      for (let i = 0; i < n; i++) {
        last = last * 0.92 + (Math.random() * 2 - 1) * 0.08;
        d[i] = last + (Math.random() * 2 - 1) * 0.18;
      }
      this.noise = buf;
    }
    return this.ctx;
  },
  master(ctx, t, dur, peak) {
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    g.connect(ctx.destination);
    return g;
  },
  rustle(ctx, opts) {
    const t = ctx.currentTime;
    const dur = opts.dur || 0.28;
    const src = ctx.createBufferSource();
    src.buffer = this.noise;
    src.loop = true;
    const bp = ctx.createBiquadFilter();
    bp.type = "bandpass";
    bp.frequency.setValueAtTime(opts.from || 1900, t);
    bp.frequency.exponentialRampToValueAtTime(opts.to || 720, t + dur);
    bp.Q.value = opts.q || 0.75;
    const hp = ctx.createBiquadFilter();
    hp.type = "highpass";
    hp.frequency.value = 380;
    const g = this.master(ctx, t, dur, opts.peak || 0.16);
    src.connect(hp);
    hp.connect(bp);
    bp.connect(g);
    src.start(t);
    src.stop(t + dur + 0.02);
  },
  tone(ctx, freq, type, start, dur, peak) {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(freq, start);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(peak, start + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    o.connect(g);
    g.connect(ctx.destination);
    o.start(start);
    o.stop(start + dur + 0.02);
  },
  play(name, extra) {
    if (!this.enabled) return;
    const ctx = this.ensure();
    if (!ctx) return;
    const t = ctx.currentTime;
    if (name === "page") {
      this.rustle(ctx, extra < 0
        ? { from: 1100, to: 1600, dur: 0.3, peak: 0.15, q: 0.65 }
        : { from: 2100, to: 680, dur: 0.32, peak: 0.17, q: 0.7 });
      this.tone(ctx, extra < 0 ? 210 : 240, "triangle", t, 0.05, 0.03);
    } else if (name === "flip") {
      this.rustle(ctx, { from: 2800, to: 900, dur: 0.18, peak: 0.14, q: 1.1 });
    } else if (name === "select") {
      const now = performance.now();
      if (now - this.lastTap < 70) return;
      this.lastTap = now;
      this.tone(ctx, 1480, "sine", t, 0.04, 0.05);
      this.tone(ctx, 320, "triangle", t, 0.06, 0.028);
    } else if (name === "ok") {
      this.tone(ctx, 523.25, "triangle", t, 0.12, 0.07);
      this.tone(ctx, 659.25, "triangle", t + 0.09, 0.18, 0.06);
    } else if (name === "bad") {
      this.tone(ctx, 196, "triangle", t, 0.16, 0.07);
      this.tone(ctx, 185, "sine", t + 0.02, 0.18, 0.04);
    } else if (name === "open") {
      this.rustle(ctx, { from: 400, to: 1400, dur: 0.22, peak: 0.1, q: 0.5 });
    } else if (name === "close") {
      this.rustle(ctx, { from: 1400, to: 360, dur: 0.18, peak: 0.09, q: 0.5 });
    }
  },
  setEnabled(on) {
    this.enabled = on;
    localStorage.setItem(SOUND_KEY, on ? "on" : "off");
    document.querySelectorAll("[data-sound-toggle]").forEach((b) => {
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.classList.toggle("is-muted", !on);
    });
    if (on) this.play("select");
  },
};

function bindSound() {
  document.querySelectorAll("[data-sound-toggle]").forEach((btn) => {
    btn.setAttribute("aria-pressed", Sfx.enabled ? "true" : "false");
    btn.classList.toggle("is-muted", !Sfx.enabled);
    btn.addEventListener("click", () => Sfx.setEnabled(!Sfx.enabled));
  });
  const unlock = () => Sfx.ensure();
  document.addEventListener("pointerdown", unlock, { once: true });
  document.addEventListener("keydown", unlock, { once: true });
}

function pageOrder() {
  return [
    "index.html",
    "temario.html",
    "metodo.html",
    ...Array.from({ length: 13 }, (_, i) => `semana-${String(i + 1).padStart(2, "0")}.html`),
    "repaso.html",
    "proyecto.html",
  ];
}

function navDirFor(href) {
  const cur = (location.pathname.split("/").pop() || "index.html").split("#")[0];
  const dest = (href || "").split("/").pop().split("#")[0];
  const order = pageOrder();
  const a = order.indexOf(cur);
  const b = order.indexOf(dest);
  if (a >= 0 && b >= 0 && b < a) return -1;
  return 1;
}

function goTo(href, dir) {
  if (goTo.busy) return;
  goTo.busy = true;
  const d = dir ?? navDirFor(href);
  Sfx.play("page", d);
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    location.href = href;
    return;
  }
  document.documentElement.classList.remove("is-leaving", "is-leaving-back");
  document.documentElement.classList.add(d < 0 ? "is-leaving-back" : "is-leaving");
  window.setTimeout(() => {
    location.href = href;
  }, 220);
}

function bindPageTransitions() {
  document.documentElement.classList.add("is-entered");
  window.addEventListener("pageshow", () => {
    document.documentElement.classList.remove("is-leaving", "is-leaving-back");
  });
  document.addEventListener("click", (ev) => {
    if (ev.defaultPrevented) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button) return;
    const a = ev.target.closest("a[href]");
    if (!a) return;
    const href = a.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:")) return;
    if (a.target === "_blank" || a.hasAttribute("download")) return;
    if (/^https?:/i.test(href) && !href.includes(location.host)) return;
    const dest = href.split("#")[0];
    const here = location.pathname.split("/").pop() || "index.html";
    if (dest && dest !== here) {
      ev.preventDefault();
      goTo(href);
    }
  });
}

function weekState(id) {
  const s = loadState();
  if (!s.weeks[id]) {
    s.weeks[id] = { lecture: false, shorts: false, pset: [], quiz: 0, quizDone: false };
    saveState(s);
  }
  return s;
}

function percentFor(id, meta) {
  const s = loadState();
  const w = s.weeks[id] || {};
  let score = 0;
  if (w.lecture) score += 25;
  if (w.shorts) score += 15;
  if (w.quizDone) score += 25;
  const tasks = meta?.tasks || 4;
  const done = (w.pset || []).filter(Boolean).length;
  score += Math.round((done / tasks) * 35);
  return Math.min(100, score);
}

function isTypingTarget(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || el.isContentEditable;
}

function applyIndexFilter(root) {
  const input = root.querySelector("[data-index-q]");
  const q = (input?.value || "").trim().toLowerCase();
  const tabBtn = root.querySelector("[data-index-tab].is-on");
  const tab = tabBtn?.getAttribute("data-index-tab") || "todo";
  let n = 0;
  root.querySelectorAll("[data-index-item]").forEach((el) => {
    const hay = (el.getAttribute("data-hay") || el.textContent).toLowerCase();
    const kind = el.getAttribute("data-index-kind") || "";
    const matchQ = !q || hay.includes(q);
    const matchTab = tab === "todo" || !kind || kind === tab;
    const show = matchQ && matchTab;
    el.hidden = !show;
    if (show) n += 1;
  });
  root.querySelectorAll("[data-index-section]").forEach((sec) => {
    const kind = sec.getAttribute("data-index-section");
    const any = [...sec.querySelectorAll("[data-index-item]")].some((el) => !el.hidden);
    const matchTab = tab === "todo" || kind === tab;
    sec.hidden = !(any && matchTab);
  });
  const empty = root.querySelector("[data-index-empty]");
  if (empty) empty.hidden = n > 0;
  const count = root.querySelector("[data-index-count]");
  if (count) {
    count.textContent = q ? (n ? n + " coincidencias" : "") : "";
  }
}

function bindIndex() {
  const overlay = document.getElementById("indice");
  const openBtn = document.querySelector("[data-index-open]");
  const close = () => {
    if (!overlay) return;
    if (!overlay.hidden) Sfx.play("close");
    overlay.hidden = true;
    document.body.style.overflow = "";
    if (openBtn) openBtn.setAttribute("aria-expanded", "false");
  };
  const open = () => {
    if (!overlay) return;
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    if (openBtn) openBtn.setAttribute("aria-expanded", "true");
    Sfx.play("open");
    const q = overlay.querySelector("[data-index-q]");
    q?.focus({ preventScroll: true });
    applyIndexFilter(overlay);
  };
  openBtn?.addEventListener("click", () => {
    if (!overlay) return;
    if (overlay.hidden) open();
    else close();
  });
  overlay?.querySelectorAll("[data-index-close]").forEach((b) => b.addEventListener("click", close));
  overlay?.addEventListener("click", (ev) => {
    if (ev.target === overlay) close();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && overlay && !overlay.hidden) {
      close();
      return;
    }
    if (isTypingTarget(ev.target)) return;
    if (ev.key === "/" || ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "k")) {
      ev.preventDefault();
      open();
    }
  });

  document.querySelectorAll(".index-overlay, main").forEach((root) => {
    root.querySelectorAll("[data-index-q]").forEach((input) => {
      input.addEventListener("input", () => applyIndexFilter(root));
    });
    root.querySelectorAll("[data-index-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        Sfx.play("select");
        root.querySelectorAll("[data-index-tab]").forEach((t) => {
          const on = t === btn;
          t.classList.toggle("is-on", on);
          t.setAttribute("aria-selected", on ? "true" : "false");
        });
        applyIndexFilter(root);
      });
    });
    if (root.querySelector("[data-index-q], [data-index-tab]")) applyIndexFilter(root);
  });
}

function setNav() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === here || (here === "" && href === "index.html")) a.classList.add("is-active");
  });
  bindIndex();
}

function paintHomeProgress() {
  document.querySelectorAll("[data-week-progress]").forEach((el) => {
    const id = el.getAttribute("data-week-progress");
    const tasks = Number(el.getAttribute("data-tasks") || 4);
    const p = percentFor(id, { tasks });
    const bar = el.querySelector("i");
    if (bar) bar.style.width = p + "%";
    const label = el.querySelector("[data-pct]");
    if (label) label.textContent = p + "%";
  });
  const total = document.querySelector("[data-total-progress]");
  if (total) {
    const cards = [...document.querySelectorAll("[data-week-progress]")];
    const seen = new Set();
    const vals = [];
    cards.forEach((el) => {
      const id = el.getAttribute("data-week-progress");
      if (!id || seen.has(id)) return;
      seen.add(id);
      vals.push(percentFor(id, { tasks: Number(el.getAttribute("data-tasks") || 4) }));
    });
    const avg = vals.length ? Math.round(vals.reduce((n, v) => n + v, 0) / vals.length) : 0;
    total.textContent = avg + "%";
  }
}

function bindComfort() {
  const s = loadState();
  document.querySelectorAll("[data-comfort]").forEach((btn) => {
    if (s.comfort && btn.getAttribute("data-comfort") === s.comfort) btn.classList.add("is-on");
    btn.addEventListener("click", () => {
      const next = loadState();
      next.comfort = btn.getAttribute("data-comfort");
      saveState(next);
      Sfx.play("select");
      document.querySelectorAll("[data-comfort]").forEach((b) => b.classList.toggle("is-on", b === btn));
    });
  });
}

function bindWeek() {
  const root = document.querySelector("[data-week]");
  if (!root) return;
  const id = root.getAttribute("data-week");
  const s = weekState(id);
  const w = s.weeks[id];

  const lecture = document.querySelector("[data-mark=lecture]");
  const shorts = document.querySelector("[data-mark=shorts]");
  if (lecture) {
    lecture.checked = !!w.lecture;
    lecture.addEventListener("change", () => {
      const st = loadState();
      st.weeks[id] = st.weeks[id] || {};
      st.weeks[id].lecture = lecture.checked;
      saveState(st);
      paintWeekBar(id);
    });
  }
  if (shorts) {
    shorts.checked = !!w.shorts;
    shorts.addEventListener("change", () => {
      const st = loadState();
      st.weeks[id] = st.weeks[id] || {};
      st.weeks[id].shorts = shorts.checked;
      saveState(st);
      paintWeekBar(id);
    });
  }

  document.querySelectorAll("[data-task]").forEach((box) => {
    const i = Number(box.getAttribute("data-task"));
    box.checked = !!(w.pset || [])[i];
    box.addEventListener("change", () => {
      const st = loadState();
      st.weeks[id] = st.weeks[id] || { pset: [] };
      st.weeks[id].pset = st.weeks[id].pset || [];
      st.weeks[id].pset[i] = box.checked;
      saveState(st);
      paintWeekBar(id);
    });
  });

  document.querySelectorAll("[data-tab]").forEach((tab) => {
    tab.addEventListener("click", () => {
      const name = tab.getAttribute("data-tab");
      document.querySelectorAll("[data-tab]").forEach((t) => t.classList.toggle("is-on", t === tab));
      document.querySelectorAll("[data-pane]").forEach((p) => {
        p.hidden = p.getAttribute("data-pane") !== name;
      });
    });
  });

  const comfort = loadState().comfort;
  if (comfort === "hacker") {
    const hacker = document.querySelector('[data-tab="hacker"]');
    if (hacker) hacker.click();
  }

  bindQuiz(id);
  bindFeynman(id);
  bindFlash(id);
  paintWeekBar(id);
}

function paintWeekBar(id) {
  const el = document.querySelector("[data-week-bar]");
  if (!el) return;
  const tasks = document.querySelectorAll("[data-task]").length || 4;
  const p = percentFor(id, { tasks });
  el.style.width = p + "%";
  const label = document.querySelector("[data-week-pct]");
  if (label) label.textContent = p + "% completado";
}

function bindQuiz(id) {
  document.querySelectorAll(".q-card").forEach((card, qi) => {
    const answer = Number(card.getAttribute("data-answer"));
    card.querySelectorAll(".choice").forEach((btn, i) => {
      btn.addEventListener("click", () => {
        if (card.dataset.locked) return;
        card.dataset.locked = "1";
        card.querySelectorAll(".choice").forEach((c, j) => {
          if (j === answer) c.classList.add("is-ok");
          if (j === i && i !== answer) c.classList.add("is-bad");
        });
        const explain = card.querySelector(".explain");
        if (explain) explain.hidden = false;
        const st = loadState();
        st.weeks[id] = st.weeks[id] || {};
        st.weeks[id].quiz = (st.weeks[id].quiz || 0) + (i === answer ? 1 : 0);
        const total = document.querySelectorAll(".q-card").length;
        if (qi === total - 1) st.weeks[id].quizDone = true;
        saveState(st);
        paintWeekBar(id);
        Sfx.play(i === answer ? "ok" : "bad");
      });
    });
  });
}

function bindFeynman(id) {
  const area = document.querySelector("[data-feynman]");
  if (!area) return;
  const st = loadState();
  area.value = st.feynman[id] || "";
  area.addEventListener("input", () => {
    const next = loadState();
    next.feynman[id] = area.value;
    saveState(next);
  });
  const hide = document.querySelector("[data-hide-lecture]");
  if (hide) {
    hide.addEventListener("click", () => {
      const lecture = document.querySelector("#conferencia .lecture");
      if (!lecture) return;
      lecture.hidden = !lecture.hidden;
      hide.textContent = lecture.hidden ? "Mostrar conferencia" : "Cerrar y enseñar";
    });
  }
}

function daysFromBox(box) {
  return [1, 3, 7, 14, 30][Math.max(0, Math.min(4, box - 1))] || 1;
}

function bindFlash(weekId) {
  const stage = document.querySelector("[data-flash]");
  if (!stage) return;
  const cards = JSON.parse(stage.getAttribute("data-cards") || "[]");
  if (!cards.length) return;
  const st = loadState();
  st.cards[weekId] = st.cards[weekId] || {};
  cards.forEach((_, i) => {
    if (!st.cards[weekId][i]) st.cards[weekId][i] = { box: 1, next: Date.now() };
  });
  saveState(st);

  let i = 0;

  function dueIndex() {
    const now = Date.now();
    const map = loadState().cards[weekId];
    const due = cards.map((c, idx) => idx).filter((idx) => (map[idx]?.next || 0) <= now);
    return due.length ? due[0] : 0;
  }

  function render() {
    i = dueIndex();
    stage.classList.remove("is-flipped");
    const card = cards[i];
    stage.querySelector("[data-q]").textContent = card.q;
    stage.querySelector("[data-a]").textContent = card.a;
    const meta = loadState().cards[weekId][i];
    const box = stage.querySelector("[data-box]");
    if (box) box.textContent = "Caja " + meta.box;
  }

  stage.addEventListener("click", () => {
    stage.classList.toggle("is-flipped");
    Sfx.play("flip");
  });

  document.querySelectorAll("[data-rate]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const ok = btn.getAttribute("data-rate") === "ok";
      const next = loadState();
      const rec = next.cards[weekId][i];
      rec.box = ok ? Math.min(5, (rec.box || 1) + 1) : 1;
      rec.next = Date.now() + daysFromBox(rec.box) * 86400000;
      saveState(next);
      render();
    });
  });
  render();
}

function bindGlobalFlash() {
  const stage = document.querySelector("[data-global-flash]");
  if (!stage) return;
  const cards = JSON.parse(stage.getAttribute("data-cards") || "[]");
  if (!cards.length) return;
  let i = 0;
  function render() {
    stage.classList.remove("is-flipped");
    const card = cards[i % cards.length];
    stage.querySelector("[data-q]").textContent = card.q;
    stage.querySelector("[data-a]").textContent = card.a;
    const src = stage.querySelector("[data-src]");
    if (src) src.textContent = card.src || "";
  }
  stage.addEventListener("click", () => {
    stage.classList.toggle("is-flipped");
    Sfx.play("flip");
  });
  document.querySelector("[data-next-card]")?.addEventListener("click", (e) => {
    e.stopPropagation();
    i += 1;
    render();
  });
  render();
}

function bindBook() {
  const book = document.querySelector("[data-book]");
  if (!book) return;
  const folios = [...book.querySelectorAll("[data-folio]")];
  const keys = folios.map((f) => f.getAttribute("data-folio"));
  let i = 0;
  let primed = false;
  let leavingTimer = 0;

  function paintChrome() {
    const key = keys[i];
    book.querySelectorAll("[data-folio-go]").forEach((b) => {
      b.classList.toggle("is-active", b.getAttribute("data-folio-go") === key);
    });
    const running = book.querySelector("[data-running]");
    const title = folios[i].getAttribute("data-folio-title") || key;
    if (running) running.textContent = title;
    const counter = book.querySelector("[data-folio-n]");
    if (counter) counter.textContent = i + 1 + " / " + folios.length;
    const prevBtn = book.querySelector("[data-folio-prev]");
    if (prevBtn) {
      prevBtn.textContent = i === 0 ? book.getAttribute("data-prev-label") || "Anterior" : "Anterior";
    }
    book.querySelectorAll("[data-folio-next]").forEach((b) => {
      if (b.classList.contains("page-turn")) return;
      b.textContent = i === folios.length - 1 ? book.getAttribute("data-next-label") || "Siguiente" : "Siguiente";
    });
  }

  function show(next, dir) {
    if (next < 0) {
      const href = book.getAttribute("data-prev-chapter");
      if (href) goTo(href, -1);
      return;
    }
    if (next >= folios.length) {
      const href = book.getAttribute("data-next-chapter");
      if (href) goTo(href, 1);
      return;
    }
    if (next === i && primed) return;
    const from = folios[i];
    const to = folios[next];
    i = next;
    if (primed) {
      Sfx.play("page", dir);
      book.querySelector(".book-paper")?.classList.remove("is-turning");
      void book.querySelector(".book-paper")?.offsetWidth;
      book.querySelector(".book-paper")?.classList.add("is-turning");
    }
    window.clearTimeout(leavingTimer);
    folios.forEach((f) => {
      if (f !== to && f !== from) {
        f.hidden = true;
        f.classList.remove("is-on", "is-leaving", "from-next", "from-prev");
      }
    });
    to.hidden = false;
    to.classList.remove("is-leaving");
    if (primed && from && from !== to) {
      from.classList.remove("is-on");
      from.classList.add("is-leaving");
      to.classList.add("is-on", dir > 0 ? "from-next" : "from-prev");
      leavingTimer = window.setTimeout(() => {
        from.hidden = true;
        from.classList.remove("is-leaving", "from-next", "from-prev");
      }, 360);
    } else {
      to.classList.add("is-on");
      if (from && from !== to) {
        from.hidden = true;
        from.classList.remove("is-on");
      }
    }
    primed = true;
    paintChrome();
    const hash = keys[i] === "portada" ? "" : "#" + keys[i];
    const file = location.pathname.split("/").pop() || "index.html";
    history.replaceState(null, "", file + hash);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const hash = (location.hash || "").replace("#", "");
  const start = keys.indexOf(hash);
  show(start >= 0 ? start : 0, 1);

  book.querySelector("[data-folio-prev]")?.addEventListener("click", () => show(i - 1, -1));
  book.querySelectorAll("[data-folio-next]").forEach((b) => {
    b.addEventListener("click", () => show(i + 1, 1));
  });
  book.querySelectorAll("[data-folio-go]").forEach((b) => {
    b.addEventListener("click", () => {
      const idx = keys.indexOf(b.getAttribute("data-folio-go"));
      if (idx >= 0) show(idx, idx > i ? 1 : -1);
    });
  });

  document.addEventListener("keydown", (ev) => {
    if (isTypingTarget(ev.target)) return;
    const overlay = document.getElementById("indice");
    if (overlay && !overlay.hidden) return;
    if (ev.key === "ArrowRight") {
      ev.preventDefault();
      show(i + 1, 1);
    }
    if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      show(i - 1, -1);
    }
  });

  let x0 = null;
  book.addEventListener("touchstart", (ev) => {
    x0 = ev.changedTouches[0].clientX;
  }, { passive: true });
  book.addEventListener("touchend", (ev) => {
    if (x0 == null) return;
    const dx = ev.changedTouches[0].clientX - x0;
    x0 = null;
    if (Math.abs(dx) < 56) return;
    if (dx < 0) show(i + 1, 1);
    else show(i - 1, -1);
  });

  window.addEventListener("hashchange", () => {
    const h = (location.hash || "").replace("#", "") || "portada";
    const idx = keys.indexOf(h);
    if (idx >= 0) show(idx, idx > i ? 1 : -1);
  });
}

function bindSelectFx() {
  const sel = ".week-card, .chip, .choice, .atlas-card, .spine-body, .doc-toc a, .btn, .tab, .menu-btn, .folio-nav button, .comfort button, .nav a";
  document.addEventListener("pointerdown", (ev) => {
    const el = ev.target.closest(sel);
    if (!el) return;
    el.classList.add("is-pressed");
    if (el.matches("a[href]") && el.getAttribute("href") && !el.getAttribute("href").startsWith("#")) return;
    if (el.matches("[data-folio-next], [data-folio-prev], [data-folio-go], [data-sound-toggle], [data-index-open], [data-index-close], .choice, .flash, [data-flash], [data-global-flash]")) return;
    Sfx.play("select");
  });
  const clear = () => document.querySelectorAll(".is-pressed").forEach((el) => el.classList.remove("is-pressed"));
  document.addEventListener("pointerup", clear);
  document.addEventListener("pointercancel", clear);
  document.addEventListener("pointerleave", (ev) => {
    if (ev.target === document.documentElement) clear();
  });
}

setNav();
paintHomeProgress();
bindComfort();
bindWeek();
bindBook();
bindGlobalFlash();
bindSelectFx();
bindSound();
bindPageTransitions();

