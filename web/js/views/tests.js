// View: the two tests (backtest on past adaptations, false alarms on never-adapted stories).
import { timeline } from "../charts.js";
import { esc, fmtMonths, fmtDate, icon, nf } from "../ui.js";
import { median } from "./common.js";

export const title = "Tests";

/** "73,104 AniList fans" -> "73 104 fans AniList" ; "5,438 want to read" -> "5 438 « à lire »". */
function popularity(txt) {
  const m = /^([\d,]+)\s+(.*)$/.exec(txt || "");
  if (!m) return txt || "—";
  const n = nf.format(Number(m[1].replace(/,/g, "")));
  if (/AniList fans/i.test(m[2])) return `${n} fans AniList`;
  if (/want to read/i.test(m[2])) return `${n} « à lire »`;
  return `${n} ${m[2]}`;
}

const VERDICTS = {
  "False alarm": ["Fausse alerte", "v-false"],
  "No alert": ["Pas d'alerte", "v-none"],
  "Adapted after all: alert before the deal": ["Achetée en fait : alerte avant le contrat", "v-found"],
  "Adapted after all: alert around the deal": ["Achetée en fait : alerte au moment du contrat", "v-found"],
  "Adapted after all: missed": ["Achetée en fait : pas d'alerte", "v-found"],
};

export function render(el, store) {
  const d = store.state.data;
  const bt = d.backtest;
  const flagged = bt.filter((r) => r.lead_months !== null && r.lead_months !== undefined);
  const leads = flagged.map((r) => r.lead_months);
  const s = d.summary || {};
  el.innerHTML = `
  <div class="page-head fade-in"><div>
    <div class="eyebrow">Est-ce que ça marche ?</div>
    <h1>Les tests</h1>
    <p class="lead">Une règle fixée à l'avance, appliquée à de vraies adaptations, puis à des histoires
    populaires jamais adaptées pour compter les fausses alertes.</p>
  </div></div>

  <div class="kpis fade-in">
    <div class="kpi hot"><div class="v">${flagged.length}/${bt.length}</div><div class="l">Adaptations repérées</div><div class="s">avant l'annonce du contrat</div></div>
    <div class="kpi"><div class="v">${leads.length ? fmtMonths(median(leads)) : "—"} mois</div><div class="l">D'avance (médiane)</div><div class="s">de ${leads.length ? fmtMonths(Math.min(...leads)) : "—"} à ${leads.length ? fmtMonths(Math.max(...leads)) : "—"} mois</div></div>
    <div class="kpi"><div class="v" style="color:var(--coral)">${s.controls_flagged ?? "—"}/${s.controls_total ?? "—"}</div><div class="l">Fausses alertes</div><div class="s">histoires jamais adaptées qui ont sonné</div></div>
    <div class="kpi"><div class="v">${s.precision !== undefined ? Math.round(s.precision * 100) + " %" : "—"}</div><div class="l">Précision</div><div class="s">alertes suivies d'un contrat</div></div>
  </div>

  <section class="card fade-in">
    <div class="card-head"><h2>Test 1 : le radar aurait-il vu venir ces adaptations ?</h2>
      <span class="hint">Règle : les recherches Google sur 3 mois au moins doublées par rapport aux 6 mois d'avant, deux mois de suite.</span></div>
    ${timeline(bt)}
    <div class="legend" style="justify-content:flex-start">
      <span><i style="background:var(--coral)"></i>Alerte du radar</span>
      <span><i style="background:#fff;border:2.5px solid var(--plum);width:12px;height:12px"></i>Première page Wikipedia</span>
      <span><i style="background:var(--ink)"></i>Contrat d'adaptation annoncé</span>
    </div>
  </section>

  <section class="card fade-in">
    <div class="card-head"><h2>Test 2 : sonne-t-il aussi pour rien ?</h2>
      <span class="hint">16 histoires populaires sans adaptation connue, choisies avant de regarder leurs courbes.</span></div>
    <div class="callout" style="margin-bottom:16px"><b>Ce qu'on en retient :</b> la hausse des recherches repère
      les succès, mais elle sonne pour presque toutes les histoires populaires. C'est un premier filtre, pas une
      décision : d'où le score à trois questions et la vérification des droits à la main. Bonus : ${s.controls_found_adapted ?? 4}
      « témoins » avaient en fait été achetés, dont la série Twisted, repérée environ trois ans avant le contrat Netflix.</div>
    <div class="table-wrap" style="box-shadow:none;border:1px solid var(--line)"><table>
      <thead><tr><th>Histoire</th><th>Format</th><th>Popularité</th><th>Alerte</th><th>Verdict</th><th>Contrat trouvé</th></tr></thead>
      <tbody>${d.controls.map((r) => {
        const [lab, cls] = VERDICTS[r.verdict] || [r.verdict, ""];
        return `<tr><td><b>${esc(r.title)}</b></td><td>${r.format === "Book" ? "Livre" : "Webtoon"}</td>
          <td class="muted nowrap">${esc(popularity(r.popularity))}</td>
          <td class="nowrap">${r.radar_alert ? esc(fmtDate(r.radar_alert, { month: "short", year: "numeric" })) : "—"}</td>
          <td class="verdict ${cls}">${esc(lab)}</td>
          <td>${r.deal ? `${esc(r.deal)} ${r.source_url ? `<a href="${esc(r.source_url)}" target="_blank" rel="noopener">${icon("external", 14)}</a>` : ""}` : ""}</td></tr>`;
      }).join("")}</tbody></table></div>
  </section>`;
}
