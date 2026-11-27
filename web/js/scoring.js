// Story Radar — scoring engine (runs in the browser, so every setting changes the results live).
// With DEFAULT_SETTINGS it reproduces the Python pipeline (src/radar/watchlist.py).
import { activeExtensions } from "./extensions/index.js";

/** Percentile rank like pandas rank(pct=True): ties get their average rank; null stays null. */
export function pctRank(values) {
  const idx = values.map((v, i) => [v, i]).filter(([v]) => v !== null && v !== undefined && !Number.isNaN(v));
  idx.sort((a, b) => a[0] - b[0]);
  const n = idx.length;
  const out = values.map(() => null);
  let i = 0;
  while (i < n) {
    let j = i;
    while (j + 1 < n && idx[j + 1][0] === idx[i][0]) j++;
    const avg = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) out[idx[k][1]] = avg / n;
    i = j + 1;
  }
  return out;
}

const clip = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

/** Mainstream awareness on a log scale: 100 views/month = 0, 10k = 0.5, 1M = 1. */
export function awareness(views) {
  return clip((Math.log10(Math.max(views, 1)) - 2) / 4, 0, 1);
}

export function inScope(story, s) {
  if (story.format === "Book" && !s.showBooks) return false;
  if (story.format === "Webtoon" && !s.showWebtoons) return false;
  if (story.format === "Webtoon" && (story.s.fansNow ?? 0) < s.minFans) return false;
  if (story.format === "Book" && (story.s.readers ?? 0) < s.minReaders) return false;
  return activeExtensions(s).every((e) => !e.keep || safe(e, () => e.keep(story, s), true) !== false);
}

/** Runs an extension hook; a broken extension is reported once and ignored, never breaks the radar. */
const broken = new Set();
function safe(ext, fn, fallback) {
  try { return fn(); } catch (err) {
    if (!broken.has(ext.id)) { broken.add(ext.id); console.warn(`Extension « ${ext.id} » ignorée :`, err); }
    return fallback;
  }
}

/** Scores every story. Returns new objects with accel, unaware, spreading, score, status, reasons. */
export function scoreAll(stories, s) {
  const out = stories.map((st) => ({ ...st }));
  // (100 - x) / 100 rather than 1 - x / 100: 1 - 0.7 = 0.30000000000000004, which breaks exact ties
  const share = s.accelGrowthShare / 100, rest = (100 - s.accelGrowthShare) / 100;
  for (const fmt of ["Book", "Webtoon"]) {
    const g = out.filter((r) => r.format === fmt);
    const gp = pctRank(g.map((r) => r.s.accelSignal));
    const ap = pctRank(g.map((r) => r.s.activityNow));
    const raw = g.map((r, i) => (gp[i] !== null ? share * gp[i] + rest * (ap[i] ?? 0) : ap[i]));
    const acc = pctRank(raw);
    g.forEach((r, i) => { r.accel = acc[i] ?? 0; });
  }
  const wSum = Math.max(1, s.wAccel + s.wUnaware + s.wSpread);
  const bonuses = activeExtensions(s).filter((e) => e.points);
  for (const r of out) {
    const views = r.s.wikiViews;
    const hasPage = views !== null && views !== undefined;
    r.unaware = hasPage ? 0.9 * (1 - awareness(views)) : 1;
    r.unknown = !hasPage || views <= s.unawareMaxViews;
    const growing = hasPage && ((r.s.wikiMomentum ?? 0) >= 1 + s.spreadGrowthPct / 100
      || (r.s.wikiAgeMonths ?? 99) <= s.spreadPageAgeMonths);
    r.spreading = growing ? 1 : 0;
    r.parts = {
      accel: (s.wAccel / wSum) * r.accel,
      unaware: (s.wUnaware / wSum) * r.unaware,
      spread: (s.wSpread / wSum) * r.spreading,
    };
    r.baseScore = Math.round(100 * (r.parts.accel + r.parts.unaware + r.parts.spread));
    if (r.adapted) r.status = "Already adapted";
    else if (r.accel >= s.actNowPct / 100 && r.unknown && (!s.actNowNeedsSpread || r.spreading)) r.status = "Act now";
    else if (r.accel >= s.preparePct / 100) r.status = "Prepare";
    else r.status = "Watch";
    // extensions add (or remove) points; the status above does not change
    r.extras = [];
    for (const e of bonuses) {
      const res = safe(e, () => e.points(r, s), null);
      if (res && Number(res.points)) r.extras.push({ id: e.id, label: e.label, points: Number(res.points), reason: res.reason || e.label });
    }
    r.score = clip(r.baseScore + r.extras.reduce((t, x) => t + x.points, 0), 0, 100);
    r.reasons = reasons(r);
  }
  const order = { "Act now": 0, Prepare: 1, Watch: 2, "Already adapted": 3 };
  return out.sort((a, b) => order[a.status] - order[b.status] || b.score - a.score);
}

const nf = new Intl.NumberFormat("fr-FR");
export const k = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1).replace(".", ",")} M`
  : n >= 1e3 ? `${Math.round(n / 1e3)} k` : nf.format(Math.round(n)));

function reasons(r) {
  const top = Math.max(1, Math.round((1 - r.accel) * 100));
  const out = [];
  if (r.format === "Webtoon") {
    out.push(r.s.growth90d === null || r.s.growth90d === undefined
      ? `Nouveau sur AniList (moins de 90 jours d'historique), déjà ${k(r.s.fansNow)} fans (top ${top} % des webtoons suivis)`
      : `Base de fans AniList ${r.s.growth90d >= 0 ? "+" : ""}${(r.s.growth90d * 100).toFixed(1).replace(".", ",")} % en 90 jours, ${k(r.s.fansNow)} fans aujourd'hui (top ${top} % des webtoons suivis)`);
  } else {
    out.push(`Lecteurs Open Library : ${Math.round(r.s.last24h ?? 0)} ajouts sur les dernières 24 h, contre ${Math.round(r.s.prevDaysAvg ?? 0)} par jour la semaine d'avant (top ${top} % des livres suivis)`);
  }
  const v = r.s.wikiViews;
  if (v === null || v === undefined) out.push("Pas encore de page Wikipedia en anglais : le grand public ne la connaît pas");
  else {
    const m = r.s.wikiMomentum;
    const trend = m && m < 999 && m >= 1.25 ? `, en hausse de ${Math.round((m - 1) * 100)} % sur 6 mois`
      : m >= 999 ? ", page créée récemment" : "";
    out.push(`Wikipedia : ${k(v)} vues le mois dernier${trend}`);
  }
  if (r.adapted) out.push(`Déjà adaptée : ${r.adaptation || "adaptation listée"}`);
  else if (r.format === "Webtoon") out.push("Aucun anime listé sur AniList : vérifier les droits en prises de vues réelles");
  else out.push("Aucune adaptation listée sur Wikipedia : vérifier les droits auprès de l'éditeur");
  for (const x of r.extras) out.push(`${x.reason} (${x.points > 0 ? "+" : ""}${x.points} pts, extension « ${x.label} »)`);
  return out;
}

export function counts(scored) {
  const c = { "Act now": 0, Prepare: 0, Watch: 0, "Already adapted": 0 };
  for (const r of scored) c[r.status]++;
  return c;
}
