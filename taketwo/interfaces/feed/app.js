/* TakeTwo Feed — intuitive + wow: a swipeable feed of "broken → fixed" clips with the
   reveal, plain-language status, and clear actions. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const media = (job, name) => `/media/${encodeURIComponent(job)}/${name}`;

const state = { feed: [], score: {}, liked: new Set() };

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg; el.hidden = false;
  clearTimeout(el._t); el._t = setTimeout(() => (el.hidden = true), 2200);
}
function statusFor(run) {
  if (run.verdict === "reproduced" && run.verified) return { cls: "fixed", label: "✅ Fixed", sub: "Reproduced and verified — same steps, before and after." };
  if (run.verdict === "reproduced") return { cls: "wip", label: "🔧 Fix ready", sub: "Found it and fixed it." };
  if (run.verdict === "not_reproduced") return { cls: "looking", label: "👀 Couldn't see it", sub: "We couldn't reproduce this from the clip." };
  return { cls: "looking", label: "🤖 On it", sub: "Still looking into it." };
}

/* ---------------------------------------------------------------- card */
function stageMarkup(run) {
  if (run.has_video) return `<video src="${media(run.job, "proof.mp4")}" autoplay loop muted playsinline></video>`;
  if (run.has_before && run.has_after) {
    return `<div class="compare" data-job="${esc(run.job)}">
        <img class="after" src="${media(run.job, "after.png")}" alt="after the fix" />
        <img class="before" src="${media(run.job, "before.png")}" alt="before the fix" />
        <div class="divider"><span class="knob">⇔</span></div></div>`;
  }
  return "";
}
function cardMarkup(run) {
  const st = statusFor(run);
  const hasCompare = !run.has_video && run.has_before && run.has_after;
  return `<article class="card" data-job="${esc(run.job)}">
    <div class="stage">
      ${stageMarkup(run)}
      <div class="grade"></div>
      <div class="kinetic"><span class="k broken">It's broken</span><span class="k fixed">Fixed</span></div>
      ${hasCompare ? `<div class="labels"><span class="b">Before</span><span class="a">After</span></div>` : ""}
    </div>
    <div class="meta">
      <div class="line1"><span class="status ${st.cls}">${st.label}</span><span class="repo">${esc(run.repo === "local" ? "your clip" : run.repo)}</span></div>
      <div class="evidence">${esc(run.evidence || st.sub)}</div>
      <div class="thumbs">
        <button class="btn" data-act="details">Details</button>
        <button class="btn primary" data-act="approve">Looks good ✅</button>
      </div>
      <div class="dev-only line1" style="margin-top:8px">
        <span class="repo">${esc(run.job)} · score ${run.score} · ${esc(run.verdict)}</span>
      </div>
    </div>
  </article>`;
}

function initCompare(el) {
  const before = $(".before", el), divider = $(".divider", el);
  const setX = (x) => { const p = Math.max(0, Math.min(100, x)); before.style.clipPath = `inset(0 ${100 - p}% 0 0)`; divider.style.left = p + "%"; };
  const at = (x) => { const r = el.getBoundingClientRect(); setX(((x - r.left) / r.width) * 100); };
  setX(50);
  let axis = null, start = null;
  el.addEventListener("pointerdown", (e) => { axis = null; start = { x: e.clientX, y: e.clientY }; });
  el.addEventListener("pointermove", (e) => {
    if (!start) return;
    const dx = e.clientX - start.x, dy = e.clientY - start.y;
    if (axis === null) { if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return; axis = Math.abs(dx) > Math.abs(dy) ? "x" : "y"; }
    if (axis === "x") at(e.clientX);
  });
  const end = () => { start = null; axis = null; };
  el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
}

