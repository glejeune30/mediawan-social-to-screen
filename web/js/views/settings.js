// View: settings. The form is generated from SETTINGS_SCHEMA (config.js) and from the extensions
// (js/extensions/): add an entry there to get a new control. Results update live in the summary.
import { SETTINGS_SCHEMA, PRESETS, STATUSES, DEFAULT_SETTINGS, CORE_DEFAULTS } from "../config.js";
import { EXTENSIONS, extKey, activeExtensions } from "../extensions/index.js";
import { counts, scoreAll, inScope } from "../scoring.js";
import { esc, icon, toast } from "../ui.js";

export const title = "Réglages";

export function render(el, store) {
  const s = store.state.settings;
  const data = store.state.data;
  const groups = [...new Set(SETTINGS_SCHEMA.map((f) => f.group))];
  el.innerHTML = `
  <div class="page-head fade-in"><div>
    <div class="eyebrow">Laboratoire</div>
    <h1>Les réglages</h1>
    <p class="lead">Changez les règles du radar et voyez tout de suite l'effet sur la liste. Vos réglages sont
    gardés dans ce navigateur, et vous pouvez les exporter pour les partager.</p>
  </div></div>

  <div class="presets fade-in">${PRESETS.map((p) => `
    <button class="preset ${isPreset(s, p) ? "on" : ""}" data-preset="${p.id}">${icon(p.icon, 22)}
      <b>${esc(p.label)}</b><span>${esc(p.desc)}</span></button>`).join("")}</div>

  <div class="settings-grid">
    <div class="settings-main">
      <div class="settings-groups">${groups.map((g) => `
        <section class="card fade-in"><div class="card-head"><h2>${esc(g)}</h2></div>
          ${SETTINGS_SCHEMA.filter((f) => f.group === g).map((f) => field(f, s, data)).join("")}
          ${g === "Pondération du score" ? `<div class="weights-note" id="w-note"></div>` : ""}
        </section>`).join("")}</div>

      <section class="ext fade-in" id="extensions">
        <div class="ext-head">
          <div><div class="eyebrow">${icon("blocks", 15)} Extensions</div>
            <h2>Vos idées, branchées sur le radar</h2>
            <p class="muted">Une idée = un fichier dans <code>web/js/extensions/</code>. Elle apparaît ici toute seule,
            avec ses réglages. Une extension peut ajouter des points au score ou masquer des histoires ; le statut,
            lui, reste celui des règles ci-dessus.</p></div>
        </div>
        <div class="ext-grid">${EXTENSIONS.map((e) => extCard(e, s, data)).join("")}</div>
      </section>
    </div>
    <aside class="card summary fade-in" id="summary"></aside>
  </div>`;

  // controls -> settings
  el.querySelectorAll("[data-key]").forEach((input) => {
    const key = input.dataset.key;
    const ev = input.type === "range" ? "input" : "change";
    input.addEventListener(ev, () => {
      const v = input.type === "checkbox" ? input.checked : (input.dataset.num === "1" ? Number(input.value) : input.value);
      if (input.type === "range") paint(input);
      const out = el.querySelector(`[data-out="${key}"]`);
      if (out) out.textContent = valueLabel(findField(key), v);
      if (key.startsWith("ext_")) input.closest(".ext-card")?.classList.toggle("on", v);
      store.setSettings({ [key]: v });
      el.querySelectorAll("[data-preset]").forEach((b) =>
        b.classList.toggle("on", isPreset(store.state.settings, PRESETS.find((p) => p.id === b.dataset.preset))));
    });
    if (input.type === "range") paint(input);
  });
  el.querySelectorAll("[data-preset]").forEach((b) => { b.onclick = () => {
    const p = PRESETS.find((x) => x.id === b.dataset.preset);
    const cur = store.state.settings;
    store.setSettings({ ...CORE_DEFAULTS, ...p.values, radarSweep: cur.radarSweep });
    render(el, store);
    toast(`Profil « ${esc(p.label)} » appliqué`);
  }; });
  update(el, store);
  return { update: () => update(el, store) };
}

function extCard(e, s, data) {
  const on = Boolean(s[extKey(e)]);
  return `<section class="card ext-card ${on ? "on" : ""}">
    <div class="ext-top">
      <span class="ext-ico">${icon(e.icon || "blocks", 20)}</span>
      <div class="ext-txt"><b>${esc(e.label)}</b><span>${esc(e.description || "")}</span></div>
      <label class="switch" title="Activer"><input type="checkbox" data-key="${extKey(e)}" ${on ? "checked" : ""}><span></span></label>
    </div>
    ${(e.settings || []).length ? `<div class="ext-fields">${e.settings.map((f) => field(f, s, data)).join("")}</div>` : ""}
  </section>`;
}

const ALL_FIELDS = () => [...SETTINGS_SCHEMA, ...EXTENSIONS.flatMap((e) => e.settings || [])];
const findField = (key) => ALL_FIELDS().find((f) => f.key === key);

function options(f, data) {
  return typeof f.options === "function" ? f.options(data) : f.options || [];
}

