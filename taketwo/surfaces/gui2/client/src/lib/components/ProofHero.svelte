<script>
  import { media } from "$lib/api";
  import Compare from "$lib/components/Compare.svelte";

  let { run } = $props();
</script>

<div class="card mt-4 h-[320px] overflow-hidden">
  {#if run.has_video}
    <video src={media(run.job, "proof.mp4")} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
  {:else if run.has_before && run.has_after}
    <Compare before={media(run.job, "before.png")} after={media(run.job, "after.png")} />
  {:else if run.source}
    <video src={media(run.job, run.source)} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
  {:else if run.has_before}
    <img src={media(run.job, "before.png")} alt="captured frame" class="h-full w-full object-cover" />
  {:else}
    <div class="grid h-full place-items-center text-muted">no clip</div>
  {/if}
</div>
{#if !(run.has_before && run.has_after) && !run.has_video}
  <p class="mt-1 text-xs text-muted">Source recording — no proof yet (this run didn't reproduce).</p>
{/if}
