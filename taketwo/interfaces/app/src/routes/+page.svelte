<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { getRuns, submit, jobStatus, media } from "$lib/api";
  import Compare from "$lib/Compare.svelte";

  let runs = $state([]);
  let loading = $state(true);
  let video = $state("runtime/data/sample_bug_live.mov");
  let repo = $state("");
  let app_url = $state("");
  let jobId = $state(null);
  let stage = $state("");

  async function load() {
    loading = true;
    try {
      runs = (await getRuns()).runs;
    } finally {
      loading = false;
    }
  }
  async function go() {
    const { job_id } = await submit({ video_path: video, repo, app_url });
    jobId = job_id;
    poll();
  }
  function poll() {
    const t = setInterval(async () => {
      try {
        const s = await jobStatus(jobId);
        stage = s.progress?.stage || s.status;
        if (["done", "failed", "cancelled"].includes(s.status)) {
          clearInterval(t);
          jobId = null;
          stage = "";
          load();
        }
      } catch {
        /* keep polling */
      }
    }, 1500);
  }
  const status = (r) =>
    r.verdict === "reproduced" && r.verified
      ? ["✅ Fixed", "text-good"]
      : r.verdict === "reproduced"
        ? ["🔧 Fix ready", "text-accent2"]
        : ["👀 Unclear", "text-muted"];

  onMount(load);
</script>

<h1 class="font-display text-3xl font-bold">Runs</h1>
<p class="mt-1 text-sm text-muted">Turn a screen recording into a reproduction, a fix, and a before/after proof.</p>

<section class="card mt-5 p-4">
  <h2 class="font-display text-lg">New run</h2>
  <div class="mt-3 grid gap-3 sm:grid-cols-3">
    <label class="text-xs text-muted">Clip
      <input bind:value={video} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">Repository
      <input bind:value={repo} placeholder="owner/name" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">App URL
      <input bind:value={app_url} placeholder="http://localhost:8130" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
  </div>
  <button
    onclick={go}
    class="mt-4 rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/40"
  >Record &amp; reproduce</button>
  {#if jobId}<p class="mt-2 text-xs text-accent2">Running {jobId} · {stage}…</p>{/if}
</section>

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if !runs.length}
  <p class="mt-6 text-sm text-muted">No runs yet. Submit a clip above.</p>
{:else}
  <div class="mt-5 grid gap-4 sm:grid-cols-2">
    {#each runs as r (r.job)}
      {@const [label, cls] = status(r)}
      <a href={`${base}/review?job=${encodeURIComponent(r.job)}`} class="card overflow-hidden transition hover:border-accent2">
        <div class="relative aspect-video bg-black">
          {#if r.has_video}
            <video src={media(r.job, "proof.mp4")} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
          {:else if r.has_before && r.has_after}
            <Compare before={media(r.job, "before.png")} after={media(r.job, "after.png")} />
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
        </div>
      </a>
    {/each}
  </div>
{/if}
