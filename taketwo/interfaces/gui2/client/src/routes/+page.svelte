<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { getRuns, submit, jobStatus, jobs, media, upload, cancel, retry, sample } from "$lib/api";
  import Compare from "$lib/Compare.svelte";

  let runs = $state([]);
  let active = $state(0);
  let loading = $state(true);

  // form
  let video = $state("runtime/data/sample_bug_live.mov");
  let repo = $state("");
  let base_branch = $state("main");
  let app_url = $state("");
  let agentic = $state(false);
  let uploadName = $state("");
  let uploading = $state(false);

  // live job
  let jobId = $state(null);
  let job = $state(null);
  let feed = $state([]);

  // filter
  let filter = $state("All");
  const FILTERS = ["All", "Reproduced", "Not reproduced", "Unclear"];
  const FILTER_VALUES = { All: null, Reproduced: "reproduced", "Not reproduced": "not_reproduced", Unclear: "unclear" };

  async function load() {
    loading = true;
    try {
      runs = (await getRuns()).runs;
      try {
        active = (await jobs()).jobs.filter((j) => ["queued", "running"].includes(j.status)).length;
      } catch {
        active = 0;
      }
    } finally {
      loading = false;
    }
  }

  async function pickFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    uploading = true;
    try {
      const res = await upload(file);
      video = res.path;
      uploadName = res.name;
    } catch (err) {
      alert(`Upload failed: ${err}`);
    } finally {
      uploading = false;
    }
  }

  async function useSample() {
    try {
      const s = await sample();
      if (s.clip) {
        video = s.clip;
        uploadName = "";
      }
      if (s.app_url) app_url = s.app_url;
    } catch {
      /* sample unavailable */
    }
  }

  async function go() {
    feed = [];
    const { job_id } = await submit({ video_path: video, repo, base_branch, app_url, agentic });
    jobId = job_id;
    poll();
  }

  function apply(s) {
    job = s;
    const p = s.progress || {};
    const done = ["done", "failed", "cancelled"].includes(s.status);
    const steps = (p.timings || []).map((t) => ({ stage: t.stage, seconds: t.seconds, state: "done" }));
    if (p.stage && p.stage !== "done") {
      steps.push({ stage: p.stage, seconds: null, state: done ? "done" : "running" });
    }
    feed = steps;
  }

  let timer;
  function poll() {
    clearInterval(timer);
    timer = setInterval(async () => {
      try {
        const s = await jobStatus(jobId);
        apply(s);
        if (["done", "failed", "cancelled"].includes(s.status)) {
          clearInterval(timer);
          jobId = null;
          load();
        }
      } catch {
        /* keep polling */
      }
    }, 1500);
  }

  async function stop() {
    if (jobId) await cancel(jobId);
  }
  async function again() {
    if (!job?.id) return;
    feed = [];
    const { job_id } = await retry(job.id);
    jobId = job_id;
    poll();
  }

  const status = (r) =>
    r.verdict === "reproduced" && r.verified
      ? ["✅ Fixed", "text-good"]
      : r.verdict === "reproduced"
        ? ["🔧 Fix ready", "text-accent2"]
        : ["👀 Unclear", "text-muted"];

  const tone = { done: "text-good", running: "text-accent2", failed: "text-bad", cancelled: "text-muted" };

  const stats = $derived({
    total: runs.length,
    reproduced: runs.filter((r) => r.verdict === "reproduced").length,
    verified: runs.filter((r) => r.verified).length,
    approved: runs.filter((r) => r.review === "approved").length,
  });
  const filtered = $derived(
    filter === "All" ? runs : runs.filter((r) => r.verdict === FILTER_VALUES[filter]),
  );

  onMount(load);
</script>

<h1 class="font-display text-3xl font-bold">Reproduce a bug from a screen recording</h1>
<p class="mt-1 text-sm text-muted">A screen recording in. A reproduction, a fix, and before/after proof out.</p>

