// Story Radar — extensions. One idea = one file in this folder, then one line in the list below.
// Each extension appears in Réglages > Extensions with an on/off switch and its own settings.
// What an extension can do (all optional), see web/README.md:
//   settings: [...]      its own controls, same format as SETTINGS_SCHEMA in config.js, plus `default`
//   points(story, s)     add (or remove) points to a story's score: return { points, reason } or null
//   keep(story, s)       return false to hide a story from the radar
import bonusGenre from "./bonus-genre.js";
import parutionRecente from "./parution-recente.js";
import fanBase from "./base-de-fans.js";

export const EXTENSIONS = [bonusGenre, parutionRecente, fanBase];

/** Settings key of an extension's on/off switch. */
export const extKey = (ext) => `ext_${ext.id}`;

/** Extensions switched on in these settings. */
export const activeExtensions = (s) => EXTENSIONS.filter((e) => s[extKey(e)]);
