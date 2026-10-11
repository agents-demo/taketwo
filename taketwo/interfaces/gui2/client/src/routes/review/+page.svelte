<script>
  import { page } from "$app/stores";
  import { getRun, review } from "$lib/api";
  import { captionFor } from "$lib/format";
  import RunSummary from "$lib/components/RunSummary.svelte";
  import ProofHero from "$lib/components/ProofHero.svelte";
  import ShareProof from "$lib/components/ShareProof.svelte";
  import FixBlock from "$lib/components/FixBlock.svelte";
  import Evidence from "$lib/components/Evidence.svelte";
  import Usage from "$lib/components/Usage.svelte";
  import Execution from "$lib/components/Execution.svelte";
  import ReviewPanel from "$lib/components/ReviewPanel.svelte";
  import Ask from "$lib/components/Ask.svelte";

  let run = $state(null);
  let error = $state("");
  const job = $derived($page.url.searchParams.get("job"));

  async function load() {
    if (!job) return;
    try {
      run = await getRun(job);
    } catch (e) {
      error = String(e);
    }
  }
  async function decide(decision, note, actor) {
    await review(job, decision, note, actor);
    await load();
  }
  $effect(() => {
    job;
    load();
  });
</script>

{#if error}
  <p class="text-bad">{error}</p>
{:else if !run}
  <p class="text-muted">Loading…</p>
{:else}
  <RunSummary {run} />
  <ProofHero {run} />
  <ShareProof {run} caption={captionFor(run)} />
  <FixBlock {run} />
  <Evidence {run} />
  <Usage {run} />
  <Execution {run} />
  <ReviewPanel {run} ondecide={decide} />
  <Ask {job} />
{/if}