{#if runs.length}
  {@const r = runs[0]}
  <section class="card mt-5 p-4">
    <h2 class="font-display text-lg">Latest run</h2>
    <p class="mt-1 text-xs text-muted">{r.job} · {r.when}</p>
    <div class="mt-2 flex flex-wrap items-center gap-2 text-xs">
      <span class="rounded-full border-2 border-line px-2 py-0.5 {r.verdict === "reproduced" ? "text-good" : "text-muted"}">{r.verdict.replace("_", " ")}</span>
      <span class="rounded-full border-2 border-line px-2 py-0.5 {r.verified ? "text-good" : "text-muted"}">{r.verified ? "verified" : "unverified"}</span>
      <span class="rounded-full border-2 border-line px-2 py-0.5 {r.grounded ? "text-accent2" : "text-muted"}">{r.grounded ? "grounded" : "ungrounded"}</span>
    </div>
    <div class="mt-3 grid grid-cols-3 gap-3">
      <div><div class="font-display text-2xl">{r.score}</div><div class="text-xs text-muted">score</div></div>
      <div><div class="font-display text-2xl">{r.review}</div><div class="text-xs text-muted">review</div></div>
      <div><div class="font-display text-2xl">{r.verdict.replace("_", " ")}</div><div class="text-xs text-muted">verdict</div></div>
    </div>
    <a href={`${base}/review?job=${encodeURIComponent(r.job)}`} class="mt-3 inline-block text-sm font-semibold text-accent2">Open the full review →</a>
  </section>
{/if}

<section class="card mt-4 p-4">
  <h2 class="font-display text-lg">New run</h2>
  <div class="mt-3 grid gap-3 sm:grid-cols-3">
    <label class="text-xs text-muted sm:col-span-3">Clip
      <input bind:value={video} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">Repository
      <input bind:value={repo} placeholder="owner/name" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">Base branch
      <input bind:value={base_branch} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">App URL
      <input bind:value={app_url} placeholder="http://localhost:8130" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
  </div>
  <div class="mt-3 flex flex-wrap items-center gap-3">
    <label class="cursor-pointer rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">
      Upload clip
      <input type="file" class="hidden" onchange={pickFile} accept=".mp4,.mov,.webm,.mkv,.png,.jpg,.jpeg,.webp" />
    </label>
    <span class="text-xs text-muted">{uploading ? "uploading…" : uploadName || "or paste a path above"}</span>
    <label class="ml-auto flex items-center gap-2 text-xs text-muted">
      <input type="checkbox" bind:checked={agentic} /> Agentic (let the model drive)
    </label>
  </div>
  <div class="mt-4 flex gap-3">
    <button
      onclick={go}
      disabled={!video.trim()}
      class="rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/40 disabled:opacity-40"
    >Record &amp; reproduce</button>
    <button onclick={useSample} class="rounded-xl border-2 border-line px-5 py-2.5 text-sm font-semibold">Try the sample</button>
  </div>
</section>

{#if job}
  <section class="card mt-4 p-4">
    <div class="flex items-center gap-2">
      <span class="text-sm font-semibold {tone[job.status] || "text-muted"}">{job.status}</span>
      <span class="text-xs text-muted">{job.progress?.stage || ""}{job.progress?.detail ? ` · ${job.progress.detail}` : ""}</span>
      <span class="ml-auto text-xs text-muted">{job.progress?.pct != null ? `${Math.round(job.progress.pct)}%` : ""}</span>
    </div>
    {#if job.progress?.pct != null}
      <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface">
        <div class="h-full rounded-full bg-gradient-to-r from-accent to-accent2" style={`width: ${Math.max(2, Math.round(job.progress.pct))}%`}></div>
      </div>
    {/if}
    {#if feed.length}
      <ol class="mt-3 space-y-1">
        {#each feed as s}
          <li class="flex items-center gap-2 text-sm">
            <span class="{s.state === "running" ? "text-accent2" : "text-good"}">{s.state === "running" ? "●" : "✓"}</span>
            <span class="text-app">{s.stage}</span>
            {#if s.seconds != null}<span class="ml-auto text-xs text-muted">{s.seconds}s</span>{/if}
          </li>
        {/each}
      </ol>
    {/if}
    {#if job.error}<p class="mt-2 text-xs text-bad">{job.error}</p>{/if}
    <div class="mt-3 flex gap-3">
      {#if ["queued", "running"].includes(job.status)}
        <button onclick={stop} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">Cancel</button>
      {/if}
      {#if ["failed", "cancelled", "done"].includes(job.status)}
        <button onclick={again} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">Retry</button>
      {/if}
    </div>
  </section>
{:else if active}
  <p class="mt-3 text-xs text-muted">{active} run(s) in flight</p>
{/if}

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if !runs.length}
  <p class="mt-6 text-sm text-muted">No runs yet. Submit a clip above.</p>
{:else}
  <h2 class="mt-6 font-display text-lg">Runs</h2>
  <div class="mt-3 grid grid-cols-4 gap-3">
    <div class="card p-3"><div class="font-display text-2xl">{stats.total}</div><div class="text-xs text-muted">runs</div></div>
    <div class="card p-3"><div class="font-display text-2xl">{stats.reproduced}</div><div class="text-xs text-muted">reproduced</div></div>
    <div class="card p-3"><div class="font-display text-2xl">{stats.verified}</div><div class="text-xs text-muted">verified</div></div>
    <div class="card p-3"><div class="font-display text-2xl">{stats.approved}</div><div class="text-xs text-muted">approved</div></div>
  </div>
  <div class="mt-3 flex flex-wrap gap-2">
    {#each FILTERS as f}
      <button
        onclick={() => (filter = f)}
        class="rounded-full border-2 border-line px-3 py-1 text-xs font-semibold"
        class:bg-surface={filter === f}
        class:text-app={filter === f}
        class:text-muted={filter !== f}
      >{f}</button>
    {/each}
  </div>

  {#if !filtered.length}
    <p class="mt-4 text-sm text-muted">No runs match this filter.</p>
  {:else}
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      {#each filtered as r (r.job)}
        {@const [label, cls] = status(r)}
        <a href={`${base}/review?job=${encodeURIComponent(r.job)}`} class="card overflow-hidden transition hover:border-accent2">
          <div class="relative aspect-video bg-black">
            {#if r.has_video}
              <video src={media(r.job, "proof.mp4")} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
            {:else if r.has_before && r.has_after}
              <Compare before={media(r.job, "before.png")} after={media(r.job, "after.png")} />
            {:else if r.has_before}
              <img src={media(r.job, "before.png")} alt="captured frame" class="h-full w-full object-cover" />
            {:else if r.source}
              <video src={media(r.job, r.source)} muted loop autoplay playsinline class="h-full w-full object-cover"></video>
            {:else}
              <div class="grid h-full place-items-center text-muted">▶</div>
            {/if}
          </div>
          <div class="p-3">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold {cls}">{label}</span>
              <span class="ml-auto text-xs text-muted">{r.repo}</span>
            </div>
            <p class="mt-1 truncate text-xs text-muted">{r.evidence || "—"}</p>
            <div class="mt-2 flex items-center justify-between">
              <span class="text-xs text-muted">{r.job}</span>
              <span class="text-xs font-semibold text-accent2">Review →</span>
            </div>
          </div>
        </a>
      {/each}
    </div>
  {/if}
{/if}
