// The story page, opened as a panel on the right.
import { STATUS } from "../config.js";
import { lineChart, barChart, scoreRing } from "../charts.js";
import { esc, icon, pill, cover, fmtLabel } from "../ui.js";

const panel = () => document.querySelector("#drawer .drawer-panel");

export function openStory(store, id) {
  const r = store.find(id);
  if (!r) return;
  const s = store.state.settings;
  const ser = store.state.data.series[id] || {};
  const st = STATUS[r.status];
  const sum = Math.max(1, s.wAccel + s.wUnaware + s.wSpread);
  const parts = [
    ["Accélération", r.accel, s.wAccel / sum, "#FF5A4E", `${Math.round(r.accel * 100)}e centile de son format`],
    ["Méconnaissance", r.unaware, s.wUnaware / sum, "#5B3F8C", r.s.wikiViews == null ? "pas de page Wikipedia" : "selon les vues Wikipedia"],
    ["Diffusion", r.spreading, s.wSpread / sum, "#8E74C2", r.spreading ? "page récente ou vues en hausse" : "pas de hausse visible"],
  ];
  let community = "";
  if (r.format === "Webtoon" && ser.fans?.length) {
    community = `<div><h3>Fans sur AniList</h3>${lineChart(ser.fans, { label: "Fans sur AniList" })}</div>`;
  } else if (ser.reader_activity?.length) {
    community = `<div><h3>Activité des lecteurs sur Open Library</h3>${barChart(
      ser.reader_activity.map(([l, v]) => [l, v, l.startsWith("Average") ? "Jour moyen (semaine d'avant)" : "Dernières 24 h"]),
      { color: "#B7AFCB", highlightLast: true, label: "Activité des lecteurs" })}</div>`;
  }
  let wiki = `<div class="callout"><b>Pas encore de page Wikipedia en anglais.</b> Le grand public ne la connaît pas :
    Heartstopper non plus n'en avait pas quand Netflix a commandé la série.</div>`;
  if (ser.wikipedia_views?.length) {
    const pts = ser.wikipedia_views.map(([x, v]) => [x, v, new Date(x).toLocaleDateString("fr-FR", { month: "short", year: "2-digit" })]);
    wiki = `<div><h3>Vues Wikipedia par mois</h3>${barChart(pts, { every: 4, label: "Vues Wikipedia" })}</div>`;
  }

  panel().innerHTML = `
    <div class="d-hero">
      ${r.cover ? `<img class="cover-big" src="${esc(r.cover)}" alt="" referrerpolicy="no-referrer">` : cover(r, "cover-big cover-ph")}
      <div style="min-width:0">
        ${pill(r.status)}
        <h2>${esc(r.title)}</h2>
        <div class="d-meta">${esc(r.author || "Auteur inconnu")} · ${fmtLabel(r.format)}${r.year ? ` · première publication ${r.year}` : ""}</div>
        <div class="d-tags">${r.genres.map((g) => `<span class="tag">${esc(g)}</span>`).join("")}</div>
      </div>
      <button class="d-close" aria-label="Fermer">${icon("close", 18)}</button>
    </div>
    <div class="d-body">
      <div class="d-score">${scoreRing(r.score, st.color)}
        <div><div class="muted" style="font-size:13px">Score d'émergence${r.extras.length
          ? ` · dont ${r.score - r.baseScore >= 0 ? "+" : ""}${r.score - r.baseScore} par les extensions` : ""}</div>
        <div class="todo"><b>Que faire :</b> ${esc(st.help)}</div></div></div>
      <div><h3>Pourquoi ce statut</h3><ul class="reasons">${r.reasons.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
      <div class="parts"><h3>D'où vient le score</h3>
        ${parts.map(([lab, val, w, col, note]) => `<div class="part"><span>${lab}<div class="muted" style="font-size:11.5px">${esc(note)}</div></span>
          <span class="bar"><i style="width:${Math.round(val * 100)}%;background:${col}"></i></span>
          <span class="pts">+${Math.round(100 * w * val)}</span></div>`).join("")}
        ${r.extras.map((x) => `<div class="part part-ext"><span>${esc(x.label)}<div class="muted" style="font-size:11.5px">${esc(x.reason)}</div></span>
          <span class="ext-badge">${icon("blocks", 14)} extension</span>
          <span class="pts">${x.points > 0 ? "+" : ""}${x.points}</span></div>`).join("")}
      </div>
      ${community}
      ${wiki}
      <div class="d-links">
        <a class="btn" href="${esc(r.src)}" target="_blank" rel="noopener">${icon("external", 16)} ${r.format === "Webtoon" ? "Page AniList" : "Page Open Library"}</a>
        ${r.wikiUrl ? `<a class="btn" href="${esc(r.wikiUrl)}" target="_blank" rel="noopener">${icon("external", 16)} Wikipedia</a>` : ""}
        <a class="btn" href="https://www.google.com/search?q=${encodeURIComponent(`"${r.title}" adaptation rights`)}" target="_blank" rel="noopener">${icon("search", 16)} Chercher les droits</a>
      </div>
    </div>`;
  const drawer = document.getElementById("drawer");
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
  panel().querySelector(".d-close").onclick = closeStory;
  panel().scrollTop = 0;
}

export function closeStory() {
  const drawer = document.getElementById("drawer");
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
}
