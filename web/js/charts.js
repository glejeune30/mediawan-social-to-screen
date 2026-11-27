// Story Radar — hand-made SVG charts (no library): polar radar, map, line, bars, timeline, ring.
import { STATUS, PALETTE } from "./config.js";
import { awareness, k } from "./scoring.js";
import { esc, nf, fmtMonths } from "./ui.js";

const hash = (s) => { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
const niceStep = (max, n = 4) => {
  const raw = max / n; const p = 10 ** Math.floor(Math.log10(raw || 1));
  return [1, 2, 2.5, 5, 10].map((m) => m * p).find((s) => s >= raw) || p * 10;
};

/** The radar: closer to the centre = higher score. Books on the left, webtoons on the right. */
export function polarRadar(rows, { sweep = true } = {}) {
  const S = 600, cx = 300, cy = 300, R = 250;
  const rad = (score) => R * (0.08 + 0.92 * (1 - score / 100));
  const pos = (r) => {
    const t = (hash(r.id) % 997) / 997;
    const deg = (r.format === "Webtoon" ? 14 : 194) + t * 152;
    const a = (deg * Math.PI) / 180, d = rad(r.score);
    return [cx + d * Math.sin(a), cy - d * Math.cos(a)];
  };
  const rings = [80, 60, 40, 20].map((s) => `
    <circle cx="${cx}" cy="${cy}" r="${rad(s)}" class="ring"/>
    <text x="${cx + 6}" y="${cy - rad(s) + 14}" class="ring-label">${s}</text>`).join("");
  const a2 = (52 * Math.PI) / 180;
  const wedge = `M${cx},${cy} L${cx},${cy - R} A${R},${R} 0 0 1 ${cx + R * Math.sin(a2)},${cy - R * Math.cos(a2)} Z`;
  const dots = [...rows].sort((a, b) => a.score - b.score).map((r) => {
    const [x, y] = pos(r); const st = STATUS[r.status];
    const big = r.status === "Act now";
    return `<g class="dot${big ? " dot-hot" : ""}" data-id="${esc(r.id)}" transform="translate(${x.toFixed(1)},${y.toFixed(1)})">
      ${big ? `<circle r="15" class="pulse" fill="${st.color}"/>` : ""}
      <circle r="${big ? 8 : 6}" fill="${st.color}" stroke="#fff" stroke-width="2"/></g>`;
  }).join("");
  return `<svg class="polar" viewBox="0 0 ${S} ${S}" role="img" aria-label="Radar des histoires">
    <defs>
      <radialGradient id="polar-bg" cx="50%" cy="50%" r="50%">
        <stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#F4F1FA"/></radialGradient>
      <linearGradient id="polar-sweep" x1="0" y1="0" x2="1" y2="0.4">
        <stop offset="0" stop-color="${PALETTE.coral}" stop-opacity=".30"/>
        <stop offset="1" stop-color="${PALETTE.coral}" stop-opacity="0"/></linearGradient>
    </defs>
    <circle cx="${cx}" cy="${cy}" r="${R}" fill="url(#polar-bg)" class="ring ring-outer"/>
    ${rings}
    <line x1="${cx}" y1="${cy - R - 8}" x2="${cx}" y2="${cy + R + 8}" class="axis-split"/>
    ${sweep ? `<g class="sweep"><path d="${wedge}" fill="url(#polar-sweep)"/>
      <line x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy - R}" class="sweep-line"/></g>` : ""}
    <text x="${cx - R * 0.72}" y="${cy - R * 0.92}" class="half-label" text-anchor="middle">LIVRES</text>
    <text x="${cx + R * 0.72}" y="${cy - R * 0.92}" class="half-label" text-anchor="middle">WEBTOONS</text>
    ${dots}
    <circle cx="${cx}" cy="${cy}" r="5" fill="${PALETTE.ink}"/>
  </svg>`;
}

/** Map: acceleration (up) against mainstream awareness (right). */
export function scatterMap(rows, settings) {
  const W = 1080, H = 440, L = 60, B = 50, T = 16, Rm = 16;
  const pw = W - L - Rm, ph = H - T - B;
  const xv = (r) => {
    const v = r.s.wikiViews;
    if (v === null || v === undefined) return 2 + 21 * ((hash(r.id) % 1000) / 1000);
    return 32 + 68 * awareness(v);
  };
  const X = (v) => L + (v / 100) * pw, Y = (v) => T + ph - (v / 100) * ph;
  const thr = 32 + 68 * awareness(settings.unawareMaxViews);
  const yAct = settings.actNowPct;
  const ticks = [[12, "pas de page"], [32, "100"], [49, "1 k"], [66, "10 k"], [83, "100 k"], [100, "1 M"]];
  const grid = [0, 25, 50, 75, 100].map((v) => `<line x1="${L}" x2="${W - Rm}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/>
      <text x="${L - 10}" y="${Y(v) + 4}" class="tick" text-anchor="end">${v}</text>`).join("");
  const xt = ticks.map(([v, l]) => `<text x="${X(v)}" y="${H - B + 20}" class="tick" text-anchor="middle">${l}</text>`).join("");
  const pts = [...rows].sort((a, b) => a.score - b.score).map((r) => {
    const st = STATUS[r.status];
    return `<circle class="mdot" data-id="${esc(r.id)}" cx="${X(xv(r)).toFixed(1)}" cy="${Y(100 * r.accel).toFixed(1)}"
      r="${r.status === "Act now" ? 8 : 6}" fill="${st.color}" stroke="#fff" stroke-width="1.6"/>`;
  }).join("");
  return `<svg class="map" viewBox="0 0 ${W} ${H}" role="img" aria-label="Carte accélération et notoriété">
    <rect x="${X(0)}" y="${T}" width="${X(25) - X(0)}" height="${ph}" class="band-nopage"/>
    <rect x="${X(0)}" y="${Y(100)}" width="${X(thr) - X(0)}" height="${Y(yAct) - Y(100)}" class="band-act"/>
    <text x="${X(thr) - 8}" y="${Y(100) + 16}" class="band-label" text-anchor="end">ZONE « AGIR MAINTENANT »</text>
    ${grid}${xt}
    <text x="${L + pw / 2}" y="${H - 6}" class="axis-title" text-anchor="middle">Notoriété : vues Wikipedia par mois →</text>
    <text transform="translate(14 ${T + ph / 2}) rotate(-90)" class="axis-title" text-anchor="middle">Accélération dans sa communauté (centile) →</text>
    ${pts}
  </svg>`;
}

/** Line chart for a time series [[isoDate, value], ...]. */
export function lineChart(points, { color = PALETTE.coral, label = "" } = {}) {
  if (!points?.length) return "";
  const W = 520, H = 220, L = 52, B = 30, T = 14, Rm = 14;
  const xs = points.map((p) => new Date(p[0]).getTime());
  const ys = points.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  let y0 = Math.min(...ys), y1 = Math.max(...ys);
  const pad = (y1 - y0) * 0.15 || y1 * 0.1 || 1; y0 = Math.max(0, y0 - pad); y1 += pad;
  const X = (v) => L + ((v - x0) / (x1 - x0 || 1)) * (W - L - Rm);
  const Y = (v) => T + (H - T - B) - ((v - y0) / (y1 - y0 || 1)) * (H - T - B);
  const path = points.map((p, i) => `${i ? "L" : "M"}${X(xs[i]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join(" ");
  const area = `${path} L${X(x1)},${Y(y0)} L${X(x0)},${Y(y0)} Z`;
  const step = niceStep(y1 - y0);
  const yt = []; for (let v = Math.ceil(y0 / step) * step; v <= y1; v += step) yt.push(v);
  const months = points.map((p) => new Date(p[0]).toLocaleDateString("fr-FR", { month: "short", year: "2-digit" }));
  return `<svg class="mini" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
    ${yt.map((v) => `<line x1="${L}" x2="${W - Rm}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/>
      <text x="${L - 8}" y="${Y(v) + 4}" class="tick" text-anchor="end">${k(v)}</text>`).join("")}
    <path d="${area}" fill="${color}" opacity=".10"/>
    <path d="${path}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>
    ${points.map((p, i) => `<circle cx="${X(xs[i])}" cy="${Y(p[1])}" r="4" fill="${color}" stroke="#fff" stroke-width="1.5"><title>${months[i]} : ${nf.format(p[1])}</title></circle>
      <text x="${X(xs[i])}" y="${H - 8}" class="tick" text-anchor="middle">${months[i]}</text>`).join("")}
  </svg>`;
}

/** Bar chart: [[label, value], ...]. */
export function barChart(points, { color = PALETTE.plum, every = 1, label = "", highlightLast = false } = {}) {
  if (!points?.length) return "";
  const W = 520, H = 220, L = 52, B = 30, T = 14, Rm = 10;
  const ys = points.map((p) => p[1]);
  const y1 = Math.max(...ys) * 1.12 || 1;
  const bw = (W - L - Rm) / points.length;
  const Y = (v) => T + (H - T - B) - (v / y1) * (H - T - B);
  const step = niceStep(y1);
  const yt = []; for (let v = 0; v <= y1; v += step) yt.push(v);
  return `<svg class="mini" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
    ${yt.map((v) => `<line x1="${L}" x2="${W - Rm}" y1="${Y(v)}" y2="${Y(v)}" class="gridline"/>
      <text x="${L - 8}" y="${Y(v) + 4}" class="tick" text-anchor="end">${k(v)}</text>`).join("")}
    ${points.map((p, i) => `<rect x="${(L + i * bw + bw * 0.16).toFixed(1)}" y="${Y(p[1]).toFixed(1)}" width="${(bw * 0.68).toFixed(1)}"
        height="${(Y(0) - Y(p[1])).toFixed(1)}" rx="3" fill="${highlightLast && i === points.length - 1 ? PALETTE.coral : color}">
        <title>${esc(p[0])} : ${nf.format(Math.round(p[1]))}</title></rect>
      ${i % every === 0 ? `<text x="${L + i * bw + bw / 2}" y="${H - 8}" class="tick" text-anchor="middle">${esc(p[2] ?? p[0])}</text>` : ""}`).join("")}
  </svg>`;
}

/** Backtest timeline: radar alert -> deal, with the first Wikipedia page. */
export function timeline(rows) {
  const W = 900, rowH = 70, L = 230, Rm = 190, T = 20;
  const H = T + rows.length * rowH + 36;
  const t0 = new Date("2018-01-01").getTime(), t1 = new Date("2024-06-01").getTime();
  const X = (iso) => L + ((new Date(iso).getTime() - t0) / (t1 - t0)) * (W - L - Rm);
  const years = [2018, 2019, 2020, 2021, 2022, 2023, 2024];
  const body = rows.map((r, i) => {
    const y = T + i * rowH + rowH / 2;
    const hit = r.lead_months !== null && r.lead_months !== undefined;
    return `<text x="${L - 18}" y="${y + 5}" class="tl-title" text-anchor="end">${esc(r.title)}</text>
      ${r.radar_alert ? `<line x1="${X(r.radar_alert)}" x2="${X(r.announcement_date)}" y1="${y}" y2="${y}" class="tl-span"/>
        <circle cx="${X(r.radar_alert)}" cy="${y}" r="9" fill="${PALETTE.coral}"><title>Alerte : ${esc(r.radar_alert)}</title></circle>` : ""}
      ${r.first_wikipedia_page ? `<circle cx="${X(r.first_wikipedia_page)}" cy="${y}" r="10" fill="#fff" stroke="${PALETTE.plum}" stroke-width="3"><title>Première page Wikipedia : ${esc(r.first_wikipedia_page)}</title></circle>` : ""}
      <circle cx="${X(r.announcement_date)}" cy="${y}" r="9" fill="${PALETTE.ink}"><title>Contrat : ${esc(r.announcement_date)}</title></circle>
      <text x="${W - Rm + 18}" y="${y + 5}" class="${hit ? "tl-lead" : "tl-miss"}">${hit ? `${fmtMonths(r.lead_months)} mois d'avance` : "Raté : croissance lente"}</text>`;
  }).join("");
  return `<svg class="timeline" viewBox="0 0 ${W} ${H}" role="img" aria-label="Alertes du radar et contrats">
    ${years.map((yr) => `<line x1="${X(`${yr}-01-01`)}" x2="${X(`${yr}-01-01`)}" y1="${T - 6}" y2="${H - 30}" class="gridline"/>
      <text x="${X(`${yr}-01-01`)}" y="${H - 10}" class="tick" text-anchor="middle">${yr}</text>`).join("")}
    ${body}
  </svg>`;
}

/** Score ring for the story drawer. */
export function scoreRing(score, color) {
  const r = 34, c = 2 * Math.PI * r;
  return `<svg class="ring-score" viewBox="0 0 84 84" aria-label="Score ${score} sur 100">
    <circle cx="42" cy="42" r="${r}" class="ring-track"/>
    <circle cx="42" cy="42" r="${r}" fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round"
      stroke-dasharray="${((score / 100) * c).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 42 42)"/>
    <text x="42" y="47" text-anchor="middle" class="ring-num">${score}</text></svg>`;
}
