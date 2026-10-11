<script>
  import { jobStatus, cancel, retry } from "$lib/api";
  import { JOB_TONE } from "$lib/format";

  let { jobId, onfinished } = $props();

  let currentId = $state(jobId);
  let job = $state(null);
  let feed = $state([]);
  let timer;

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

  function start(id) {
    clearInterval(timer);
    timer = setInterval(async () => {
      try {
        const s = await jobStatus(id);
        apply(s);
        if (["done", "failed", "cancelled"].includes(s.status)) {
          clearInterval(timer);
          onfinished?.();
        }
      } catch {
        /* keep polling */
      }
    }, 1500);
  }

  // A new jobId prop (a fresh submission) resets the panel.
  $effect(() => {
    if (jobId && jobId !== currentId) {
      currentId = jobId;
      job = null;
      feed = [];
    }
  });

  $effect(() => {
    if (currentId) start(currentId);
    return () => clearInterval(timer);
  });

  async function stop() {
    if (currentId) await cancel(currentId);
  }
  async function again() {
    if (!job?.id) return;
    const { job_id } = await retry(job.id);
    currentId = job_id;
    job = null;
    feed = [];
  }
</script>

{#if job}
  <section class="card mt-4 p-4">
    <div class="flex items-center gap-2">
      <span class="text-sm font-semibold {JOB_TONE[job.status] || "text-muted"}">{job.status}</span>
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
{/if}
