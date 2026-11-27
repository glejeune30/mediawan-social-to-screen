// Shared bits for the views.
import { STATUS } from "../config.js";
import { esc, showTip, hideTip, fmtLabel } from "../ui.js";
import { k } from "../scoring.js";

/** Tooltips and clicks on chart dots (any element with data-id inside root). */
export function bindDots(root, store, ctx) {
  root.querySelectorAll("svg [data-id]").forEach((node) => {
    const r = store.find(node.dataset.id);
    if (!r) return;
    const html = `<b>${esc(r.title)}</b>${esc(STATUS[r.status].label)} · score ${r.score}/100<br>
      <span style="opacity:.75">${esc(fmtLabel(r.format))} · ${esc(signalShort(r))}</span>`;
    node.addEventListener("mouseenter", (e) => showTip(html, e.clientX, e.clientY));
    node.addEventListener("mousemove", (e) => showTip(html, e.clientX, e.clientY));
    node.addEventListener("mouseleave", hideTip);
    node.addEventListener("click", () => { hideTip(); ctx.openStory(r.id); });
  });
}

export function signalShort(r) {
  if (r.format === "Webtoon") {
    const g = r.s.growth90d;
    return `${k(r.s.fansNow ?? 0)} fans${g === null || g === undefined ? " · nouveau" : ` · ${g >= 0 ? "+" : ""}${(g * 100).toFixed(1).replace(".", ",")} % / 90 j`}`;
  }
  const prev = r.s.prevDaysAvg || 0, now = r.s.last24h || 0;
  return `${Math.round(now)} ajouts / 24 h${prev ? ` (×${(now / prev).toFixed(1).replace(".", ",")})` : ""}`;
}

export function mainstreamShort(r) {
  const v = r.s.wikiViews;
  if (v === null || v === undefined) return "Pas de page Wikipedia";
  return `${k(v)} vues / mois${r.spreading ? " ↗" : ""}`;
}

export const median = (arr) => {
  const a = [...arr].sort((x, y) => x - y); const m = Math.floor(a.length / 2);
  return a.length ? (a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2) : null;
};
