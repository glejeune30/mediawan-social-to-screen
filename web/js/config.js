// Story Radar — configuration.
// Everything that can be tuned lives here: statuses, default settings, the settings form
// (generated from SETTINGS_SCHEMA), presets and navigation. To add an option, see web/README.md.
// New ideas can also live in their own file: see js/extensions/.
import { EXTENSIONS, extKey } from "./extensions/index.js";

export const PALETTE = {
  ink: "#1F1A2E", plum: "#5B3F8C", plum2: "#8E74C2", coral: "#FF5A4E",
  lilac: "#F1EEF7", line: "#E7E3EF", muted: "#6B6680", soft: "#B7AFCB",
};

export const STATUSES = [
  { id: "Act now", label: "Agir maintenant", color: "#FF5A4E", text: "#FFFFFF",
    help: "Forte croissance alors que le grand public l'ignore encore : contacter l'ayant droit." },
  { id: "Prepare", label: "Préparer", color: "#5B3F8C", text: "#FFFFFF",
    help: "Elle accélère : la lire et vérifier qui détient les droits." },
  { id: "Watch", label: "Surveiller", color: "#B7AFCB", text: "#1F1A2E",
    help: "Premier buzz : la garder sur la liste." },
  { id: "Already adapted", label: "Déjà adaptée", color: "#DAD6E2", text: "#6B6680",
    help: "Une adaptation est déjà listée : les droits sont probablement pris." },
];
export const STATUS = Object.fromEntries(STATUSES.map((s) => [s.id, s]));

export const FORMATS = { Book: "Livre", Webtoon: "Webtoon" };

// Default settings = the rules presented to the jury (same results as the Python pipeline).
export const CORE_DEFAULTS = {
  wAccel: 60, wUnaware: 25, wSpread: 15,
  accelGrowthShare: 70,
  actNowPct: 90, preparePct: 60,
  unawareMaxViews: 6000,
  actNowNeedsSpread: false,
  spreadGrowthPct: 25, spreadPageAgeMonths: 12,
  showBooks: true, showWebtoons: true, hideAdapted: true,
  minFans: 0, minReaders: 0,
  radarSweep: true,
};

// ... plus, for each extension, its on/off switch ("ext_<id>") and the defaults of its own settings.
export const DEFAULT_SETTINGS = {
  ...CORE_DEFAULTS,
  ...Object.fromEntries(EXTENSIONS.flatMap((e) => [
    [extKey(e), Boolean(e.enabled)],
    ...(e.settings || []).map((f) => [f.key, f.default]),
  ])),
};

