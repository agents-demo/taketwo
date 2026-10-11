<script>
  let { run } = $props();
</script>

<h2 class="mt-6 font-display text-lg">Fix</h2>
<pre class="card mt-2 overflow-x-auto p-3 text-xs">{run.diff || "(no diff proposed)"}</pre>
{#if run.culprits?.length}
  <p class="mt-1 text-xs text-muted">Suspected cause: {run.culprits.slice(0, 3).join(", ")}</p>
{/if}
{#if run.test}
  <h3 class="mt-3 text-sm font-semibold">Regression test</h3>
  <pre class="card mt-1 overflow-x-auto p-3 text-xs">{run.test}</pre>
{/if}
