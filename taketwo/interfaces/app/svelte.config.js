import adapter from "@sveltejs/adapter-static";

/** @type {import('@sveltejs/kit').Config} */
export default {
  kit: {
    // Served under /app by the FastAPI backend; SPA (single fallback page).
    paths: { base: "/app" },
    adapter: adapter({ fallback: "index.html" }),
    prerender: { entries: [] },
  },
};
