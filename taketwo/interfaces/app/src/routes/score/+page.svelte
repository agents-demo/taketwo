<script>
  import { onMount } from "svelte";
  import { getScoreboard } from "$lib/api";

  let d = $state(null);
  onMount(async () => {
    d = await getScoreboard();
  });
  const pct = $derived(Math.round((d?.rate || 0) * 100));
</script>

<h1 class="font-display text-3xl font-bold">Scoreboard</h1>
<p class="mt-1 text-sm text-muted">The reproduce rate, in the open.</p>

{#if d}
  <div class="mt-4 bg-gradient-to-br from-accent2 to-accent bg-clip-text font-display text-7xl font-bold text-transparent">{pct}%</div>
  <div class="mt-3 h-3 overflow-hidden rounded-full border-2 border-line"><div class="h-full bg-gradient-to-r from-accent to-accent2" style="width:{pct}%"></div></div>

  <div class="mt-4 grid grid-cols-3 gap-3">
    <div class="card p-4"><div class="font-display text-3xl">{d.reproduced}</div><div class="text-xs text-muted">fixed</div></div>
    <div class="card p-4"><div class="font-display text-3xl">{d.verified}</div><div class="text-xs text-muted">proven</div></div>
    <div class="card p-4"><div class="font-display text-3xl">{d.total}</div><div class="text-xs text-muted">clips</div></div>
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
{/if}
