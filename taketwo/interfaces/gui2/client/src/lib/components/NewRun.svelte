<script>
  import { submit, upload, sample } from "$lib/api";

  let { onqueued } = $props();

  let video = $state("runtime/data/sample_bug_live.mov");
  let repo = $state("");
  let base_branch = $state("main");
  let app_url = $state("");
  let agentic = $state(false);
  let uploadName = $state("");
  let uploading = $state(false);

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

  async function useSample() {
    try {
      const s = await sample();
      if (s.clip) {
        video = s.clip;
        uploadName = "";
      }
      if (s.app_url) app_url = s.app_url;
    } catch {
      /* sample unavailable */
    }
  }

  async function go() {
    const { job_id } = await submit({ video_path: video, repo, base_branch, app_url, agentic });
    onqueued?.(job_id);
  }
</script>

<section class="card mt-4 p-4">
  <h2 class="font-display text-lg">New run</h2>
  <div class="mt-3 grid gap-3 sm:grid-cols-3">
    <label class="text-xs text-muted sm:col-span-3">Clip
      <input bind:value={video} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">Repository
      <input bind:value={repo} placeholder="owner/name" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">Base branch
      <input bind:value={base_branch} class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
    </label>
    <label class="text-xs text-muted">App URL
      <input bind:value={app_url} placeholder="http://localhost:8130" class="mt-1 w-full rounded-lg border-2 border-line bg-ink px-3 py-2 text-sm" />
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
  <div class="mt-4 flex gap-3">
    <button
      onclick={go}
      disabled={!video.trim()}
      class="rounded-xl bg-gradient-to-br from-accent to-accent2 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-accent/40 disabled:opacity-40"
    >Record &amp; reproduce</button>
    <button onclick={useSample} class="rounded-xl border-2 border-line px-5 py-2.5 text-sm font-semibold">Try the sample</button>
  </div>
  <p class="mt-2 text-xs text-muted">Typically ~5–15 model calls · 1–5 min, depending on the clip and the app.</p>
</section>
