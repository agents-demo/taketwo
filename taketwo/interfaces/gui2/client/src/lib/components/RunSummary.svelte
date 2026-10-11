<script>
  import { base } from "$app/paths";
  import { verdictTone } from "$lib/format";

  let { run } = $props();
</script>

<div class="flex items-center gap-3">
  <h1 class="font-display text-2xl font-bold">{run.job}</h1>
  <span class="rounded-full border-2 border-line px-3 py-1 text-xs">{run.review.replace("_", " ")}</span>
  <a href={`${base}/`} class="ml-auto text-sm text-muted hover:text-white">← Runs</a>
</div>
<div class="mt-1 flex flex-wrap items-center gap-2 text-xs">
  <span class="rounded-full border-2 border-line px-2 py-0.5 {verdictTone(run.verdict)}">{run.verdict?.replace("_", " ")}</span>
  <span class="rounded-full border-2 border-line px-2 py-0.5 {run.verified ? "text-good" : "text-muted"}">{run.verified ? "verified" : "unverified"}</span>
  <span class="rounded-full border-2 border-line px-2 py-0.5 {run.grounded ? "text-accent2" : "text-muted"}">{run.grounded ? "grounded" : "ungrounded"}</span>
</div>
<p class="mt-1 text-xs text-muted">{[run.when, run.base_branch, run.video_name].filter(Boolean).join(" · ")}</p>
{#if run.evidence}<p class="mt-1 text-sm text-muted">Evidence: {run.evidence}</p>{/if}

<div class="mt-4 grid grid-cols-5 gap-3">
  <div class="card p-3"><div class="text-xs text-muted">Score</div><div class="font-display text-2xl">{run.score}</div></div>
  <div class="card p-3"><div class="text-xs text-muted">Grounded</div><div class="font-display text-lg">{run.grounded ? "yes" : "no"}</div></div>
  <div class="card p-3"><div class="text-xs text-muted">Verified</div><div class="font-display text-lg">{run.verified ? "yes" : "no"}</div></div>
  <div class="card p-3"><div class="text-xs text-muted">Steps</div><div class="font-display text-2xl">{(run.steps || []).length}</div></div>
  <div class="card p-3"><div class="text-xs text-muted">Tokens</div><div class="font-display text-2xl">{(run.usage?.total_tokens ?? 0).toLocaleString()}</div></div>
</div>
