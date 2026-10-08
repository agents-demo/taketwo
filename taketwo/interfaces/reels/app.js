/* TakeTwo Reels — a consumer "broken → fixed" feed. Plain language by default;
   everything technical is behind the Dev toggle. */
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const media = (job, name) => `/media/${encodeURIComponent(job)}/${name}`;

const state = { feed: [], tab: "feed", liked: new Set() };

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(el._t);
  el._t = setTimeout(() => (el.hidden = true), 2200);
}

/* Plain-language status — no enums, no scores. */
function statusFor(run) {
  if (run.verdict === "reproduced" && run.verified)
    return { cls: "fixed", label: "✅ Fixed", headline: "Broken → fixed.", sub: "We replayed it — works now." };
  if (run.verdict === "reproduced")
    return { cls: "wip", label: "🔧 Fix ready", headline: "Found it. Fixed it.", sub: "Same steps, before and after." };
  if (run.verdict === "not_reproduced")
    return { cls: "looking", label: "👀 Couldn't see it", headline: "Couldn't reproduce this.", sub: "Try a longer clip." };
  return { cls: "looking", label: "🤖 On it", headline: "Working on it.", sub: "Hang tight." };
}

/* ---------------------------------------------------------------- feed card */
function mediaMarkup(run) {
  if (run.has_video) {
    return `<div class="media">
      <video src="${media(run.job, "proof.mp4")}" autoplay loop muted playsinline></video>
      <span class="chip before-chip">bug</span><span class="chip after-chip">fixed</span>
    </div>`;
  }
  if (run.has_before && run.has_after) {
    return `<div class="media">
      <div class="compare" data-job="${esc(run.job)}">
        <img class="after" src="${media(run.job, "after.png")}" alt="after the fix" />
        <img class="before" src="${media(run.job, "before.png")}" alt="before the fix" />
        <div class="divider"><span class="knob">⇔</span></div>
      </div>
      <span class="chip before-chip">bug</span><span class="chip after-chip">fixed</span>
    </div>`;
  }
  return `<div class="media" style="display:grid;place-items:center;color:var(--muted)">▶</div>`;
}

function devMeta(run) {
  return `<div class="dev-only line1">
    <span class="pill">${esc(run.job)}</span>
    <span class="pill">score ${run.score}</span>
    <span class="pill">${esc(run.repo)}</span>
    <span class="pill">${run.verdict.replace("_", " ")}</span>
  </div>`;
}

function cardMarkup(run) {
  const st = statusFor(run);
  return `<article class="card" data-job="${esc(run.job)}">
    ${mediaMarkup(run)}
    <span class="statuschip ${st.cls}">${st.label}</span>
    <div class="headline"><b>${st.headline}</b><small>${st.sub}</small></div>
    <div class="rail">
      <button data-act="like" title="React">${state.liked.has(run.job) ? "❤️" : "🤍"}</button>
      <button data-act="share" title="Share">↗</button>
    </div>
    <div class="meta">
      <div class="thumbs">
        <button class="btn primary" data-act="approve">Looks good ✅</button>
        <button class="btn" style="flex:0 0 56px" data-act="details" title="More">⋯</button>
      </div>
      ${devMeta(run)}
    </div>
  </article>`;
}

function initCompare(el) {
  const before = $(".before", el);
  const divider = $(".divider", el);
  const setX = (x) => {
    const p = Math.max(0, Math.min(100, x));
    before.style.clipPath = `inset(0 ${100 - p}% 0 0)`;
    divider.style.left = p + "%";
  };
  setX(50);
  const at = (clientX) => {
    const rect = el.getBoundingClientRect();
    setX(((clientX - rect.left) / rect.width) * 100);
  };
  el.addEventListener("pointerdown", (e) => {
    el.setPointerCapture(e.pointerId);
    at(e.clientX);
    const move = (ev) => at(ev.clientX);
    const up = () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); };
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
  });
}

