// View: how the radar works, with the values of the current settings.
import { SOURCES, STATUSES } from "../config.js";
import { activeExtensions } from "../extensions/index.js";
import { esc, pill, nf } from "../ui.js";

export const title = "Méthode";

const SRC_LABEL = { live: ["Branchée", "src-live"], ready: ["Code prêt, clé à créer", "src-ready"], planned: ["Prévue", "src-planned"] };

export function render(el, store) {
  const s = store.state.settings;
  const sum = Math.max(1, s.wAccel + s.wUnaware + s.wSpread);
  const w = (v) => (v / sum).toFixed(2).replace(".", ",");
  el.innerHTML = `
  <div class="page-head fade-in"><div>
    <div class="eyebrow">Comment ça marche</div>
    <h1>La méthode</h1>
    <p class="lead">Chaque semaine, pour chaque histoire, le radar pose trois questions. Les valeurs ci-dessous
    suivent vos réglages.</p>
  </div></div>

  <div class="three fade-in">
    <div class="qcard"><div class="qnum">1</div><h3>Le buzz accélère-t-il ?</h3>
      <div class="muted">Webtoons : croissance des fans AniList sur 90 jours. Livres : ajouts de lecteurs Open Library
      sur 24 h comparés à la semaine d'avant. Part de la croissance : <b>${s.accelGrowthShare} %</b>, le reste pour
      le volume d'activité. Chaque histoire est classée parmi celles de son format.</div></div>
    <div class="qcard"><div class="qnum">2</div><h3>Se propage-t-il ?</h3>
      <div class="muted">Oui si sa page Wikipedia a moins de <b>${s.spreadPageAgeMonths} mois</b>, ou si ses vues
      ont augmenté d'au moins <b>${s.spreadGrowthPct} %</b> (3 derniers mois contre les 6 d'avant).</div></div>
    <div class="qcard"><div class="qnum">3</div><h3>Le grand public l'ignore-t-il encore ?</h3>
      <div class="muted">Pas de page Wikipedia en anglais, ou moins de <b>${nf.format(s.unawareMaxViews)} vues par mois</b>.
      La note suit une échelle logarithmique : 100 vues = 0, 10 000 = 0,5, 1 million = 1.</div></div>
  </div>

  <section class="card fade-in" style="margin-top:20px">
    <div class="card-head"><h2>Le score et les statuts</h2></div>
    <div class="formula">Score = 100 × ( <b>${w(s.wAccel)}</b> × accélération + <b>${w(s.wUnaware)}</b> × méconnaissance + <b>${w(s.wSpread)}</b> × diffusion )${
      activeExtensions(s).some((e) => e.points) ? ` <span class="formula-ext">+ points des extensions : ${activeExtensions(s).filter((e) => e.points).map((e) => esc(e.label)).join(", ")}</span>` : ""}</div>
    <div class="table-wrap" style="box-shadow:none;border:1px solid var(--line)"><table><tbody>
      <tr><td>${pill("Already adapted")}</td><td>Un anime est listé sur AniList, ou Wikipedia signale une adaptation (série, film).</td></tr>
      <tr><td>${pill("Act now")}</td><td>Dans les <b>${100 - s.actNowPct} %</b> qui accélèrent le plus dans leur format, et le grand public l'ignore encore${s.actNowNeedsSpread ? ", et l'histoire se propage" : ""}.</td></tr>
      <tr><td>${pill("Prepare")}</td><td>Dans les <b>${100 - s.preparePct} %</b> qui accélèrent le plus.</td></tr>
      <tr><td>${pill("Watch")}</td><td>Toutes les autres histoires suivies.</td></tr>
    </tbody></table></div>
    <p class="muted" style="margin-bottom:0">Le score sert à classer, le statut dit quoi faire. ${STATUSES.map((x) => `<b>${esc(x.label)}</b> : ${esc(x.help)}`).join(" ")}</p>
  </section>

  <section class="card fade-in">
    <div class="card-head"><h2>Les sources</h2><span class="hint">Données publiques uniquement, aucune donnée personnelle.</span></div>
    <div class="table-wrap" style="box-shadow:none;border:1px solid var(--line)"><table>
      <thead><tr><th>Source</th><th>Ce qu'elle nous dit</th><th>Accès</th><th>État</th></tr></thead>
      <tbody>${SOURCES.map(([n, what, access, st]) => `<tr><td><b>${esc(n)}</b></td><td>${esc(what)}</td>
        <td class="muted">${esc(access)}</td><td><span class="src-status ${SRC_LABEL[st][1]}">${SRC_LABEL[st][0]}</span></td></tr>`).join("")}</tbody>
    </table></div>
  </section>

  <section class="card fade-in">
    <div class="card-head"><h2>Les limites</h2></div>
    <ul class="reasons">
      <li>AniList penche vers l'action et la fantasy coréennes ; Open Library est une petite communauté anglophone.</li>
      <li>TikTok n'a pas d'accès public pour ce type de projet : BookTok est capté indirectement.</li>
      <li>AniList ne liste que les animes, et la détection automatique a raté 4 contrats sur 16 : les droits se vérifient à la main.</li>
      <li>Le classement est relatif : le haut de la liste est le signal le plus fort de la semaine, pas une garantie de succès.</li>
    </ul>
  </section>`;
}
