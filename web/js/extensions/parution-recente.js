// Example extension: keep only recent stories (their rights are more likely to be free).
export default {
  id: "parution-recente",
  label: "Parutions récentes seulement",
  icon: "clock",
  description: "Masque les histoires publiées avant une année donnée : les droits des titres récents sont plus souvent libres.",
  enabled: false,
  settings: [
    { key: "recentMinYear", type: "range", min: 2000, max: new Date().getFullYear(), step: 1, default: 2022,
      label: "Première publication à partir de", help: "Les histoires sans année connue restent affichées." },
  ],
  keep(story, s) {
    return !story.year || story.year >= s.recentMinYear;
  },
};
