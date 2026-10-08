<script>
  import { page } from "$app/stores";
  import { base } from "$app/paths";
  import { getRun, review, ask, media } from "$lib/api";
  import Compare from "$lib/Compare.svelte";

  let run = $state(null);
  let error = $state("");
  let q = $state("");
  let answer = $state("");
  let note = $state("");
  const job = $derived($page.url.searchParams.get("job"));

  async function load() {
    if (!job) return;
    try {
      run = await getRun(job);
    } catch (e) {
      error = String(e);
    }
  }
  async function decide(decision) {
    await review(job, decision);
    await load();
  }
  async function askRun() {
    if (!q.trim()) return;
    answer = "…";
    try {
      answer = (await ask(job, q)).answer;
    } catch {
      answer = "Couldn't answer that.";
    }
  }
  $effect(() => {
    job;
    load();
  });
</script>

{#if error}
  <p class="text-bad">{error}</p>
{:else if !run}
  <p class="text-muted">Loading…</p>
{:else}
  <div class="flex items-center gap-3">
    <h1 class="font-display text-2xl font-bold">{run.job}</h1>
    <span class="rounded-full border-2 border-line px-3 py-1 text-xs">{run.verified ? "verified" : "unverified"}</span>
    <a href={`${base}/`} class="ml-auto text-sm text-muted hover:text-white">← Runs</a>
  </div>
  <p class="mt-1 text-sm text-muted">{run.evidence || "—"}</p>

  <div class="card mt-4 h-[320px] overflow-hidden">
    {#if run.has_before && run.has_after}
      <Compare before={media(run.job, "before.png")} after={media(run.job, "after.png")} />
    {:else if run.has_video}
      <video src={media(run.job, "proof.mp4")} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
    {:else}
      <div class="grid h-full place-items-center text-muted">no proof clip</div>
    {/if}
  </div>

  <div class="mt-4 grid grid-cols-3 gap-3">
    <div class="card p-3"><div class="text-xs text-muted">Score</div><div class="font-display text-2xl">{run.score}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Verdict</div><div class="font-display text-lg">{run.verdict}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Steps</div><div class="font-display text-2xl">{(run.steps || []).length}</div></div>
  </div>

  <h2 class="mt-6 font-display text-lg">Fix</h2>
  <pre class="card mt-2 overflow-x-auto p-3 text-xs">{run.diff || "(no diff proposed)"}</pre>

  {#if run.steps?.length}
    <h2 class="mt-6 font-display text-lg">Steps</h2>
    <ol class="mt-2 space-y-1 text-sm text-muted">
      {#each run.steps as s, i}<li>{i + 1}. {s.action} {s.target || ""}</li>{/each}
    </ol>
  {/if}

  {@const u = run.usage || {}}
  {#if u.calls || run.calls?.length || run.tools?.length}
    <h2 class="mt-6 font-display text-lg">Usage</h2>
    <div class="mt-2 grid grid-cols-4 gap-3">
      <div class="card p-3"><div class="text-xs text-muted">Calls</div><div class="font-display text-xl">{u.calls ?? run.calls?.length ?? 0}</div></div>
      <div class="card p-3"><div class="text-xs text-muted">Tokens</div><div class="font-display text-xl">{u.total_tokens ?? 0}</div></div>
      <div class="card p-3"><div class="text-xs text-muted">Vision tok</div><div class="font-display text-xl">{u.vision?.total_tokens ?? 0}</div></div>
      <div class="card p-3"><div class="text-xs text-muted">Text tok</div><div class="font-display text-xl">{u.text?.total_tokens ?? 0}</div></div>
    </div>
    {#if run.calls?.length}
      <div class="card mt-3 overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="text-muted"><tr><th class="px-3 py-2">call</th><th>model</th><th>prompt</th><th>completion</th><th>total</th><th>s</th></tr></thead>
          <tbody>
            {#each run.calls as c}
              <tr class="border-t border-line/60">
                <td class="px-3 py-2">{c.label}</td><td>{c.model || "—"}</td>
                <td>{c.prompt_tokens ?? "—"}</td><td>{c.completion_tokens ?? "—"}</td>
                <td>{c.total_tokens ?? "—"}</td><td>{c.seconds ?? "—"}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
    {#if run.tools?.length}
      <h2 class="mt-4 font-display text-base">Tool activity</h2>
      <div class="card mt-2 overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="text-muted"><tr><th class="px-3 py-2">tool</th><th>seconds</th><th>arguments</th></tr></thead>
          <tbody>
            {#each run.tools as t}
              <tr class="border-t border-line/60"><td class="px-3 py-2">{t.name}</td><td>{t.seconds ?? "—"}</td><td class="max-w-[320px] truncate">{t.arguments || ""}</td></tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}

  <h2 class="mt-6 font-display text-lg">Review</h2>
  <input bind:value={note} placeholder="why approve or send back" class="mt-2 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
  <div class="mt-3 flex gap-3">
    <button
      onclick={() => decide("approved")}
      disabled={!run.verified}
      class="rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
    >Approve &amp; merge</button>
    <button onclick={() => decide("changes_requested")} class="rounded-xl border-2 border-line px-5 py-2.5 text-sm font-semibold">Request changes</button>
  </div>

  <h2 class="mt-6 font-display text-lg">Ask</h2>
  <div class="mt-2 flex gap-2">
    <input bind:value={q} onkeydown={(e) => e.key === "Enter" && askRun()} placeholder="was this a real fix?" class="flex-1 rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    <button onclick={askRun} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">Ask</button>
  </div>
  {#if answer}<div class="card mt-3 whitespace-pre-wrap p-3 text-sm">{answer}</div>{/if}
{/if}
