<script>
  import { base } from "$app/paths";

  let { run } = $props();
</script>

<section class="card mt-5 p-4">
  <h2 class="font-display text-lg">Latest run</h2>
  <p class="mt-1 text-xs text-muted">{run.job} · {run.when}</p>
  <div class="mt-2 flex flex-wrap items-center gap-2 text-xs">
    <span class="rounded-full border-2 border-line px-2 py-0.5 {run.verdict === "reproduced" ? "text-good" : "text-muted"}">{run.verdict.replace("_", " ")}</span>
    <span class="rounded-full border-2 border-line px-2 py-0.5 {run.verified ? "text-good" : "text-muted"}">{run.verified ? "verified" : "unverified"}</span>
    <span class="rounded-full border-2 border-line px-2 py-0.5 {run.grounded ? "text-accent2" : "text-muted"}">{run.grounded ? "grounded" : "ungrounded"}</span>
  </div>
  <div class="mt-3 grid grid-cols-3 gap-3">
    <div><div class="font-display text-2xl">{run.score}</div><div class="text-xs text-muted">score</div></div>
    <div><div class="font-display text-2xl">{run.review}</div><div class="text-xs text-muted">review</div></div>
    <div><div class="font-display text-2xl">{run.verdict.replace("_", " ")}</div><div class="text-xs text-muted">verdict</div></div>
  </div>
  <a href={`${base}/review?job=${encodeURIComponent(run.job)}`} class="mt-3 inline-block text-sm font-semibold text-accent2">Open the full review →</a>
</section>
