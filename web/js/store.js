// Story Radar — application state: data, settings (saved in the browser), filters.
import { DEFAULT_SETTINGS } from "./config.js";
import { scoreAll, inScope } from "./scoring.js";

const KEY = "storyRadar.settings.v1";

function loadSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || "{}");
    return { ...DEFAULT_SETTINGS, ...saved };
  } catch { return { ...DEFAULT_SETTINGS }; }
}

export function createStore(data) {
  const listeners = new Set();
  const state = {
    data,
    settings: loadSettings(),
    filters: { q: "", format: "all", statuses: new Set(["Act now", "Prepare", "Watch"]), genres: new Set(),
               sort: "status", layout: "cards" },
    scored: [],
  };
  const rescore = () => {
    const all = scoreAll(state.data.stories, state.settings);
    state.scoredAll = all;
    state.scored = all.filter((r) => inScope(r, state.settings)
      && !(state.settings.hideAdapted && r.status === "Already adapted"));
  };
  const emit = (what) => listeners.forEach((fn) => fn(what));
  rescore();
  return {
    state,
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    setSettings(patch) {
      Object.assign(state.settings, patch);
      localStorage.setItem(KEY, JSON.stringify(state.settings));
      rescore(); emit("settings");
    },
    resetSettings() {
      state.settings = { ...DEFAULT_SETTINGS };
      localStorage.removeItem(KEY);
      rescore(); emit("settings");
    },
    setFilters(patch) { Object.assign(state.filters, patch); emit("filters"); },
    setData(d) { state.data = d; rescore(); emit("data"); },
    find(id) { return state.scoredAll.find((r) => r.id === id); },
  };
}

/** Stories after the filters of the list view. */
export function filtered(state) {
  const f = state.filters;
  const q = f.q.trim().toLowerCase();
  let rows = state.scored.filter((r) =>
    (f.format === "all" || r.format === f.format)
    && f.statuses.has(r.status)
    && (!f.genres.size || r.genres.some((g) => f.genres.has(g)))
    && (!q || r.title.toLowerCase().includes(q) || r.author.toLowerCase().includes(q)));
  if (f.sort === "score") rows = [...rows].sort((a, b) => b.score - a.score);
  if (f.sort === "accel") rows = [...rows].sort((a, b) => b.accel - a.accel);
  if (f.sort === "title") rows = [...rows].sort((a, b) => a.title.localeCompare(b.title, "fr"));
  return rows;
}
