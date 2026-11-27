// Story Radar — small UI helpers: escaping, formatting, icons, pills, tooltip, toast.
import { STATUS, FORMATS } from "./config.js";

export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const nf = new Intl.NumberFormat("fr-FR");
export const fmtDate = (iso, opts = { day: "numeric", month: "long", year: "numeric" }) =>
  iso ? new Date(iso).toLocaleDateString("fr-FR", opts) : "—";
export const fmtMonths = (v) => (v >= 10 ? Math.round(v) : String(v.toFixed(1)).replace(".", ","));

const ICONS = {
  radar: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12 L18 6"/><circle cx="17" cy="7" r="1.2" fill="currentColor"/>',
  list: '<path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r="1" fill="currentColor"/><circle cx="4" cy="12" r="1" fill="currentColor"/><circle cx="4" cy="18" r="1" fill="currentColor"/>',
  chart: '<path d="M4 19h16"/><path d="M7 15l4-5 3 3 5-7"/>',
  book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>',
  sliders: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  external: '<path d="M14 4h6v6"/><path d="M10 14L20 4"/><path d="M19 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6"/>',
  sparkle: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
  scale: '<path d="M12 4v16M5 20h14M6 8l-3 6h6zM18 8l-3 6h6zM6 8h12"/>',
  grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
  rows: '<rect x="4" y="5" width="16" height="4" rx="1.5"/><rect x="4" y="11" width="16" height="4" rx="1.5"/><rect x="4" y="17" width="16" height="2" rx="1"/>',
  download: '<path d="M12 4v11"/><path d="M7 10l5 5 5-5"/><path d="M5 20h14"/>',
  upload: '<path d="M12 20V9"/><path d="M7 14l5-5 5 5"/><path d="M5 4h14"/>',
  undo: '<path d="M9 14L4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>',
  arrow: '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  users: '<circle cx="9" cy="9" r="3.2"/><path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="16.5" cy="8" r="2.6"/><path d="M16 13.2c2.4.1 4 1.7 4.5 4.6"/>',
  blocks: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/><path d="M16.5 4v7M13 7.5h7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
};
export const icon = (name, size = 18) =>
  `<svg class="ico" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;

export const pill = (status, small = false) => {
  const s = STATUS[status];
  return `<span class="pill${small ? " pill-sm" : ""}" style="--pill:${s.color};--pill-text:${s.text}">${esc(s.label)}</span>`;
};

export const fmtLabel = (f) => FORMATS[f] || f;

export const cover = (r, cls = "cover") => r.cover
  ? `<img class="${cls}" src="${esc(r.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
  : `<div class="${cls} cover-ph">${esc(r.title.slice(0, 1))}</div>`;

/** Large artwork for the story cards: the whole cover on a blurred copy of itself, or a drawn cover. */
export const coverArt = (r) => r.cover
  ? `<img class="art-bg" src="${esc(r.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer">
     <img class="art-fg" src="${esc(r.cover)}" alt="" loading="lazy" referrerpolicy="no-referrer">`
  : `<div class="art-ph"><div class="art-book"><b>${esc(r.title)}</b><span>${esc(r.author || "")}</span></div></div>`;

export function scoreBar(score) {
  return `<span class="scorebar"><i style="width:${score}%"></i></span><b class="scoreval">${score}</b>`;
}

// ---- tooltip
const tip = () => document.getElementById("tooltip");
export function showTip(html, x, y) {
  const t = tip();
  t.innerHTML = html;
  t.classList.add("on");
  const r = t.getBoundingClientRect();
  const left = Math.min(window.innerWidth - r.width - 12, x + 14);
  const top = y + r.height + 24 > window.innerHeight ? y - r.height - 14 : y + 14;
  t.style.transform = `translate(${left}px, ${top}px)`;
}
export function hideTip() { tip().classList.remove("on"); }

// ---- toast
let toastTimer;
export function toast(msg, ms = 3500) {
  const t = document.getElementById("toast");
  t.innerHTML = msg;
  t.classList.add("on");
  clearTimeout(toastTimer);
  if (ms) toastTimer = setTimeout(() => t.classList.remove("on"), ms);
}
