<script>
  import { onMount } from "svelte";
  import { readiness } from "$lib/api";

  let checks = $state([]);
  onMount(async () => {
    try {
      checks = (await readiness()).checks;
    } catch {
      checks = [];
    }
  });
</script>

{#if checks.length}
  <section class="card mt-4 p-3">
    <div class="mb-1 text-xs text-muted">Readiness</div>
    <div class="flex flex-wrap gap-2 text-xs">
      {#each checks as c}
        <span class="rounded-full border-2 border-line px-2 py-0.5 {c.ok ? 'text-good' : 'text-bad'}" title={c.detail}>
          {c.ok ? "✓" : "✗"} {c.name}
        </span>
      {/each}
    </div>
    {#each checks.filter((c) => !c.ok) as c}
      <p class="mt-1 text-xs text-muted">⚠ {c.name}: {c.detail}</p>
    {/each}
  </section>
{/if}