// The settings page is generated from this list. One entry = one control.
// type: "range" | "toggle" | "select" ; group: title of the card it appears in.
export const SETTINGS_SCHEMA = [
  { group: "Pondération du score", key: "wAccel", type: "range", min: 0, max: 100, step: 5, unit: "%",
    label: "Accélération dans la communauté", help: "Le buzz accélère-t-il ?" },
  { group: "Pondération du score", key: "wUnaware", type: "range", min: 0, max: 100, step: 5, unit: "%",
    label: "Méconnaissance du grand public", help: "Le grand public l'ignore-t-il encore ?" },
  { group: "Pondération du score", key: "wSpread", type: "range", min: 0, max: 100, step: 5, unit: "%",
    label: "Diffusion", help: "L'histoire se propage-t-elle ?" },

  { group: "Accélération", key: "accelGrowthShare", type: "range", min: 0, max: 100, step: 5, unit: "%",
    label: "Part de la croissance", help: "Le reste vient du volume d'activité actuel. Webtoons : fans sur 90 jours. Livres : activité des dernières 24 h comparée à la semaine d'avant." },

  { group: "Seuils des statuts", key: "actNowPct", type: "range", min: 50, max: 99, step: 1, unit: "e centile",
    label: "« Agir maintenant » à partir du", help: "90 = les 10 % qui accélèrent le plus dans leur format." },
  { group: "Seuils des statuts", key: "preparePct", type: "range", min: 10, max: 95, step: 1, unit: "e centile",
    label: "« Préparer » à partir du", help: "60 = les 40 % qui accélèrent le plus." },
  { group: "Seuils des statuts", key: "unawareMaxViews", type: "select", label: "Le grand public l'ignore si moins de",
    options: [[1000, "1 000 vues / mois"], [3000, "3 000 vues / mois"], [6000, "6 000 vues / mois"],
              [10000, "10 000 vues / mois"], [30000, "30 000 vues / mois"]],
    help: "Sur Wikipedia en anglais. Pas de page = inconnue du grand public." },
  { group: "Seuils des statuts", key: "actNowNeedsSpread", type: "toggle",
    label: "Exiger aussi la diffusion pour « Agir maintenant »", help: "Moins d'alertes, mais plus solides." },

  { group: "Diffusion", key: "spreadGrowthPct", type: "range", min: 0, max: 200, step: 5, unit: "%",
    label: "Hausse des vues Wikipedia", help: "Moyenne des 3 derniers mois comparée aux 6 mois d'avant." },
  { group: "Diffusion", key: "spreadPageAgeMonths", type: "range", min: 0, max: 36, step: 1, unit: " mois",
    label: "Ou page Wikipedia créée depuis moins de", help: "Une page récente = l'histoire commence à se faire connaître." },

  { group: "Périmètre", key: "showBooks", type: "toggle", label: "Livres (Open Library)" },
  { group: "Périmètre", key: "showWebtoons", type: "toggle", label: "Webtoons (AniList)" },
  { group: "Périmètre", key: "hideAdapted", type: "toggle", label: "Masquer les histoires déjà adaptées" },
  { group: "Périmètre", key: "minFans", type: "select", label: "Webtoons : au moins",
    options: [[0, "tous"], [1000, "1 000 fans"], [5000, "5 000 fans"], [20000, "20 000 fans"]] },
  { group: "Périmètre", key: "minReaders", type: "select", label: "Livres : au moins",
    options: [[0, "tous"], [20, "20 lecteurs"], [100, "100 lecteurs"], [500, "500 lecteurs"]] },

  { group: "Affichage", key: "radarSweep", type: "toggle", label: "Animation du radar" },
];

// A preset changes the core rules only (extensions keep their state). Missing keys = CORE_DEFAULTS.
export const PRESETS = [
  { id: "balanced", label: "Équilibré", icon: "scale",
    desc: "Les réglages présentés au jury.", values: {} },
  { id: "hunter", label: "Chasseur de pépites", icon: "sparkle",
    desc: "Privilégie les histoires que personne ne connaît encore.",
    values: { wAccel: 50, wUnaware: 40, wSpread: 10, actNowPct: 85, unawareMaxViews: 3000,
              actNowNeedsSpread: false } },
  { id: "prudent", label: "Prudent", icon: "shield",
    desc: "Moins d'alertes, plus sûres : il faut aussi que l'histoire se propage.",
    values: { wAccel: 55, wUnaware: 20, wSpread: 25, actNowPct: 95, preparePct: 75,
              actNowNeedsSpread: true } },
];

export const NAV = [
  { id: "radar", label: "Radar", icon: "radar" },
  { id: "liste", label: "Liste", icon: "list" },
  { id: "tests", label: "Tests", icon: "chart" },
  { id: "methode", label: "Méthode", icon: "book" },
  { id: "reglages", label: "Réglages", icon: "sliders" },
];

export const SOURCES = [
  ["AniList", "Fans de webtoons (communauté)", "API publique, sans clé", "live"],
  ["Open Library", "Lecteurs de livres (communauté)", "API publique, sans clé", "live"],
  ["Wikipedia", "Notoriété auprès du grand public", "API officielle, sans clé", "live"],
  ["Google Trends", "Recherches du grand public (test sur le passé)", "Client non officiel", "live"],
  ["YouTube", "BookTube et critiques de webtoons", "API officielle, clé gratuite", "ready"],
  ["Reddit", "Communautés de fans", "API officielle, clé gratuite", "ready"],
  ["NYT Best Sellers", "Vérité terrain pour les livres", "API officielle, clé gratuite", "ready"],
  ["Classements Webtoon et Wattpad", "Nouvelles entrées, fortes progressions", "Classements publics", "planned"],
];

// Partner logo shown in the sidebar: first file found is used, otherwise the name in letters.
// The folder is not in the public repository (see web/README.md).
export const PARTNER_LOGOS = ["assets/partners/mediawan.png", "assets/partners/mediawan.svg"];
