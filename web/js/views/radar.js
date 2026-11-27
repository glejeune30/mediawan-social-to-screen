// View: the weekly radar (home page).
import { STATUSES } from "../config.js";
import { counts } from "../scoring.js";
import { polarRadar, scatterMap } from "../charts.js";
import { esc, icon, pill, cover, fmtDate, fmtLabel, fmtMonths } from "../ui.js";
import { bindDots, median } from "./common.js";

export const title = "Radar";

export function render(el, store, ctx) {
  const { state } = store;
  const rows = state.scored;
  const c = counts(rows);
  const d = state.data;
  const flagged = d.backtest.filter((r) => r.lead_months !== null && r.lead_months !== undefined);
  const med = median(flagged.map((r) => r.lead_months));
  const books = rows.filter((r) => r.format === "Book").length;
  const top = rows.filter((r) => r.status !== "Already adapted").slice(0, 7);
  const prec = d.summary?.precision;

  el.innerHTML = `
  <div class="page-head fade-in">
    <div>
      <div class="eyebrow">Données du ${fmtDate(d.meta.snapshot)}</div>
      <h1>Le radar de la semaine</h1>
      <p class="lead">Les livres et webtoons qui accélèrent dans leur communauté alors que le grand public
      ne les connaît pas encore : les histoires à optionner avant que leurs droits deviennent chers.</p>
    </div>
  </div>

  <div class="kpis fade-in">
    <div class="kpi hot"><div class="v">${c["Act now"]}</div><div class="l">Agir maintenant</div><div class="s">histoires à traiter tout de suite</div></div>
    <div class="kpi"><div class="v" style="color:var(--plum)">${c.Prepare}</div><div class="l">Préparer</div><div class="s">à lire, droits à vérifier</div></div>
    <div class="kpi"><div class="v">${rows.length}</div><div class="l">Histoires suivies</div><div class="s">${books} livres · ${rows.length - books} webtoons</div></div>
    <div class="kpi"><div class="v">${flagged.length}/${d.backtest.length}</div><div class="l">Adaptations repérées</div><div class="s">avant le contrat · médiane ${med ? fmtMonths(med) : "—"} mois</div></div>
    <div class="kpi"><div class="v">${prec !== undefined ? Math.round(prec * 100) + " %" : "—"}</div><div class="l">Précision de la règle seule</div><div class="s">${d.summary?.controls_flagged ?? "—"} fausses alertes sur ${d.summary?.controls_total ?? "—"}</div></div>
  </div>

  <div class="grid-radar fade-in">
    <section class="card radar-card">
      <div class="card-head"><h2>Le radar</h2><span class="hint">Plus un point est proche du centre, plus son score est élevé.</span></div>
      <div class="polar-wrap">${polarRadar(rows, { sweep: state.settings.radarSweep })}</div>
      <div class="legend">${STATUSES.filter((s) => s.id !== "Already adapted" || !state.settings.hideAdapted)
        .map((s) => `<span><i style="background:${s.color}"></i>${s.label}</span>`).join("")}</div>
      ${split(rows, state.settings)}
    </section>
    <section class="card">
      <div class="card-head"><h2>Les signaux les plus forts</h2><a href="#/liste" class="link">Toute la liste ${icon("arrow", 16)}</a></div>
      <div class="toplist">
        ${top.map((r) => `<button class="toprow" data-open="${esc(r.id)}">
          ${cover(r, "cover-sm")}
          <div class="toprow-main">
            <div class="toprow-title">${esc(r.title)}</div>
            <div class="toprow-meta">${esc(r.author || "Auteur inconnu")} · ${fmtLabel(r.format)}${r.year ? ` · ${r.year}` : ""}</div>
            <div class="toprow-why">${esc(r.reasons[0])}</div>
          </div>
          <div class="toprow-side">${pill(r.status, true)}<b class="toprow-score">${r.score}</b></div>
        </button>`).join("") || `<div class="empty">Aucune histoire avec ces réglages.</div>`}
      </div>
    </section>
  </div>

  <section class="card fade-in">
    <div class="card-head"><h2>La carte : accélération et notoriété</h2>
      <span class="hint">En haut : l'histoire accélère plus que les autres de son format. À gauche : le grand public ne la connaît pas encore.</span></div>
    <div class="map-wrap">${scatterMap(rows, state.settings)}</div>
  </section>`;

  bindDots(el, store, ctx);
  el.querySelectorAll("[data-open]").forEach((b) => { b.onclick = () => ctx.openStory(b.dataset.open); });
}

/** One stacked bar per format: how many stories in each status. */
function split(rows, settings) {
  const sts = STATUSES.filter((s) => s.id !== "Already adapted" || !settings.hideAdapted);
  const line = (fmt, label) => {
    const g = rows.filter((r) => r.format === fmt);
    if (!g.length) return "";
    const c = counts(g);
    return `<div class="split-row"><span class="split-lab">${label}</span>
      <span class="split-bar">${sts.filter((s) => c[s.id]).map((s) => `<i style="flex:${c[s.id]};background:${s.color};color:${s.text}"
        title="${s.label} : ${c[s.id]}">${c[s.id]}</i>`).join("")}</span>
      <span class="split-n">${g.length}</span></div>`;
  };
  return `<div class="split">${line("Book", "Livres")}${line("Webtoon", "Webtoons")}</div>`;
}