function renderFeed() {
  const feed = $("#feed");
  if (!state.feed.length) {
    feed.innerHTML = `<div class="empty"><h2>Send a broken clip 🎬</h2><p style="color:var(--muted)">Drop that shaky recording — we reproduce it, fix it, and show before/after.</p><button class="btn primary" id="empty-new" style="width:auto;padding:12px 22px">Miracle this ✨</button></div>`;
    $("#empty-new").addEventListener("click", openNew);
    $("#hint") && ($("#hint").hidden = true);
    return;
  }
  feed.innerHTML = state.feed.map(cardMarkup).join("") + `<div class="hint" id="hint">${state.feed.length > 1 ? "▲ swipe for next" : "tap a card for details"}</div>`;
  $$(".compare", feed).forEach(initCompare);

  $$(".card", feed).forEach((card) => {
    const job = card.dataset.job;
    const run = state.feed.find((r) => r.job === job);
    card.querySelectorAll("button[data-act]").forEach((b) =>
      b.addEventListener("click", (e) => { e.stopPropagation(); if (b.dataset.act === "approve") approve(job); else openClip(run); })
    );
    let down = null;
    card.querySelector(".stage").addEventListener("pointerdown", (e) => { down = { x: e.clientX, y: e.clientY }; });
    card.querySelector(".stage").addEventListener("pointerup", (e) => {
      if (!down) return;
      const dx = Math.abs(e.clientX - down.x), dy = Math.abs(e.clientY - down.y);
      down = null;
      if (dx < 8 && dy < 8) openClip(run);
    });
  });

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting && e.intersectionRatio > 0.55) {
      e.target.classList.remove("active", "settled"); void e.target.offsetWidth;
      e.target.classList.add("active");
      setTimeout(() => e.target.classList.add("settled"), 2400);
    }
  }, { threshold: [0.55] });
  $$(".card", feed).forEach((c) => io.observe(c));
}

/* ---------------------------------------------------------------- actions */
async function approve(job) {
  try { await api(`/runs/${encodeURIComponent(job)}/review/approved`, { method: "POST" }); flash(); confetti(); setTimeout(load, 1300); }
  catch { toast("Try again"); }
}
function flash() {
  const el = $("#flash");
  el.hidden = false; el.style.animation = "none"; void el.offsetWidth; el.style.animation = "";
  clearTimeout(el._t); el._t = setTimeout(() => { el.hidden = true; }, 1250);
}
function share(run) {
  const text = `This bug got fixed from a screen recording 🎬 ${run.evidence || ""}`.trim();
  if (navigator.share) navigator.share({ title: "TakeTwo", text }).catch(() => {});
  else navigator.clipboard.writeText(text).then(() => toast("Copied")).catch(() => {});
}

/* ---------------------------------------------------------------- sheets */
function openSheet(html) { $("#sheet").innerHTML = `<div class="grabber"></div>` + html; $("#sheet").hidden = false; $("#scrim").hidden = false; }
function closeSheet() { $("#sheet").hidden = true; $("#scrim").hidden = true; }

function openClip(run) {
  if (!run) return;
  const st = statusFor(run);
  const steps = (run.steps || []).map((s, i) => `<li>${i + 1}. ${esc(s.action)} ${esc(s.target || "")}</li>`).join("");
  openSheet(`
    <span class="status ${st.cls}" style="display:inline-block;margin-bottom:6px">${st.label}</span>
    <h2>${st.sub}</h2>
    ${run.has_before && run.has_after ? `<div class="stage" style="position:relative;height:270px;border-radius:16px;overflow:hidden">
        <div class="compare" data-job="${esc(run.job)}">
          <img class="after" src="${media(run.job, "after.png")}" alt="after" />
          <img class="before" src="${media(run.job, "before.png")}" alt="before" />
          <div class="divider"><span class="knob">⇔</span></div></div></div>` : ""}
    <div class="dev-only">
      <pre class="diff">${esc(run.diff || "(no diff proposed)")}</pre>
      <h2 style="font-size:16px">Steps</h2><ul class="steps">${steps || "<li>(none inferred)</li>"}</ul>
    </div>
    <h2 style="font-size:18px">Ask</h2>
    <div class="chat"><input id="q" placeholder="Was this a real fix?" /><button class="btn primary" id="ask">Ask</button></div>
    <div class="ans" id="ans" hidden></div>
  `);
  const cmp = $("#sheet .compare"); if (cmp) initCompare(cmp);
  $("#ask").addEventListener("click", () => askRun(run.job));
  $("#q").addEventListener("keydown", (e) => { if (e.key === "Enter") askRun(run.job); });
}
async function askRun(job) {
  const q = $("#q").value.trim(); if (!q) return;
  const ans = $("#ans"); ans.hidden = false; ans.textContent = "…";
  try { ans.textContent = (await api(`/runs/${encodeURIComponent(job)}/ask?q=${encodeURIComponent(q)}`)).answer; }
  catch { ans.textContent = "Couldn't answer that."; }
}

