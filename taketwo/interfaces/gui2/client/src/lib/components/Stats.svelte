<script>
  let { runs } = $props();
  const stats = $derived({
    total: runs.length,
    reproduced: runs.filter((r) => r.verdict === "reproduced").length,
    verified: runs.filter((r) => r.verified).length,
    approved: runs.filter((r) => r.review === "approved").length,
  });
</script>

<div class="mt-3 grid grid-cols-4 gap-3">
  <div class="card p-3"><div class="font-display text-2xl">{stats.total}</div><div class="text-xs text-muted">runs</div></div>
  <div class="card p-3"><div class="font-display text-2xl">{stats.reproduced}</div><div class="text-xs text-muted">reproduced</div></div>
  <div class="card p-3"><div class="font-display text-2xl">{stats.verified}</div><div class="text-xs text-muted">verified</div></div>
  <div class="card p-3"><div class="font-display text-2xl">{stats.approved}</div><div class="text-xs text-muted">approved</div></div>
</div>
