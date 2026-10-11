<script>
  import { base } from "$app/paths";
  import { media } from "$lib/api";
  import Compare from "$lib/components/Compare.svelte";
  import { statusLabel } from "$lib/format";

  let { run } = $props();
  const [label, cls] = $derived(statusLabel(run));
</script>

<a href={`${base}/review?job=${encodeURIComponent(run.job)}`} class="card overflow-hidden transition hover:border-accent2">
  <div class="relative aspect-video bg-black">
    {#if run.has_video}
      <video src={media(run.job, "proof.mp4")} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
    {:else if run.has_before && run.has_after}
      <Compare before={media(run.job, "before.png")} after={media(run.job, "after.png")} />
    {:else if run.has_before}
      <img src={media(run.job, "before.png")} alt="captured frame" class="h-full w-full object-cover" />
    {:else if run.source}
      <video src={media(run.job, run.source)} muted loop autoplay playsinline class="h-full w-full object-cover"></video>
    {:else}
      <div class="grid h-full place-items-center text-muted">▶</div>
    {/if}
  </div>
  <div class="p-3">
    <div class="flex items-center gap-2">
      <span class="text-sm font-semibold {cls}">{label}</span>
      <span class="ml-auto text-xs text-muted">{run.repo}</span>
    </div>
    <p class="mt-1 truncate text-xs text-muted">{run.evidence || "—"}</p>
    <div class="mt-2 flex items-center justify-between">
      <span class="text-xs text-muted">{run.job}</span>
      <span class="text-xs font-semibold text-accent2">Review →</span>
    </div>
  </div>
</a>