function field(f, s, data) {
  const v = s[f.key];
  let control = "";
  if (f.type === "range") {
    control = `<input type="range" data-key="${f.key}" data-num="1" min="${f.min}" max="${f.max}" step="${f.step}" value="${v}">`;
  } else if (f.type === "toggle") {
    control = `<label class="switch"><input type="checkbox" data-key="${f.key}" ${v ? "checked" : ""}><span></span></label>`;
  } else if (f.type === "select") {
    const opts = options(f, data);
    const numeric = opts.every(([val]) => typeof val === "number");
    control = `<select data-key="${f.key}" data-num="${numeric ? 1 : 0}">${opts.map(([val, lab]) =>
      `<option value="${esc(val)}" ${String(val) === String(v) ? "selected" : ""}>${esc(lab)}</option>`).join("")}</select>`;
  }
  if (f.type === "range") {
    return `<div class="field"><div class="field-row"><span class="field-label">${esc(f.label)}</span>
      <span class="field-val" data-out="${f.key}">${valueLabel(f, v)}</span></div>${control}
      ${f.help ? `<div class="field-help">${esc(f.help)}</div>` : ""}</div>`;
  }
  return `<div class="field"><div class="field-row"><span class="field-label">${esc(f.label)}</span>${control}</div>
    ${f.help ? `<div class="field-help">${esc(f.help)}</div>` : ""}</div>`;
}

function valueLabel(f, v) { return f?.unit ? `${v}${f.unit}` : String(v); }

function paint(input) {
  const p = ((input.value - input.min) / (input.max - input.min)) * 100;
  input.style.setProperty("--p", `${p}%`);
}

/** A preset is "on" when every core rule matches it (display options and extensions aside). */
function isPreset(s, p) {
  return Object.entries({ ...CORE_DEFAULTS, ...p.values })
    .every(([key, val]) => key === "radarSweep" || s[key] === val);
}

function update(el, store) {
  const { state } = store;
  const s = state.settings;
  const now = counts(state.scored);
  const ref = counts(scoreAll(state.data.stories, DEFAULT_SETTINGS)
    .filter((r) => inScope(r, DEFAULT_SETTINGS) && r.status !== "Already adapted"));
  const total = Math.max(1, state.scored.length);
  const active = activeExtensions(s);
  const note = el.querySelector("#w-note");
  if (note) {
    const sum = s.wAccel + s.wUnaware + s.wSpread;
    note.innerHTML = sum === 100 ? "Total : 100 %." : `Total : ${sum} %. Les poids sont ramenés à 100 % pour le calcul.`;
  }
  const box = el.querySelector("#summary");
  if (!box) return;
  box.innerHTML = `
    <div class="card-head"><h2>Effet de vos réglages</h2></div>
    <div class="muted" style="font-size:13px">${state.scored.length} histoires dans le périmètre. Écart avec les réglages de référence :</div>
    ${STATUSES.filter((x) => x.id !== "Already adapted" || !s.hideAdapted).map((x) => {
      const d = now[x.id] - ref[x.id];
      return `<div class="row"><span class="lab">${x.label}</span>
        <span class="bar"><i style="width:${(now[x.id] / total) * 100}%;background:${x.color}"></i></span>
        <span class="num">${now[x.id]}</span><span class="delta">${d === 0 ? "=" : (d > 0 ? "+" : "") + d}</span></div>`;
    }).join("")}
    <a class="ext-count" href="#/reglages" data-goto="extensions">${icon("blocks", 16)}
      ${active.length ? `${active.length} extension${active.length > 1 ? "s" : ""} active${active.length > 1 ? "s" : ""} : ${active.map((e) => esc(e.label)).join(", ")}`
        : "Aucune extension active"}</a>
    <div class="actions">
      <a class="btn btn-dark" href="#/radar">${icon("radar", 16)} Voir le radar</a>
      <button class="btn" id="s-export">${icon("download", 16)} Exporter les réglages</button>
      <label class="btn">${icon("upload", 16)} Importer des réglages
        <input type="file" id="s-import" accept="application/json" hidden></label>
      <button class="btn" id="s-reset">${icon("undo", 16)} Réglages de référence</button>
    </div>`;
  box.querySelector("[data-goto]").onclick = (e) => {
    e.preventDefault();
    el.querySelector("#extensions")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  box.querySelector("#s-export").onclick = () => {
    const blob = new Blob([JSON.stringify(s, null, 2)], { type: "application/json" });
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "story-radar-reglages.json" });
    a.click(); URL.revokeObjectURL(a.href);
  };
  box.querySelector("#s-import").onchange = async (e) => {
    try {
      const data = JSON.parse(await e.target.files[0].text());
      const clean = Object.fromEntries(Object.entries(data).filter(([key]) => key in DEFAULT_SETTINGS));
      store.setSettings(clean); render(el, store); toast("Réglages importés");
    } catch { toast("Ce fichier n'est pas un export de réglages valide"); }
  };
  box.querySelector("#s-reset").onclick = () => { store.resetSettings(); render(el, store); toast("Réglages de référence rétablis"); };
}
