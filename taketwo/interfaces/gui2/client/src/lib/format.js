// Small shared helpers for the gui2 client.

export const pretty = (v) => {
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

export function statusLabel(run) {
  return run.verdict === "reproduced" && run.verified
    ? ["✅ Fixed", "text-good"]
    : run.verdict === "reproduced"
      ? ["🔧 Fix ready", "text-accent2"]
      : ["👀 Unclear", "text-muted"];
}

export function verdictTone(verdict) {
  return verdict === "reproduced" ? "text-good" : verdict === "not_reproduced" ? "text-bad" : "text-muted";
}

export const JOB_TONE = { done: "text-good", running: "text-accent2", failed: "text-bad", cancelled: "text-muted" };

export const VERDICT_FILTERS = ["All", "Reproduced", "Not reproduced", "Unclear"];
const VERDICT_VALUES = { All: null, Reproduced: "reproduced", "Not reproduced": "not_reproduced", Unclear: "unclear" };
export const filterValue = (label) => VERDICT_VALUES[label] ?? null;

export function captionFor(run) {
  if (!run) return "";
  return `TakeTwo turned a screen recording into a fix 🎬\n\`${run.job}\` — ${run.verdict} · ${run.verified ? "verified" : "unverified"}\n${run.evidence || "reproduced from the clip"}\n\n#TakeTwo #openjiuwen`;
}

export function buildTimeline(run) {
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
    }),
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
    }),
  );
  return events.sort((a, b) => (a.seq || 0) - (b.seq || 0));
}
