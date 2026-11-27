// Example extension: extra points for the genre the team is looking for right now.
export default {
  id: "bonus-genre",
  label: "Bonus de genre",
  icon: "sparkle",
  description: "Ajoute des points aux histoires du genre que Mediawan cherche en ce moment.",
  enabled: false,
  settings: [
    { key: "genreBonusGenre", type: "select", label: "Genre recherché", default: "Romance",
      // options can be a list, or a function of the data: here, the genres actually in the watchlist
      options: (data) => topGenres(data.stories).map((g) => [g, g]) },
    { key: "genreBonusPoints", type: "range", min: 0, max: 30, step: 1, unit: " pts", default: 10,
      label: "Bonus", help: "Le score reste plafonné à 100. Le statut ne change pas : il dépend de l'accélération." },
  ],
  points(story, s) {
    if (!story.genres.includes(s.genreBonusGenre)) return null;
    return { points: s.genreBonusPoints, reason: `Genre recherché : ${s.genreBonusGenre}` };
  },
};

function topGenres(stories) {
  const n = new Map();
  for (const st of stories) for (const g of st.genres) n.set(g, (n.get(g) || 0) + 1);
  return [...n.entries()].sort((a, b) => b[1] - a[1]).slice(0, 16).map(([g]) => g);
}
