<script>
  let { run } = $props();
  const u = $derived(run?.usage || {});
</script>

{#if u.calls || run.calls?.length || run.tools?.length}
  <h2 class="mt-6 font-display text-lg">Usage</h2>
  <div class="mt-2 grid grid-cols-4 gap-3">
    <div class="card p-3"><div class="text-xs text-muted">Calls</div><div class="font-display text-xl">{u.calls ?? run.calls?.length ?? 0}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Tokens</div><div class="font-display text-xl">{u.total_tokens ?? 0}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Vision tok</div><div class="font-display text-xl">{u.vision?.total_tokens ?? 0}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Text tok</div><div class="font-display text-xl">{u.text?.total_tokens ?? 0}</div></div>
  </div>
{/if}
