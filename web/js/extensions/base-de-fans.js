// Example extension: reward stories whose community is already big, not only fast-growing.
export default {
  id: "base-de-fans",
  label: "Prime à la communauté",
  icon: "users",
  description: "Ajoute des points aux webtoons qui ont déjà beaucoup de fans et aux livres que beaucoup veulent lire.",
  enabled: false,
  settings: [
    { key: "fanBaseWebtoon", type: "select", label: "Webtoons : à partir de", default: 20000,
      options: [[5000, "5 000 fans"], [20000, "20 000 fans"], [50000, "50 000 fans"]] },
    { key: "fanBaseBook", type: "select", label: "Livres : à partir de", default: 1000,
      options: [[300, "300 « à lire »"], [1000, "1 000 « à lire »"], [5000, "5 000 « à lire »"]] },
    { key: "fanBasePoints", type: "range", min: 0, max: 20, step: 1, unit: " pts", default: 5, label: "Bonus" },
  ],
  points(story, s) {
    const big = story.format === "Webtoon"
      ? (story.s.fansNow ?? 0) >= s.fanBaseWebtoon
      : (story.s.wantToRead ?? 0) >= s.fanBaseBook;
    if (!big) return null;
    return { points: s.fanBasePoints, reason: story.format === "Webtoon"
      ? "Communauté déjà large sur AniList" : "Beaucoup de lecteurs veulent le lire sur Open Library" };
  },
};
