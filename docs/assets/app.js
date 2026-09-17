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

function setNav() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === here || (here === "" && href === "index.html")) a.classList.add("is-active");
  });
  const btn = document.querySelector(".menu-btn");
  const nav = document.querySelector(".nav");
  if (btn && nav) {
    btn.addEventListener("click", () => nav.classList.toggle("is-open"));
  }
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
    const avg = cards.length
      ? Math.round(cards.reduce((n, el) => n + percentFor(el.getAttribute("data-week-progress"), { tasks: Number(el.getAttribute("data-tasks") || 4) }), 0) / cards.length)
      : 0;
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

  const tocLinks = [...document.querySelectorAll(".toc a")];
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      tocLinks.forEach((a) => a.classList.toggle("is-active", a.getAttribute("href") === "#" + e.target.id));
    });
  }, { rootMargin: "-40% 0px -50% 0px" });
  document.querySelectorAll(".week-layout section[id]").forEach((sec) => observer.observe(sec));
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
  let showA = false;

  function dueIndex() {
    const now = Date.now();
    const map = loadState().cards[weekId];
    const due = cards.map((c, idx) => idx).filter((idx) => (map[idx]?.next || 0) <= now);
    return due.length ? due[0] : 0;
  }

  function render() {
    i = dueIndex();
    showA = false;
    const card = cards[i];
    stage.querySelector("[data-q]").textContent = card.q;
    stage.querySelector("[data-a]").hidden = true;
    stage.querySelector("[data-a]").textContent = card.a;
    stage.querySelector(".hint").hidden = false;
    const meta = loadState().cards[weekId][i];
    stage.querySelector("[data-box]").textContent = "Caja " + meta.box;
  }

  stage.addEventListener("click", () => {
    showA = true;
    stage.querySelector("[data-a]").hidden = false;
    stage.querySelector(".hint").hidden = true;
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
    const card = cards[i % cards.length];
    stage.querySelector("[data-q]").textContent = card.q;
    const a = stage.querySelector("[data-a]");
    a.hidden = true;
    a.textContent = card.a;
    stage.querySelector(".hint").hidden = false;
    const src = stage.querySelector("[data-src]");
    if (src) src.textContent = card.src || "";
  }
  stage.addEventListener("click", () => {
    stage.querySelector("[data-a]").hidden = false;
    stage.querySelector(".hint").hidden = true;
  });
  document.querySelector("[data-next-card]")?.addEventListener("click", (e) => {
    e.stopPropagation();
    i += 1;
    render();
  });
  render();
}

setNav();
paintHomeProgress();
bindComfort();
bindWeek();
bindGlobalFlash();