function renderFeed() {
  const feed = $("#feed");
  if (!state.feed.length) {
    feed.innerHTML = `<div class="empty">
      <h2>Send a broken clip 🎬</h2>
      <p>That shaky screen recording of something misbehaving? Drop it and we'll figure it out — then show you the fix, before and after.</p>
      <button class="btn primary" id="empty-new">Miracle this</button>
    </div>`;
    $("#empty-new").addEventListener("click", openNew);
    return;
  }
  feed.innerHTML = state.feed.map(cardMarkup).join("");
  feed.querySelectorAll(".compare").forEach(initCompare);
  feed.querySelectorAll(".card").forEach((card) => {
    const job = card.dataset.job;
    const run = state.feed.find((r) => r.job === job);
    card.querySelectorAll("button[data-act]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const act = btn.dataset.act;
        if (act === "details") openClip(job);
        else if (act === "approve") approve(job);
        else if (act === "share") share(run);
        else if (act === "like") like(job);
      });
    });
  });
}

/* ------------------------------------------------------------------- actions */
async function approve(job) {
  try {
    await api(`/runs/${encodeURIComponent(job)}/review/approved`, { method: "POST" });
    toast("Nice — approved ✅");
    confetti();
    load();
  } catch { toast("Hmm, try again"); }
}

function like(job) {
  if (state.liked.has(job)) state.liked.delete(job); else state.liked.add(job);
  renderFeed();
  if (state.liked.has(job)) toast("Loved ❤️");
}

async function share(run) {
  const text = `This bug got fixed from a screen recording 🎬 ${run.evidence || ""}`.trim();
  try {
    if (navigator.share) await navigator.share({ title: "TakeTwo", text });
    else { await navigator.clipboard.writeText(text); toast("Copied"); }
  } catch { /* cancelled */ }
}

/* ------------------------------------------------------------------- sheet */
function openSheet(html) {
  $("#sheet").innerHTML = `<div class="grabber"></div>` + html;
  $("#sheet").hidden = false;
  $("#scrim").hidden = false;
}
function closeSheet() { $("#sheet").hidden = true; $("#scrim").hidden = true; }

function openClip(job) {
  const run = state.feed.find((r) => r.job === job);
  if (!run) return;
  const st = statusFor(run);
  const steps = (run.steps || []).map((s, i) => `<li>${i + 1}. ${esc(s.action)} ${esc(s.target || "")}</li>`).join("");
  openSheet(`
    <span class="statuschip ${st.cls}" style="position:static;display:inline-block;margin-bottom:8px">${st.label}</span>
    <h2>${st.headline}</h2>
    <p style="color:var(--muted);margin-top:-6px">${st.sub}</p>
    ${run.has_before && run.has_after ? `<div class="media" style="height:280px;border-radius:16px;overflow:hidden;position:relative;border:2px solid var(--line-2)">
        <div class="compare" data-job="${esc(job)}">
          <img class="after" src="${media(job, "after.png")}" alt="after" />
          <img class="before" src="${media(job, "before.png")}" alt="before" />
          <div class="divider"><span class="knob">⇔</span></div>
        </div></div>` : ""}
    <div class="dev-only">
      <h2 style="font-size:16px;margin-top:16px">Developer detail</h2>
      <div class="line1"><span class="pill">${esc(job)}</span><span class="pill">score ${run.score}</span><span class="pill">${esc(run.repo)}</span></div>
      <pre class="diff">${esc(run.diff || "(no diff proposed)")}</pre>
      <h2 style="font-size:16px">Steps</h2>
      <ul class="steps">${steps || "<li>(none inferred)</li>"}</ul>
    </div>
    <h2 style="font-size:18px">Ask</h2>
    <div class="chat"><input id="q" placeholder="Was this a real fix?" /><button class="btn primary" id="ask">Ask</button></div>
    <div class="ans" id="ans" hidden></div>
  `);
  const cmp = $("#sheet .compare");
  if (cmp) initCompare(cmp);
  $("#ask").addEventListener("click", () => askRun(job));
  $("#q").addEventListener("keydown", (e) => { if (e.key === "Enter") askRun(job); });
}

async function askRun(job) {
  const q = $("#q").value.trim();
  if (!q) return;
  const ans = $("#ans");
  ans.hidden = false; ans.textContent = "…";
  try { ans.textContent = (await api(`/runs/${encodeURIComponent(job)}/ask?q=${encodeURIComponent(q)}`)).answer; }
  catch { ans.textContent = "Couldn't answer that."; }
}

