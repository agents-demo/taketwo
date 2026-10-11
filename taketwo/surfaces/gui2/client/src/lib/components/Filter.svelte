<script>
  import { VERDICT_FILTERS } from "$lib/format";

  let { value = "All", onchange } = $props();
</script>

<div class="mt-3 flex flex-wrap gap-2">
  {#each VERDICT_FILTERS as f}
    <button
      onclick={() => onchange?.(f)}
      class="rounded-full border-2 border-line px-3 py-1 text-xs font-semibold"
      class:bg-surface={value === f}
      class:text-app={value === f}
      class:text-muted={value !== f}
    >{f}</button>
  {/each}
</div>
