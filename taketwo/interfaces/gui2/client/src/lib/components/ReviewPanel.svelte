<script>
  let { run, ondecide } = $props();
  let note = $state("");
  let actor = $state("web");
</script>

<h2 class="mt-6 font-display text-lg">Review</h2>
<p class="mt-1 text-xs text-muted">Reviewing as</p>
<div class="mt-2 flex gap-2">
  <input bind:value={note} placeholder="why approve or send back" class="flex-1 rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
  <input bind:value={actor} placeholder="you" class="w-40 rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
</div>
<div class="mt-3 flex gap-3">
  <button
    onclick={() => ondecide?.("approved", note, actor)}
    disabled={!run.verified}
    class="rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
  >Approve &amp; merge</button>
  <button onclick={() => ondecide?.("changes_requested", note, actor)} class="rounded-xl border-2 border-line px-5 py-2.5 text-sm font-semibold">Request changes</button>
  <span class="ml-auto self-center text-xs text-muted">status: {run.review}</span>
</div>
{#if !run.verified}
  <p class="mt-2 text-xs text-muted">Approve is disabled until the fix is verified (a browser re-run or tests actually ran).</p>
{/if}
{#if run.delivery?.pr?.url || run.delivery?.issue?.url}
  <div class="mt-3 flex gap-3">
    {#if run.delivery.pr?.url}<a href={run.delivery.pr.url} target="_blank" rel="noreferrer" class="text-sm font-semibold text-accent2">Open pull request ↗</a>{/if}
    {#if run.delivery.issue?.url}<a href={run.delivery.issue.url} target="_blank" rel="noreferrer" class="text-sm font-semibold text-accent2">Open issue ↗</a>{/if}
  </div>
{/if}
{#if run.audit?.length}
  <h3 class="mt-4 text-sm font-semibold">Audit trail</h3>
  <ol class="mt-2 space-y-1">
    {#each run.audit as a}
      <li class="card flex items-center gap-2 px-3 py-2 text-xs">
        <span class="font-semibold {a.action === "approved" ? "text-good" : "text-accent2"}">{a.action.replace("_", " ")}</span>
        <span class="text-muted">{a.actor}</span>
        {#if a.note}<span class="truncate text-muted">· {a.note}</span>{/if}
        <span class="ml-auto shrink-0 text-muted">{a.when}</span>
      </li>
    {/each}
  </ol>
{:else}
  <p class="mt-3 text-xs text-muted">No decisions yet.</p>
{/if}
