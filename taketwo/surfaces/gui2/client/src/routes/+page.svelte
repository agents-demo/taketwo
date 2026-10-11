<script>
  import { onMount } from "svelte";
  import { getRuns, jobs } from "$lib/api";
  import { filterValue } from "$lib/format";
  import NewRun from "$lib/components/NewRun.svelte";
  import LiveJob from "$lib/components/LiveJob.svelte";
  import LatestRun from "$lib/components/LatestRun.svelte";
  import Readiness from "$lib/components/Readiness.svelte";
  import Stats from "$lib/components/Stats.svelte";
  import Filter from "$lib/components/Filter.svelte";
  import RunCard from "$lib/components/RunCard.svelte";

  let runs = $state([]);
  let active = $state(0);
  let loading = $state(true);
  let jobId = $state(null);
  let filter = $state("All");

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

  const filtered = $derived(filter === "All" ? runs : runs.filter((r) => r.verdict === filterValue(filter)));

  onMount(load);
</script>

<h1 class="font-display text-3xl font-bold">Reproduce a bug from a screen recording</h1>
<p class="mt-1 text-sm text-muted">A screen recording in. A reproduction, a fix, and before/after proof out.</p>

{#if runs.length}
  <LatestRun run={runs[0]} />
{/if}

<Readiness />

<NewRun onqueued={(id) => (jobId = id)} />

{#if jobId}
  <LiveJob {jobId} onfinished={load} />
{:else if active}
  <p class="mt-3 text-xs text-muted">{active} run(s) in flight</p>
{/if}

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if !runs.length}
  <p class="mt-6 text-sm text-muted">No runs yet. Submit a clip above.</p>
{:else}
  <h2 class="mt-6 font-display text-lg">Runs</h2>
  <Stats {runs} />
  <Filter value={filter} onchange={(f) => (filter = f)} />
  {#if !filtered.length}
    <p class="mt-4 text-sm text-muted">No runs match this filter.</p>
  {:else}
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      {#each filtered as r (r.job)}
        <RunCard run={r} />
      {/each}
    </div>
  {/if}
{/if}
