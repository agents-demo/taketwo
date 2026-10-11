<script>
  import { ask } from "$lib/api";

  let { job } = $props();
  let q = $state("");
  let messages = $state([]);
  let sending = $state(false);

  // A different run resets the conversation.
  $effect(() => {
    if (job) messages = [];
  });

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
</script>

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
