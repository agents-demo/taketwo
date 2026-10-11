<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { getScoreboard, cardScore } from "$lib/api";

  let d = $state(null);
  onMount(async () => {
    d = await getScoreboard();
  });
  const pct = $derived(Math.round((d?.rate || 0) * 100));
  const hall = $derived(
    [...(d?.feed || [])].sort((a, b) => b.verified - a.verified || b.score - a.score).slice(0, 10),
  );
  const trend = $derived.by(() => {
    const rows = [...(d?.feed || [])].reverse();
    let seen = 0;
    return rows.map((r, i) => {
      seen += r.verdict === "reproduced" ? 1 : 0;
      return { x: i + 1, y: seen / (i + 1) };
    });
  });
  const trendPoints = $derived(
    trend.length < 2
      ? ""
      : trend.map((p) => `${(p.x / trend.length) * 300},${100 - p.y * 100}`).join(" "),
  );
</script>

<h1 class="font-display text-3xl font-bold">Scoreboard</h1>
<p class="mt-1 text-sm text-muted">The reproduce rate, in the open.</p>

{#if d}
  <div class="mt-4 bg-gradient-to-br from-accent2 to-accent bg-clip-text font-display text-7xl font-bold text-transparent">{pct}%</div>
  <div class="mt-3 h-3 overflow-hidden rounded-full border-2 border-line"><div class="h-full bg-gradient-to-r from-accent to-accent2" style="width:{pct}%"></div></div>

  <div class="mt-4 grid grid-cols-4 gap-3">
    <div class="card p-4"><div class="font-display text-3xl">{d.reproduced}</div><div class="text-xs text-muted">fixed</div></div>
    <div class="card p-4"><div class="font-display text-3xl">{d.verified}</div><div class="text-xs text-muted">proven</div></div>
    <div class="card p-4"><div class="font-display text-3xl">{d.approved}</div><div class="text-xs text-muted">approved</div></div>
    <div class="card p-4"><div class="font-display text-3xl">{d.total}</div><div class="text-xs text-muted">clips</div></div>
  </div>

  {#if trendPoints}
    <h2 class="mt-6 font-display text-lg">Reproduce rate over runs</h2>
    <div class="card mt-2 p-3">
      <svg viewBox="0 0 300 100" preserveAspectRatio="none" class="h-40 w-full">
        <polyline points={trendPoints} fill="none" stroke="currentColor" stroke-width="1.5" class="text-accent2" vector-effect="non-scaling-stroke" />
      </svg>
      <div class="flex justify-between text-xs text-muted"><span>first run</span><span>cumulative rate → latest</span></div>
    </div>
  {/if}

  <h2 class="mt-6 font-display text-lg">Hall of fame</h2>
  <div class="mt-2 space-y-2">
    {#each hall as r (r.job)}
      <a href={`${base}/review?job=${encodeURIComponent(r.job)}`} class="card flex items-center justify-between p-3 transition hover:border-accent2">
        <b>{r.job}</b>
        <small class="text-muted">{r.verdict.replace("_", " ")} · {r.score}{r.verified ? " · ✅ verified" : ""}</small>
      </a>
    {/each}
  </div>

  <h2 class="mt-6 font-display text-lg">Projects</h2>
  <div class="mt-2 space-y-2">
    {#each d.repos as r}
      <div class="card flex items-center justify-between p-3">
        <b>{r.repo === "local" ? "Your clips" : r.repo}</b>
        <small class="text-muted">{Math.round(r.rate * 100)}% fixed · {r.runs} runs</small>
      </div>
    {/each}
  </div>

  <h2 class="mt-6 font-display text-lg">Share the score card</h2>
  <div class="card mt-2 p-3">
    <img src={cardScore()} alt="TakeTwo score card" class="w-full rounded-lg" />
    <a href={cardScore()} download="taketwo_scorecard.png" class="mt-2 inline-block rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">Download the card</a>
  </div>
{/if}
