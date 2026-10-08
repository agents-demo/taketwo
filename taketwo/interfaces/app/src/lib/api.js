// Same-origin when served by FastAPI; CORS is enabled for the Vite dev server.
export const media = (job, name) => `/media/${encodeURIComponent(job)}/${name}`;

export async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

export const getScoreboard = () => api("/scoreboard");
export const getRuns = () => api("/runs");
export const getRun = (job) => api(`/runs/${encodeURIComponent(job)}`);
export const jobStatus = (id) => api(`/jobs/${encodeURIComponent(id)}`);
export const ask = (job, q) => api(`/runs/${encodeURIComponent(job)}/ask?q=${encodeURIComponent(q)}`);
export const review = (job, decision) =>
  api(`/runs/${encodeURIComponent(job)}/review/${decision}`, { method: "POST" });
export const submit = (body) =>
  api("/replay/async", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
