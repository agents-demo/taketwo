/* TakeTwo Reels — a swipeable proof feed over the FastAPI backend. */
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const media = (job, name) => `/media/${encodeURIComponent(job)}/${name}`;

const state = { feed: [], tab: "feed" };

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

/* ---------------------------------------------------------------- feed card */
function mediaMarkup(run) {
  const job = esc(run.job);
  if (run.has_video) {
    return `<div class="media">
      <video src="${media(run.job, "proof.mp4")}" autoplay loop muted playsinline></video>
      <span class="chip before-chip">bug</span><span class="chip after-chip">fixed</span>
    </div>`;
  }
  if (run.has_before && run.has_after) {
    return `<div class="media">
      <div class="compare" data-job="${job}">
        <img class="after" src="${media(run.job, "after.png")}" alt="after the fix" />
        <img class="before" src="${media(run.job, "before.png")}" alt="before the fix" />
        <div class="divider"><span class="knob">⇔</span></div>
      </div>
      <span class="chip before-chip">bug</span><span class="chip after-chip">fixed</span>
    </div>`;
  }
  return `<div class="media" style="display:grid;place-items:center;color:var(--muted)">no proof clip yet</div>`;
}

function cardMarkup(run) {
  const vclass = run.verdict === "reproduced" ? "good" : run.verdict === "not_reproduced" ? "bad" : "";
  return `<article class="card" data-job="${esc(run.job)}">
    ${mediaMarkup(run)}
    <div class="meta">
      <div class="line1">
        <span class="handle">@${esc(run.job)}</span>
        <span class="pill ${vclass}">${esc(run.verdict.replace("_", " "))}</span>
        <span class="pill ${run.verified ? "good" : ""}">${run.verified ? "verified" : "unverified"}</span>
        <span class="pill">${esc(run.repo)}</span>
      </div>
      <div class="evidence">${esc(run.evidence || "reproduced from the clip")}</div>
      <div class="thumbs">
        <button class="btn" data-act="details">Details</button>
        <button class="btn primary" data-act="approve" ${run.verified ? "" : "disabled"}>Approve &amp; merge</button>
      </div>
    </div>
    <div class="rail">
      <button data-act="share" title="Share">↗</button>
      <button data-act="download" title="Download">⬇</button>
      ${run.has_video || run.has_before ? `<button data-act="proof" title="Open proof">▶</button>` : ""}
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
    feed.innerHTML = `<div class="empty"><h2>No runs yet</h2><p>Tap ＋ New to drop a clip and watch it get fixed.</p></div>`;
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
        if (act === "details" || act === "proof") openClip(job);
        else if (act === "approve") approve(job);
        else if (act === "share") share(run);
        else if (act === "download") download(job, run);
      });
    });
  });
}

/* ------------------------------------------------------------------- actions */
async function approve(job) {
  try {
    await api(`/runs/${encodeURIComponent(job)}/review/approved`, { method: "POST" });
    toast("Approved — nice one 🫡");
    confetti();
    load();
  } catch { toast("Could not approve"); }
}

async function share(run) {
  const text = `TakeTwo fixed a bug from a screen recording 🎬\n@${run.job} — ${run.verdict} · ${run.verified ? "verified" : "unverified"}\n${run.evidence || ""}`;
  try {
    if (navigator.share) await navigator.share({ title: "TakeTwo", text });
    else { await navigator.clipboard.writeText(text); toast("Caption copied"); }
  } catch { /* cancelled */ }
}

function download(job, run) {
  const href = run.has_video ? media(job, "proof.mp4") : media(job, "proof.png");
  const a = document.createElement("a");
  a.href = href;
  a.download = `${job}_proof${run.has_video ? ".mp4" : ".png"}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
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
  const steps = (run.steps || []).map((s, i) => `<li>${i + 1}. ${esc(s.action)} ${esc(s.target || "")}</li>`).join("");
  openSheet(`
    <h2>@${esc(job)}</h2>
    <div class="line1" style="display:flex;gap:8px;margin-bottom:10px">
      <span class="pill ${run.verdict === "reproduced" ? "good" : "bad"}">${esc(run.verdict.replace("_", " "))}</span>
      <span class="pill">score ${run.score}</span>
      <span class="pill">${run.verified ? "verified" : "unverified"}</span>
    </div>
    ${run.has_before && run.has_after ? `<div class="media" style="height:260px;border-radius:16px;overflow:hidden;position:relative">
        <div class="compare" data-job="${esc(job)}">
          <img class="after" src="${media(job, "after.png")}" alt="after" />
          <img class="before" src="${media(job, "before.png")}" alt="before" />
          <div class="divider"><span class="knob">⇔</span></div>
        </div></div>` : ""}
    <h2 style="font-size:18px;margin-top:16px">Fix</h2>
    <pre class="diff">${esc(run.diff || "(no diff proposed)")}</pre>
    <h2 style="font-size:18px">Steps</h2>
    <ul class="steps">${steps || "<li>(none inferred)</li>"}</ul>
    <h2 style="font-size:18px">Ask about this run</h2>
    <div class="chat"><input id="q" placeholder="why this selector?" /><button class="btn primary" id="ask">Ask</button></div>
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
  catch { ans.textContent = "Could not answer."; }
}

function openNew() {
  openSheet(`
    <h2>New run</h2>
    <label class="field"><span>Recording path</span><input id="f-video" value="runtime/data/sample_bug_live.mov" /></label>
    <label class="field"><span>Repository (owner/name, optional)</span><input id="f-repo" placeholder="owner/name" /></label>
    <label class="field"><span>App URL (optional)</span><input id="f-app" placeholder="http://localhost:8130" /></label>
    <button class="btn primary" id="f-go">Record &amp; reproduce</button>
  `);
  $("#f-go").addEventListener("click", submitNew);
}

async function submitNew() {
  const body = {
    video_path: $("#f-video").value.trim(),
    repo: $("#f-repo").value.trim(),
    app_url: $("#f-app").value.trim(),
  };
  if (!body.video_path) { toast("A recording path is required"); return; }
  closeSheet();
  try {
    const { job_id } = await api("/replay/async", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    toast(`Queued ${job_id}`);
    watch(job_id);
  } catch { toast("Could not start the run"); }
}

function watch(jobId) {
  const timer = setInterval(async () => {
    let s;
    try { s = await api(`/jobs/${encodeURIComponent(jobId)}`); } catch { return; }
    const stage = (s.progress && s.progress.stage) || s.status;
    const pct = Math.round((s.progress && s.progress.pct) || 0);
    toast(`${stage} · ${pct}%`);
    if (s.status === "done" || s.status === "failed" || s.status === "cancelled") {
      clearInterval(timer);
      if (s.status === "done") { confetti(); toast("Done — check the feed"); }
      setTimeout(load, 800);
    }
  }, 1500);
}

/* ------------------------------------------------------------------ scoreboard */
function renderScore(data) {
  const pct = Math.round((data.rate || 0) * 100);
  const repos = (data.repos || []).map((r) =>
    `<div class="repo"><b>${esc(r.repo)}</b><small>${Math.round(r.rate * 100)}% · ${r.runs} runs · ${r.verified} verified</small></div>`
  ).join("");
  $("#score").innerHTML = `
    <h1>Scoreboard</h1>
    <div class="rate">${pct}%</div>
    <div class="stats">
      <div class="stat"><b>${data.reproduced}</b><span>reproduced</span></div>
      <div class="stat"><b>${data.verified}</b><span>verified</span></div>
      <div class="stat"><b>${data.total}</b><span>runs</span></div>
    </div>
    <div class="bar"><i style="width:${pct}%"></i></div>
    <h2 style="font-family:var(--display);margin-top:24px">Repos</h2>
    ${repos || '<p style="color:var(--muted)">No runs yet.</p>'}
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

async function load() {
  try {
    const data = await api("/scoreboard");
    state.feed = data.feed || [];
    renderFeed();
    renderScore(data);
  } catch {
    $("#feed").innerHTML = `<div class="empty"><h2>Backend not reachable</h2><p>Run <code>uvicorn taketwo.interfaces.api:app</code> and open <code>/app/</code>.</p></div>`;
  }
}

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => setTab(b.dataset.tab)));
$("#scrim").addEventListener("click", closeSheet);
$("#refresh").addEventListener("click", load);

load();
