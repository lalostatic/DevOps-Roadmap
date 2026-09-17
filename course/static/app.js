const STORE_KEY = "devops-roadmap-2026";

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
    overlay.hidden = true;
    document.body.style.overflow = "";
    if (openBtn) openBtn.setAttribute("aria-expanded", "false");
  };
  const open = () => {
    if (!overlay) return;
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    if (openBtn) openBtn.setAttribute("aria-expanded", "true");
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
      if (href) location.href = href;
      return;
    }
    if (next >= folios.length) {
      const href = book.getAttribute("data-next-chapter");
      if (href) location.href = href;
      return;
    }
    if (next === i && primed) return;
    const from = folios[i];
    const to = folios[next];
    i = next;
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
      }, 280);
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
}

function bindSelectFx() {
  const sel = ".week-card, .chip, .choice, .atlas-card, .spine-body, .doc-toc a, .btn, .tab, .menu-btn, .folio-nav button, .comfort button, .nav a";
  document.addEventListener("pointerdown", (ev) => {
    const el = ev.target.closest(sel);
    if (!el) return;
    el.classList.add("is-pressed");
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

