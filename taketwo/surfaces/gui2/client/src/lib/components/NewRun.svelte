<script>
  import { onMount } from "svelte";
  import { submit, upload, scenarios } from "$lib/api";

  let { onqueued } = $props();

  let tab = $state("demo"); // "demo" | "mine"

  let demos = $state([]);
  let chosen = $state("");

  let video = $state("");
  let repo = $state("");
  let base_branch = $state("main");
  let app_url = $state("");
  let agentic = $state(false);
  let uploadName = $state("");
  let uploading = $state(false);
  let busy = $state(false);

  onMount(async () => {
    try {
      demos = (await scenarios()).scenarios;
      if (demos.length) chosen = demos[0].name;
    } catch {
      demos = [];
    }
  });

  async function pickFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    uploading = true;
    try {
      const res = await upload(file);
      video = res.path;
      uploadName = res.name;
    } catch (err) {
      alert(`Upload failed: ${err}`);
    } finally {
      uploading = false;
    }
  }

  async function runDemo() {
    const demo = demos.find((d) => d.name === chosen);
    if (!demo) return;
    busy = true;
    try {
      const { job_id } = await submit({
        video_path: demo.clip,
        repo: "",
        base_branch: "main",
        app_url: demo.app_url,
        agentic: false,
      });
      onqueued?.(job_id);
    } finally {
      busy = false;
    }
  }

  async function runMine() {
    busy = true;
    try {
      const { job_id } = await submit({ video_path: video, repo, base_branch, app_url, agentic });
      onqueued?.(job_id);
    } finally {
      busy = false;
    }
  }

  const tabClass = (active) =>
    `rounded-full border-2 border-line px-4 py-1.5 text-sm font-semibold ${active ? "bg-surface text-app" : "text-muted"}`;
</script>

<section class="card mt-4 p-4">
  <h2 class="font-display text-lg">New run</h2>
  <p class="mt-1 text-xs text-muted">Reproduce a bug from a recording — start from a demo, or use your own bug.</p>

  <div class="mt-3 flex gap-2">
    <button onclick={() => (tab = "demo")} class={tabClass(tab === "demo")}>Try a demo</button>
    <button onclick={() => (tab = "mine")} class={tabClass(tab === "mine")}>Your own bug</button>
  </div>

  {#if tab === "demo"}
    <div class="mt-4">
      <label class="block text-xs text-muted">Bundled demo
        <select bind:value={chosen} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm">
          {#each demos as d (d.name)}<option value={d.name}>{d.reproducible ? "✅ " : "⚠ "}{d.title}</option>{/each}
        </select>
      </label>
      <button
        onclick={runDemo}
        disabled={!demos.length || busy}
        class="mt-3 rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/40 disabled:opacity-40"
      >Run this demo</button>
      {#if !demos.length}
        <p class="mt-2 text-xs text-bad">No demos found under <code>demos/scenarios/</code>.</p>
      {:else}
        <p class="mt-2 text-xs text-muted">✅ reproduces deterministically · the demo app is served for you.</p>
      {/if}
    </div>
  {:else}
    <div class="mt-4 grid gap-3 sm:grid-cols-3">
      <label class="text-xs text-muted sm:col-span-3">Clip
        <input bind:value={video} placeholder="upload a recording, or paste a path" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
      </label>
      <label class="text-xs text-muted">Repository
        <input bind:value={repo} placeholder="owner/name (optional)" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
      </label>
      <label class="text-xs text-muted">Base branch
        <input bind:value={base_branch} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
      </label>
      <label class="text-xs text-muted">App URL
        <input bind:value={app_url} placeholder="http://localhost:3000" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
      </label>
    </div>
    <div class="mt-3 flex flex-wrap items-center gap-3">
      <label class="cursor-pointer rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">
        Upload clip
        <input type="file" class="hidden" onchange={pickFile} accept=".mp4,.mov,.webm,.mkv,.png,.jpg,.jpeg,.webp" />
      </label>
      <span class="text-xs text-muted">{uploading ? "uploading…" : uploadName || "or paste a path above"}</span>
      <label class="ml-auto flex items-center gap-2 text-xs text-muted">
        <input type="checkbox" bind:checked={agentic} /> Agentic (let the model drive)
      </label>
    </div>
    <button
      onclick={runMine}
      disabled={!video.trim() || busy}
      class="mt-4 rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/40 disabled:opacity-40"
    >Record &amp; reproduce</button>
    <p class="mt-2 text-xs text-muted">A repository is only needed for the fix + proof.</p>
  {/if}

  <p class="mt-3 text-xs text-muted">Typically ~5–15 model calls · 1–5 min.</p>
</section>