function openNew() {
  openSheet(`
    <h2>Send a broken clip</h2>
    <p>We watch it, reproduce it, fix it, and show you before/after.</p>
    <label class="field"><span>Clip</span><input id="f-video" value="runtime/data/sample_bug_live.mov" /></label>
    <div class="dev-only">
      <label class="field"><span>Repository</span><input id="f-repo" placeholder="owner/name" /></label>
      <label class="field"><span>App URL</span><input id="f-app" placeholder="http://localhost:8130" /></label>
    </div>
    <button class="btn primary" id="f-go">Fix it ✨</button>
  `);
  $("#f-go").addEventListener("click", submitNew);
}
async function submitNew() {
  const body = { video_path: $("#f-video").value.trim(), repo: ($("#f-repo") || {}).value || "", app_url: ($("#f-app") || {}).value || "" };
  if (!body.video_path) { toast("Add a clip"); return; }
  closeSheet();
  try { const { job_id } = await api("/replay/async", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }); toast("Watching your clip…"); watch(job_id); }
  catch { toast("Couldn't start"); }
}
function watch(jobId) {
  const t = setInterval(async () => {
    let s; try { s = await api(`/jobs/${encodeURIComponent(jobId)}`); } catch { return; }
    toast((s.progress && s.progress.stage) || s.status);
    if (["done", "failed", "cancelled"].includes(s.status)) { clearInterval(t); if (s.status === "done") confetti(); setTimeout(load, 900); }
  }, 1500);
}

function openScore() {
  const d = state.score || { rate: 0, reproduced: 0, verified: 0, total: 0, repos: [] };
  const pct = Math.round((d.rate || 0) * 100);
  const repos = (d.repos || []).slice(0, 8).map((r) => `<div class="repo-row"><b>${esc(r.repo === "local" ? "Your clips" : r.repo)}</b><small>${Math.round(r.rate * 100)}% fixed · ${r.runs}</small></div>`).join("");
  openSheet(`
    <h2>Fixes</h2><div class="big">${pct}%</div><p>of clips turned into a fix</p>
    <div class="bar"><i style="width:${pct}%"></i></div>
    <div class="stats"><div class="stat"><b>${d.reproduced}</b><span>fixed</span></div><div class="stat"><b>${d.verified}</b><span>proven</span></div><div class="stat"><b>${d.total}</b><span>clips</span></div></div>
    <h2 style="font-size:18px">Projects</h2>${repos || '<p style="color:var(--muted)">Nothing yet.</p>'}
  `);
}

function confetti() {
  const colors = ["#7c3aed", "#a78bfa", "#34d399", "#fb7185", "#ecf2f8"];
  for (let i = 0; i < 26; i++) {
    const d = document.createElement("div");
    d.style.cssText = `position:fixed;z-index:50;top:-10px;left:${Math.random() * 100}vw;width:10px;height:10px;border-radius:2px;background:${colors[i % 5]};pointer-events:none;transition:transform 1.2s ease, opacity 1.2s ease`;
    document.body.appendChild(d);
    requestAnimationFrame(() => { d.style.transform = `translateY(${60 + Math.random() * 40}vh) rotate(${Math.random() * 720}deg)`; d.style.opacity = "0"; });
    setTimeout(() => d.remove(), 1300);
  }
}
function setDev(on) { document.body.classList.toggle("dev", on); try { localStorage.setItem("taketwo.dev", on ? "1" : "0"); } catch {} }

async function load() {
  try { const data = await api("/scoreboard"); state.feed = data.feed || []; state.score = data; renderFeed(); }
  catch { $("#feed").innerHTML = `<div class="empty"><h2>Offline</h2><p style="color:var(--muted)">Start the server, then refresh.</p></div>`; }
}

$("#score").addEventListener("click", openScore);
$("#new").addEventListener("click", openNew);
$("#dev").addEventListener("click", () => setDev(!document.body.classList.contains("dev")));
$("#scrim").addEventListener("click", closeSheet);
setDev(localStorage.getItem("taketwo.dev") === "1");
load();
