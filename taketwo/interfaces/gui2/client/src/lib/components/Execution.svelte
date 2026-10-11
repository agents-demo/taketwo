<script>
  import { buildTimeline } from "$lib/format";

  let { run } = $props();
  const timeline = $derived(buildTimeline(run));
</script>

{#if timeline.length}
  <h2 class="mt-6 font-display text-lg">Execution</h2>
  <p class="mt-1 text-xs text-muted">Ordered by when each model/tool call started.</p>
  <div class="mt-2 space-y-2">
    {#each timeline as e}
      <details class="card">
        <summary class="flex cursor-pointer items-center gap-2 px-3 py-2">
          <span class="rounded-full border-2 border-line px-2 py-0.5 text-[10px] uppercase tracking-wide {e.kind === 'tool' ? 'text-good' : 'text-accent2'}">{e.kind}</span>
          {#if e.kind === "model" && e.probe}
            <span class="text-sm font-semibold text-muted">image-support probe</span>
            <span class="text-xs text-muted">(framework self-check — not a real step)</span>
          {:else if e.kind === "model"}
            <span class="text-sm font-semibold">{e.label}{e.model ? ` · ${e.model}` : ""}</span>
            {#if e.prompt != null}<span class="text-xs text-muted">· {e.prompt} in / {e.completion ?? 0} out</span>{/if}
            {#if e.requested.length}<span class="truncate text-xs text-muted">→ calls {e.requested.map((r) => r.name).join(", ")}</span>{/if}
          {:else}
            <span class="text-sm font-semibold">Tool · {e.label}</span>
          {/if}
          {#if e.seconds != null}<span class="ml-auto shrink-0 text-xs text-muted">{e.seconds}s</span>{/if}
        </summary>
        <div class="px-3 pb-3">
          {#if e.kind === "tool"}
            <div class="mb-1 text-[11px] uppercase tracking-wide text-muted">Input — arguments passed to the tool</div>
            <pre class="max-h-64 overflow-auto rounded-lg border-2 border-line bg-ink p-2 text-[11px]">{e.args}</pre>
            {#if e.error}<div class="mt-2 rounded-lg border-2 border-bad/50 bg-bad/10 p-2 text-xs text-bad">{e.error}</div>{/if}
            <div class="mb-1 mt-2 text-[11px] uppercase tracking-wide text-muted">Output — result the tool returned</div>
            <pre class="max-h-64 overflow-auto rounded-lg border-2 border-line bg-ink p-2 text-[11px]">{e.result || "(empty)"}</pre>
          {:else}
            {#if e.offered.length}<p class="mb-2 text-xs text-muted">Tools offered: {e.offered.join(", ")}</p>{/if}
            <div class="mb-1 text-[11px] uppercase tracking-wide text-muted">Input — everything sent to the model</div>
            {#if e.messages.length}
              {#each e.messages as m}
                <div class="mt-2 text-[11px] font-semibold italic text-muted">{m.role}</div>
                <pre class="max-h-64 overflow-auto rounded-lg border-2 border-line bg-ink p-2 text-[11px] leading-relaxed">{m.content || (m.role === "assistant" ? "(no text — the model called a tool here)" : "")}</pre>
              {/each}
            {:else}
              <p class="text-xs text-muted">Input not saved (SAVE_CALL_IO is off) or unavailable.</p>
            {/if}
            <div class="mb-1 mt-3 text-[11px] uppercase tracking-wide text-muted">Output — what the model produced</div>
            {#each e.requested as r}
              <div class="mt-1 text-xs">↳ requested tool <code>{r.name}</code> with:</div>
              <pre class="max-h-40 overflow-auto rounded-lg border-2 border-line bg-ink p-2 text-[11px]">{r.arguments}</pre>
            {/each}
            {#if e.output}
              <pre class="mt-1 max-h-64 overflow-auto rounded-lg border-2 border-line bg-ink p-2 text-[11px] leading-relaxed">{e.output}</pre>
            {:else if e.requested.length}
              <p class="text-xs text-muted">No text — the model only requested tool calls on this turn.</p>
            {/if}
          {/if}
        </div>
      </details>
    {/each}
  </div>
{/if}
