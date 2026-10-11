<script>
  import { media, cardProof } from "$lib/api";

  let { run, caption } = $props();
  let copied = $state(false);

  async function copyCaption() {
    try {
      await navigator.clipboard.writeText(caption);
      copied = true;
      setTimeout(() => (copied = false), 1500);
    } catch {
      /* clipboard blocked */
    }
  }
</script>

<h2 class="mt-6 font-display text-lg">Share proof</h2>
<div class="mt-2 flex flex-wrap items-center gap-2">
  {#if run.has_video}
    <a href={media(run.job, "proof.mp4")} download class="rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">Download proof video</a>
  {/if}
  <a href={cardProof(run.job)} target="_blank" rel="noreferrer" class="rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">Proof card (PNG)</a>
  <button onclick={copyCaption} class="rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold">{copied ? "Copied ✓" : "Copy caption"}</button>
</div>
<pre class="card mt-2 whitespace-pre-wrap p-3 text-xs text-muted">{caption}</pre>
