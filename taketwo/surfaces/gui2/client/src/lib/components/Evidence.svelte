<script>
  let { run } = $props();
  const pipe = $derived(run?.timeline || []);
  const pipeMax = $derived(Math.max(0.001, ...pipe.map((t) => Number(t.seconds) || 0)));
</script>

<h2 class="mt-6 font-display text-lg">Evidence</h2>
{#if run.steps?.length}
  <table class="mt-2 w-full text-left text-sm">
    <thead><tr class="text-xs text-muted"><th class="py-1">action</th><th>target</th><th>value</th><th>t (s)</th><th>conf</th></tr></thead>
    <tbody>
      {#each run.steps as s}
        <tr class="border-t border-line text-muted">
          <td class="py-1">{s.action}</td><td>{s.target || ""}</td><td>{s.value ?? ""}</td><td>{s.timestamp ?? ""}</td><td>{s.confidence ?? ""}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}

{#if pipe.length}
  <h3 class="mt-4 text-sm font-semibold">Pipeline timeline</h3>
  <div class="mt-2 space-y-1">
    {#each pipe as t}
      <div class="flex items-center gap-2 text-xs">
        <span class="w-28 shrink-0 text-muted">{t.stage}</span>
        <div class="h-2.5 rounded bg-gradient-to-r from-accent to-accent2" style={`width:${Math.max(2, (Number(t.seconds) || 0) / pipeMax * 100)}%`}></div>
        <span class="text-muted">{t.seconds}s</span>
      </div>
    {/each}
  </div>
{/if}

{#if run.console?.length}
  <h3 class="mt-4 text-sm font-semibold">Browser console</h3>
  <pre class="card mt-1 overflow-auto p-3 text-xs">{run.console.join("\n")}</pre>
{/if}
{#if run.question}
  <p class="mt-3 rounded-lg border-2 border-line bg-ink p-2 text-xs text-muted">{run.question}</p>
{/if}
