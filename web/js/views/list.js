// View: the full watchlist, with filters, as cards or as a table.
import { STATUSES } from "../config.js";
import { filtered } from "../store.js";
import { esc, icon, pill, cover, coverArt, fmtLabel, scoreBar } from "../ui.js";
import { signalShort, mainstreamShort } from "./common.js";

export const title = "Liste";

export function render(el, store, ctx) {
  const { state } = store;
  const f = state.filters;
  const genreCount = {};
  state.scored.forEach((r) => r.genres.forEach((g) => { genreCount[g] = (genreCount[g] || 0) + 1; }));
  const genres = Object.entries(genreCount).sort((a, b) => b[1] - a[1]).slice(0, 14).map(([g]) => g);
  const statuses = STATUSES.filter((s) => s.id !== "Already adapted" || !state.settings.hideAdapted);

  el.innerHTML = `
  <div class="page-head fade-in"><div>
    <div class="eyebrow">Toutes les histoires suivies</div>
    <h1>La liste</h1>
    <p class="lead">Filtrez, triez, et cliquez sur une histoire pour voir pourquoi elle a ce statut.</p>
  </div></div>
  <div class="toolbar">
    <div class="seg" id="f-format">
      ${[["all", "Tout"], ["Book", "Livres"], ["Webtoon", "Webtoons"]].map(([v, l]) =>
        `<button data-v="${v}" class="${f.format === v ? "on" : ""}">${l}</button>`).join("")}
    </div>
    <div id="f-status" style="display:flex;gap:8px;flex-wrap:wrap">
      ${statuses.map((s) => `<span class="chip ${f.statuses.has(s.id) ? "on" : ""}" data-v="${esc(s.id)}">
        <i style="background:${s.color}"></i>${s.label}</span>`).join("")}
    </div>
    <div class="grow"></div>
    <select id="f-sort" aria-label="Trier">
      ${[["status", "Trier : statut puis score"], ["score", "Trier : score"], ["accel", "Trier : accélération"], ["title", "Trier : titre"]]
        .map(([v, l]) => `<option value="${v}" ${f.sort === v ? "selected" : ""}>${l}</option>`).join("")}
    </select>
    <div class="seg" id="f-layout">
      <button data-v="cards" class="${f.layout === "cards" ? "on" : ""}" title="Cartes">${icon("grid", 16)}</button>
      <button data-v="table" class="${f.layout === "table" ? "on" : ""}" title="Tableau">${icon("rows", 16)}</button>
    </div>
  </div>
  <div class="genres" id="f-genres">
    ${genres.map((g) => `<span class="chip ${f.genres.has(g) ? "on" : ""}" data-v="${esc(g)}">${esc(g)}</span>`).join("")}
  </div>
  <div id="results"></div>`;

  const results = el.querySelector("#results");
  const draw = () => {
    const rows = filtered(state);
    results.innerHTML = `<div class="count">${rows.length} histoire${rows.length > 1 ? "s" : ""}</div>` + (rows.length
      ? (state.filters.layout === "table" ? table(rows) : cards(rows))
      : `<div class="empty">Aucune histoire ne correspond à ces filtres.</div>`);
    results.querySelectorAll("[data-open]").forEach((n) => { n.onclick = () => ctx.openStory(n.dataset.open); });
  };
  draw();

  el.querySelectorAll("#f-format button").forEach((b) => { b.onclick = () => { store.setFilters({ format: b.dataset.v }); }; });
  el.querySelectorAll("#f-layout button").forEach((b) => { b.onclick = () => { store.setFilters({ layout: b.dataset.v }); }; });
  el.querySelector("#f-sort").onchange = (e) => store.setFilters({ sort: e.target.value });
  el.querySelectorAll("#f-status .chip").forEach((c) => { c.onclick = () => {
    const s = new Set(state.filters.statuses);
    s.has(c.dataset.v) ? s.delete(c.dataset.v) : s.add(c.dataset.v);
    store.setFilters({ statuses: s });
  }; });
  el.querySelectorAll("#f-genres .chip").forEach((c) => { c.onclick = () => {
    const s = new Set(state.filters.genres);
    s.has(c.dataset.v) ? s.delete(c.dataset.v) : s.add(c.dataset.v);
    store.setFilters({ genres: s });
  }; });
  return { update: () => render(el, store, ctx), updateResults: draw };
}

function cards(rows) {
  return `<div class="cards">${rows.map((r) => `
    <button class="scard fade-in" data-open="${esc(r.id)}">
      <div class="scard-cover">${coverArt(r)}${pill(r.status, true)}<div class="scard-score">${r.score}<small>/100</small></div></div>
      <div class="scard-body">
        <div class="scard-title">${esc(r.title)}</div>
        <div class="scard-meta">${esc(r.author || "Auteur inconnu")} · ${fmtLabel(r.format)}${r.year ? ` · ${r.year}` : ""}</div>
        <div class="scard-why">${esc(r.reasons[0])}</div>
        <div class="scard-tags">${r.genres.slice(0, 3).map((g) => `<span class="tag">${esc(g)}</span>`).join("")}</div>
      </div>
    </button>`).join("")}</div>`;
}

function table(rows) {
  return `<div class="table-wrap"><table>
    <thead><tr><th></th><th>Histoire</th><th>Statut</th><th>Score</th><th>Communauté</th><th>Grand public</th><th>Adaptation</th></tr></thead>
    <tbody>${rows.map((r) => `<tr class="clickable" data-open="${esc(r.id)}">
      <td style="width:58px">${cover(r, "cover-sm")}</td>
      <td><b>${esc(r.title)}</b><div class="muted" style="font-size:12.5px">${esc(r.author || "Auteur inconnu")} · ${fmtLabel(r.format)}</div></td>
      <td>${pill(r.status, true)}</td>
      <td style="white-space:nowrap">${scoreBar(r.score)}</td>
      <td>${esc(signalShort(r))}</td>
      <td>${esc(mainstreamShort(r))}</td>
      <td class="muted">${esc(r.adaptation || "Aucune listée")}</td>
    </tr>`).join("")}</tbody></table></div>`;
}