function openNew() {
  openSheet(`
    <h2>Send a broken clip</h2>
    <p style="color:var(--muted);margin-top:-6px">We watch it, reproduce it, fix it, and show you the before/after.</p>
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
  const body = {
    video_path: $("#f-video").value.trim(),
    repo: ($("#f-repo") || {}).value || "",
    app_url: ($("#f-app") || {}).value || "",
  };
  if (!body.video_path) { toast("Add a clip"); return; }
  closeSheet();
  try {
    const { job_id } = await api("/replay/async", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    toast("Watching your clip…");
    watch(job_id);
  } catch { toast("Couldn't start"); }
}

function watch(jobId) {
  const timer = setInterval(async () => {
    let s;
    try { s = await api(`/jobs/${encodeURIComponent(jobId)}`); } catch { return; }
    const stage = (s.progress && s.progress.stage) || s.status;
    toast(`${stage}`);
    if (["done", "failed", "cancelled"].includes(s.status)) {
      clearInterval(timer);
      if (s.status === "done") confetti();
      setTimeout(load, 800);
    }
  }, 1500);
}

/* ------------------------------------------------------------------ scoreboard */
function renderScore(data) {
  const pct = Math.round((data.rate || 0) * 100);
  const repos = (data.repos || []).slice(0, 8).map((r) =>
    `<div class="repo"><b>${esc(r.repo === "local" ? "Your clips" : r.repo)}</b><small>${Math.round(r.rate * 100)}% fixed · ${r.runs} clips</small></div>`
  ).join("");
  $("#score").innerHTML = `
    <h1>Fixes</h1>
    <div class="rate">${pct}%</div>
    <p style="color:var(--muted);margin-top:-4px">of clips turned into a fix</p>
    <div class="bar"><i style="width:${pct}%"></i></div>
    <div class="stats" style="margin-top:16px">
      <div class="stat"><b>${data.reproduced}</b><span>fixed</span></div>
      <div class="stat"><b>${data.verified}</b><span>proven</span></div>
      <div class="stat"><b>${data.total}</b><span>clips</span></div>
    </div>
    <h2 style="font-family:var(--display);margin-top:20px">Projects</h2>
    ${repos || '<p style="color:var(--muted)">Nothing yet.</p>'}
  `;
}

/* ------------------------------------------------------------------ tabs / boot */
function setTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  if (tab === "new") { openNew(); return; }
  $("#feed").hidden = tab !== "feed";
  $("#score").hidden = tab !== "score";
}

function confetti() {
  const colors = ["#7c3aed", "#a78bfa", "#34d399", "#fb7185"];
  for (let i = 0; i < 24; i++) {
    const d = document.createElement("div");
    d.style.cssText = `position:fixed;z-index:50;top:-10px;left:${Math.random() * 100}vw;width:9px;height:9px;border-radius:2px;background:${colors[i % 4]};pointer-events:none;transition:transform 1.1s ease, opacity 1.1s ease`;
    document.body.appendChild(d);
    requestAnimationFrame(() => {
      d.style.transform = `translateY(${60 + Math.random() * 40}vh) rotate(${Math.random() * 720}deg)`;
      d.style.opacity = "0";
    });
    setTimeout(() => d.remove(), 1200);
  }
}

function setDev(on) {
  state.dev = on;
  document.body.classList.toggle("dev", on);
  try { localStorage.setItem("taketwo.dev", on ? "1" : "0"); } catch {}
  renderFeed();
}

async function load() {
  try {
    const data = await api("/scoreboard");
    state.feed = data.feed || [];
    renderFeed();
    renderScore(data);
  } catch {
    $("#feed").innerHTML = `<div class="empty"><h2>Offline</h2><p>Start the server, then refresh.</p></div>`;
  }
}

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));
$("#scrim").addEventListener("click", closeSheet);
$("#refresh").addEventListener("click", load);
$("#dev").addEventListener("click", () => setDev(!state.dev));

try { setDev(localStorage.getItem("taketwo.dev") === "1"); } catch { setDev(false); }
load();
