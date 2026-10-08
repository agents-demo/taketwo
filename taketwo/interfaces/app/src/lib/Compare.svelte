<script>
  let { before, after } = $props();
  let pct = $state(50);
  let el;
  let axis = null;
  let start = null;

  const clamp = (v) => Math.max(0, Math.min(100, v));
  function at(clientX) {
    const r = el.getBoundingClientRect();
    pct = clamp(((clientX - r.left) / r.width) * 100);
  }
  function down(e) {
    axis = null;
    start = { x: e.clientX, y: e.clientY };
  }
  function move(e) {
    if (!start) return;
    const dx = e.clientX - start.x;
    const dy = e.clientY - start.y;
    if (axis === null) {
      if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
      axis = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    }
    if (axis === "x") at(e.clientX);
  }
  const up = () => {
    start = null;
    axis = null;
  };
</script>

<div
  bind:this={el}
  onpointerdown={down}
  onpointermove={move}
  onpointerup={up}
  onpointercancel={up}
  class="relative h-full w-full cursor-ew-resize touch-pan-y select-none overflow-hidden"
>
  <img src={after} alt="after the fix" class="absolute inset-0 h-full w-full object-cover" />
  <img
    src={before}
    alt="before the fix"
    class="absolute inset-0 h-full w-full object-cover"
    style="clip-path: inset(0 {100 - pct}% 0 0)"
  />
  <div
    class="absolute top-0 bottom-0 w-[3px] bg-accent2 shadow-[0_0_24px_rgba(167,139,250,0.9)]"
    style="left: {pct}%"
  ></div>
</div>
