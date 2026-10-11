<script>
  import { page } from "$app/stores";
  import { base } from "$app/paths";
  import { getRun, review, ask, media, cardProof } from "$lib/api";
  import Compare from "$lib/Compare.svelte";

  let run = $state(null);
  let error = $state("");
  let note = $state("");
  let actor = $state("web");
  let q = $state("");
  let messages = $state([]);
  let sending = $state(false);
  let copied = $state(false);
  const job = $derived($page.url.searchParams.get("job"));

  async function load() {
    if (!job) return;
    try {
      run = await getRun(job);
      messages = [];
    } catch (e) {
      error = String(e);
    }
  }
  async function decide(decision) {
    await review(job, decision, note, actor);
    await load();
  }
  async function askRun() {
    if (!q.trim() || sending) return;
    const question = q;
    q = "";
    messages = [...messages, { role: "user", content: question }];
    sending = true;
    try {
      const a = (await ask(job, question)).answer;
      messages = [...messages, { role: "assistant", content: a }];
    } catch {
      messages = [...messages, { role: "assistant", content: "Couldn't answer that." }];
    } finally {
      sending = false;
    }
  }
  async function copyCaption() {
    try {
      await navigator.clipboard.writeText(caption);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {
      /* clipboard blocked */
    }
  }
  $effect(() => {
    job;
    load();
  });

  const pretty = (v) => {
    if (v == null || v === "") return "{}";
    if (typeof v === "string") {
      try {
        return JSON.stringify(JSON.parse(v), null, 2);
      } catch {
        return v;
      }
    }
    return JSON.stringify(v, null, 2);
  };
  const timeline = $derived.by(() => {
    if (!run) return [];
    const events = [];
    (run.calls || []).forEach((c, i) =>
      events.push({
        kind: "model",
        seq: c.seq ?? i,
        label: c.label || "call",
        model: c.model || "",
        probe: c.probe === true,
        prompt: c.prompt_tokens,
        completion: c.completion_tokens,
        seconds: c.seconds,
        offered: c.tools || [],
        requested: (c.requested || []).map((r) => ({ name: r.name || "", arguments: pretty(r.arguments) })),
        messages: c.input || [],
        output: c.output || "",
      })
    );
    (run.tools || []).forEach((t, i) =>
      events.push({
        kind: "tool",
        seq: t.seq ?? 1000 + i,
        label: t.name || "tool",
        seconds: t.seconds,
        args: pretty(t.arguments),
        result: t.result || "",
        error: t.error || "",
      })
    );
    return events.sort((a, b) => (a.seq || 0) - (b.seq || 0));
  });

  const pipe = $derived(run?.timeline || []);
  const pipeMax = $derived(Math.max(0.001, ...pipe.map((t) => Number(t.seconds) || 0)));
  const verdictTone = $derived(
    run?.verdict === "reproduced" ? "text-good" : run?.verdict === "not_reproduced" ? "text-bad" : "text-muted",
  );
  const caption = $derived(
    run
      ? `TakeTwo turned a screen recording into a fix 🎬\n\`${run.job}\` — ${run.verdict} · ${run.verified ? "verified" : "unverified"}\n${run.evidence || "reproduced from the clip"}\n\n#TakeTwo #openjiuwen`
      : "",
  );
</script>

{#if error}
  <p class="text-bad">{error}</p>
{:else if !run}
  <p class="text-muted">Loading…</p>
{:else}
  <div class="flex items-center gap-3">
    <h1 class="font-display text-2xl font-bold">{run.job}</h1>
    <span class="rounded-full border-2 border-line px-3 py-1 text-xs">{run.review.replace("_", " ")}</span>
    <a href={`${base}/`} class="ml-auto text-sm text-muted hover:text-white">← Runs</a>
  </div>
  <div class="mt-1 flex flex-wrap items-center gap-2 text-xs">
    <span class="rounded-full border-2 border-line px-2 py-0.5 {verdictTone}">{run.verdict?.replace("_", " ")}</span>
    <span class="rounded-full border-2 border-line px-2 py-0.5 {run.verified ? "text-good" : "text-muted"}">{run.verified ? "verified" : "unverified"}</span>
    <span class="rounded-full border-2 border-line px-2 py-0.5 {run.grounded ? "text-accent2" : "text-muted"}">{run.grounded ? "grounded" : "ungrounded"}</span>
  </div>
  <p class="mt-1 text-xs text-muted">{[run.when, run.base_branch, run.video_name].filter(Boolean).join(" · ")}</p>
  {#if run.evidence}<p class="mt-1 text-sm text-muted">Evidence: {run.evidence}</p>{/if}

  <div class="card mt-4 h-[320px] overflow-hidden">
    {#if run.has_video}
      <video src={media(run.job, "proof.mp4")} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
    {:else if run.has_before && run.has_after}
      <Compare before={media(run.job, "before.png")} after={media(run.job, "after.png")} />
    {:else if run.source}
      <video src={media(run.job, run.source)} autoplay loop muted playsinline class="h-full w-full object-cover"></video>
    {:else if run.has_before}
      <img src={media(run.job, "before.png")} alt="captured frame" class="h-full w-full object-cover" />
    {:else}
      <div class="grid h-full place-items-center text-muted">no clip</div>
    {/if}
  </div>
  {#if !(run.has_before && run.has_after) && !run.has_video}
    <p class="mt-1 text-xs text-muted">Source recording — no proof yet (this run didn't reproduce).</p>
  {/if}

  <div class="mt-4 grid grid-cols-5 gap-3">
    <div class="card p-3"><div class="text-xs text-muted">Score</div><div class="font-display text-2xl">{run.score}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Grounded</div><div class="font-display text-lg">{run.grounded ? "yes" : "no"}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Verified</div><div class="font-display text-lg">{run.verified ? "yes" : "no"}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Steps</div><div class="font-display text-2xl">{(run.steps || []).length}</div></div>
    <div class="card p-3"><div class="text-xs text-muted">Tokens</div><div class="font-display text-2xl">{(run.usage?.total_tokens ?? 0).toLocaleString()}</div></div>
  </div>

  <h2 class="mt-6 font-display text-lg">Share proof</h2>
  <div class="mt-2 flex flex-wrap items-center gap-2">
    {#if run.has_video}
      <a href={media(run.job, "proof.mp4")} download class="rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">Download proof video</a>
    {/if}
    <a href={cardProof(run.job)} target="_blank" rel="noreferrer" class="rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">Proof card (PNG)</a>
    <button onclick={copyCaption} class="rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">{copied ? "Copied ✓" : "Copy caption"}</button>
  </div>
  <pre class="card mt-2 whitespace-pre-wrap p-3 text-xs text-muted">{caption}</pre>

  <h2 class="mt-6 font-display text-lg">Fix</h2>
  <pre class="card mt-2 overflow-x-auto p-3 text-xs">{run.diff || "(no diff proposed)"}</pre>
  {#if run.culprits?.length}
    <p class="mt-1 text-xs text-muted">Suspected cause: {run.culprits.slice(0, 3).join(", ")}</p>
  {/if}
  {#if run.test}
    <h3 class="mt-3 text-sm font-semibold">Regression test</h3>
    <pre class="card mt-1 overflow-x-auto p-3 text-xs">{run.test}</pre>
  {/if}

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
    <h3 class="mt-4 text-sm font-semibold">Console</h3>
    <pre class="card mt-1 overflow-auto p-3 text-xs">{run.console.join("\n")}</pre>
  {/if}
  {#if run.question}
    <p class="mt-3 rounded-lg border-2 border-line bg-ink p-2 text-xs text-muted">{run.question}</p>
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
  {/if}

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

  <h2 class="mt-6 font-display text-lg">Review</h2>
  <p class="mt-1 text-xs text-muted">Reviewing as</p>
  <div class="mt-2 flex gap-2">
    <input bind:value={note} placeholder="why approve or send back" class="flex-1 rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    <input bind:value={actor} placeholder="you" class="w-40 rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
  </div>
  <div class="mt-3 flex gap-3">
    <button
      onclick={() => decide("approved")}
      disabled={!run.verified}
      class="rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
    >Approve &amp; merge</button>
    <button onclick={() => decide("changes_requested")} class="rounded-xl border-2 border-line px-5 py-2.5 text-sm font-semibold">Request changes</button>
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

  <h2 class="mt-6 font-display text-lg">Ask about this run</h2>
  <div class="mt-2 space-y-2">
    {#each messages as m}
      <div class="card whitespace-pre-wrap p-3 text-sm {m.role === 'user' ? 'text-app' : 'text-muted'}">{m.content}</div>
    {/each}
    {#if sending}<div class="card p-3 text-sm text-muted">…</div>{/if}
  </div>
  <div class="mt-2 flex gap-2">
    <input bind:value={q} onkeydown={(e) => e.key === "Enter" && askRun()} placeholder="was this a real fix?" class="flex-1 rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    <button onclick={askRun} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">Ask</button>
  </div>
{/if}
