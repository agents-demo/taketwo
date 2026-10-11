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
export const review = (job, decision, note = "", actor = "web") =>
  api(
    `/runs/${encodeURIComponent(job)}/review/${decision}?note=${encodeURIComponent(note)}&actor=${encodeURIComponent(actor)}`,
    { method: "POST" },
  );
export const submit = (body) =>
  api("/replay/async", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
export const cancel = (id) => api(`/jobs/${encodeURIComponent(id)}/cancel`, { method: "POST" });
export const retry = (id) => api(`/jobs/${encodeURIComponent(id)}/retry`, { method: "POST" });
export const jobs = () => api("/jobs");
export const readiness = () => api("/ready");
export const scenarios = () => api("/scenarios");

export const cardScore = () => "/cards/score";
export const cardProof = (job) => `/cards/${encodeURIComponent(job)}/proof`;

export async function upload(file) {
  const form = new FormData();
  form.append("file", file);
  return api("/upload", { method: "POST", body: form });
}
