// Story Radar — start-up: load the data, build the shell, route between views.
import { NAV, PARTNER_LOGOS } from "./config.js";
import { createStore } from "./store.js";
import { icon, fmtDate, toast, hideTip } from "./ui.js";
import { openStory, closeStory } from "./views/drawer.js";
import * as radar from "./views/radar.js";
import * as liste from "./views/list.js";
import * as tests from "./views/tests.js";
import * as methode from "./views/method.js";
import * as reglages from "./views/settings.js";

// To add a page: write views/<name>.js with render(el, store, ctx), import it, add it here and in NAV.
const VIEWS = { radar, liste, tests, methode, reglages };

async function loadData() {
  const res = await fetch("data/radar.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`data/radar.json: ${res.status}`);
  return res.json();
}

function route() { return (location.hash.replace(/^#\/?/, "").split("?")[0]) || "radar"; }

async function boot() {
  const store = createStore(await loadData());
  window.__radar = store; // handy in the browser console
  const ctx = { openStory: (id) => openStory(store, id), navigate: (r) => { location.hash = `#/${r}`; } };
  const viewEl = document.getElementById("view");
  let current = null;

  document.getElementById("nav").innerHTML = NAV.map((n) =>
    `<a href="#/${n.id}" data-route="${n.id}">${icon(n.icon, 19)}<span>${n.label}</span></a>`).join("");

  const snap = () => {
    document.getElementById("snapshot").innerHTML = `Données du <b>${fmtDate(store.state.data.meta.snapshot)}</b>`;
  };

  function show() {
    const id = VIEWS[route()] ? route() : "radar";
    document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.route === id));
    hideTip();
    current = { id, api: VIEWS[id].render(viewEl, store, ctx) || null };
    document.title = `${VIEWS[id].title} · Story Radar`;
    window.scrollTo({ top: 0 });
  }

  store.subscribe((what) => {
    if (!current) return;
    if (what === "settings" && current.id === "reglages") { current.api?.update?.(); return; }
    if (what === "filters" && current.id !== "liste") return;
    current = { id: current.id, api: VIEWS[current.id].render(viewEl, store, ctx) || null };
    if (what === "data") snap();
  });

  // global search -> list view
  const search = document.getElementById("global-search");
  search.addEventListener("input", () => {
    store.setFilters({ q: search.value });
    if (route() !== "liste") location.hash = "#/liste";
  });

  // drawer
  document.querySelector("#drawer .drawer-backdrop").onclick = closeStory;
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeStory();
    if (e.key === "/" && document.activeElement !== search) { e.preventDefault(); search.focus(); }
  });

  window.addEventListener("hashchange", show);
  snap();
  show();
  partnerLogo();
  refreshButton(store);
}

/** Shows the official partner logo if its file is in assets/partners/, otherwise the name. */
async function partnerLogo() {
  const slot = document.getElementById("partner-logo");
  for (const src of PARTNER_LOGOS) {
    const ok = await new Promise((resolve) => {
      const img = new Image(); img.onload = () => resolve(true); img.onerror = () => resolve(false); img.src = src;
    });
    if (ok) { slot.innerHTML = `<img src="${src}" alt="Mediawan">`; return; }
  }
}

/** "Refresh the data" button: only when the local server (server.py) is running. */
async function refreshButton(store) {
  const btn = document.getElementById("refresh");
  let status;
  try { const r = await fetch("api/status", { cache: "no-store" }); if (!r.ok) throw 0; status = await r.json(); }
  catch { btn.hidden = true; return; }
  const idle = () => { btn.classList.remove("busy"); btn.innerHTML = `${icon("refresh", 16)}<span class="btn-label">Rafraîchir les données</span>`; };
  const busy = (step) => { btn.classList.add("busy"); btn.innerHTML = `${icon("refresh", 16)}<span class="btn-label">${step || "Collecte en cours…"}</span>`; };
  async function poll() {
    const s = await (await fetch("api/status", { cache: "no-store" })).json();
    if (s.running) { busy(s.step); setTimeout(poll, 4000); return; }
    idle();
    if (s.ok) { store.setData(await loadData()); toast("Données mises à jour"); }
    else if (s.ok === false) toast("La collecte a échoué : réessayez dans quelques minutes", 6000);
  }
  btn.onclick = async () => {
    if (!confirm("Récupérer les données de la semaine (AniList, Open Library, Wikipedia) ? Cela prend environ 10 minutes.")) return;
    await fetch("api/refresh", { method: "POST" });
    busy(); toast("Collecte lancée : vous pouvez continuer à utiliser le radar", 5000);
    setTimeout(poll, 3000);
  };
  if (status.running) { busy(status.step); poll(); } else idle();
}

boot().catch((err) => {
  console.error(err);
  document.getElementById("view").innerHTML = `<div class="card"><h2>Impossible de charger les données</h2>
    <p class="muted">Lancez l'interface avec <code>lancer_app.bat</code> (ou <code>python server.py</code>), puis ouvrez
    <code>http://localhost:8600</code>. Détail : ${String(err.message || err)}</p></div>`;
});
