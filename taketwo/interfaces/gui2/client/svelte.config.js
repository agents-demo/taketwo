import adapter from "@sveltejs/adapter-static";

/** @type {import('@sveltejs/kit').Config} */
export default {
  kit: {
    // Served under /gui2 by the FastAPI backend; SPA (single fallback page).
    paths: { base: "/gui2" },
    adapter: adapter({ fallback: "index.html" }),
    prerender: { entries: [] },
  },
};
