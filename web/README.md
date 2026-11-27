# Story Radar : l'interface web

L'interface du radar, en HTML, CSS et JavaScript, sans framework et sans compilation. Elle remplace
le prototype Streamlit (`app/streamlit_app.py`, gardé pour mémoire).

## La lancer

- **Windows** : double-cliquer sur `lancer_app.bat` à la racine du projet. L'interface s'ouvre sur
  http://localhost:8600.
- **À la main** : `python server.py` depuis la racine, puis ouvrir http://localhost:8600.

Le serveur (`server.py`) n'utilise que la bibliothèque standard de Python. Il sert les fichiers de
`web/` et fait tourner la collecte quand on clique sur « Rafraîchir les données » (environ
10 minutes : AniList, Open Library, Wikipedia, puis recalcul de `web/data/radar.json`).

Il faut passer par le serveur : un navigateur refuse d'ouvrir ces fichiers en double-cliquant
sur `index.html`.

## Comment c'est rangé

```
web/
  index.html              la coquille : barre latérale, barre du haut, zone des pages, fiche
  css/app.css             tout le design (couleurs, cartes, radar, fiche, réglages, téléphone)
  assets/logo.svg         le logo Story Radar
  assets/partners/        le logo officiel de Mediawan (non versionné, voir plus bas)
  data/radar.json         les données de la semaine (fabriqué par scripts/export_web_data.py)
  js/
    config.js             statuts, réglages par défaut, formulaire des réglages, profils, menu
    scoring.js            le calcul du score et du statut (le même qu'en Python)
    store.js              l'état de l'appli : données, réglages (gardés dans le navigateur), filtres
    charts.js             les graphiques en SVG (radar, carte, courbes, frise des tests)
    ui.js                 petits outils : icônes, pastilles de statut, couvertures, formats
    main.js               démarrage, menu, navigation entre les pages
    views/                une page = un fichier (radar, list, tests, method, settings, drawer)
    extensions/           vos idées, une par fichier (voir plus bas)
```

Le navigateur recalcule les scores lui-même : chaque réglage change le résultat tout de suite.
Avec les réglages de référence, il retrouve exactement les résultats du pipeline Python
(`src/radar/watchlist.py`) : mêmes scores et mêmes statuts pour les 105 histoires.

## Ajouter une idée : les extensions

C'est le plus simple. Une extension = un fichier dans `js/extensions/`. Elle apparaît toute seule
dans **Réglages > Extensions**, avec un interrupteur et ses propres réglages.

1. Copier un exemple, par exemple `bonus-genre.js`, sous un nouveau nom.
2. Changer `id` (unique, sans espace), `label`, `description`, et ce qu'elle fait.
3. L'ajouter à la liste dans `js/extensions/index.js`.

```js
// js/extensions/mon-idee.js
export default {
  id: "mon-idee",
  label: "Mon idée",
  icon: "sparkle",                 // une icône de ui.js : sparkle, clock, users, shield, book...
  description: "Ce que fait l'extension, en une phrase.",
  enabled: false,                  // allumée ou éteinte par défaut
  settings: [                      // ses réglages (même format que SETTINGS_SCHEMA, plus `default`)
    { key: "monIdeePoints", type: "range", min: 0, max: 20, step: 1, unit: " pts", default: 5,
      label: "Bonus", help: "Une phrase d'aide sous le réglage." },
  ],
  // Ajouter (ou retirer) des points à une histoire : renvoyer { points, reason } ou null.
  points(story, s) {
    if (story.format !== "Webtoon") return null;
    return { points: s.monIdeePoints, reason: "Les webtoons nous intéressent en priorité" };
  },
  // Masquer une histoire du radar : renvoyer false.
  keep(story, s) {
    return true;
  },
};
```

Les deux fonctions sont facultatives. Les points s'ajoutent au score (qui reste entre 0 et 100)
et s'affichent dans la fiche de l'histoire, avec la raison. Le **statut**, lui, ne change pas :
il dépend des règles du radar (accélération, notoriété). Une extension qui plante est ignorée et
signalée dans la console du navigateur ; elle ne casse pas le radar.

Trois exemples sont fournis, éteints par défaut :

| Fichier | Ce qu'il fait |
|---|---|
| `bonus-genre.js` | des points pour le genre que l'équipe cherche en ce moment |
| `parution-recente.js` | masque les histoires publiées avant une année donnée |
| `base-de-fans.js` | des points aux histoires dont la communauté est déjà large |

### Ce qu'on sait d'une histoire (`story`)

| Champ | Contenu |
|---|---|
| `title`, `author`, `year`, `genres` | titre, auteur, année de première publication, genres (liste) |
| `format` | `"Book"` ou `"Webtoon"` |
| `adapted`, `adaptation` | déjà adaptée ? et laquelle |
| `s.growth90d`, `s.fansNow` | webtoons : croissance des fans AniList sur 90 jours, fans aujourd'hui |
| `s.last24h`, `s.prevDaysAvg` | livres : ajouts Open Library sur 24 h, moyenne par jour la semaine d'avant |
| `s.readers`, `s.wantToRead` | livres : lecteurs et « à lire » sur Open Library |
| `s.wikiViews`, `s.wikiMomentum`, `s.wikiAgeMonths` | Wikipedia : vues le mois dernier, hausse, âge de la page (vide = pas de page) |
| `accel`, `unaware`, `spreading` | les trois notes du radar, entre 0 et 1 |
| `baseScore`, `status` | le score avant extensions, le statut |

Pour une donnée qui n'existe pas encore (par exemple les vues YouTube), il faut l'ajouter à
l'export : voir « Ajouter une donnée ».

## Ajouter un réglage au cœur du radar

1. Dans `js/config.js`, ajouter la valeur par défaut dans `CORE_DEFAULTS` et une ligne dans
   `SETTINGS_SCHEMA` (types : `range`, `toggle`, `select` ; `group` = la carte où il s'affiche).
2. L'utiliser dans `js/scoring.js` (le calcul) ou dans `inScope` (le périmètre).

Le formulaire de la page Réglages se construit tout seul à partir de `SETTINGS_SCHEMA`.

## Ajouter un profil

Dans `PRESETS` (`js/config.js`) : un nom, une icône, une phrase, et les valeurs qui changent
par rapport aux réglages de référence.

## Ajouter une page

1. Créer `js/views/ma-page.js` qui exporte `title` et `render(el, store, ctx)` (`el` = la zone de
   la page, `store.state` = données et réglages, `ctx.openStory(id)` ouvre une fiche).
2. L'importer dans `js/main.js` et l'ajouter à `VIEWS`, puis au menu (`NAV` dans `js/config.js`).

## Ajouter une donnée

Les données viennent de `scripts/export_web_data.py`, qui lit les fichiers du pipeline Python et
écrit `web/data/radar.json`. Pour un nouveau signal : l'ajouter dans la liste des champs de `s`
dans ce script, relancer `python scripts/export_web_data.py`, et il est disponible dans
`story.s` côté navigateur. `scripts/run_watchlist.py` relance l'export à chaque collecte.

## Le logo de Mediawan

L'interface affiche le logo officiel s'il se trouve dans `web/assets/partners/` (`mediawan.svg`
ou `mediawan.png`), sinon le nom en toutes lettres. Ce dossier n'est pas envoyé sur GitHub : le
dépôt est public, et un logo de marque n'a rien à y faire sans l'accord de Mediawan.

## Vérifier que le calcul suit toujours le Python

Dans la console du navigateur (F12), sur l'interface :

```js
const { scoreAll } = await import("/js/scoring.js");
const { DEFAULT_SETTINGS } = await import("/js/config.js");
const all = scoreAll(__radar.state.data.stories, { ...DEFAULT_SETTINGS, hideAdapted: false });
all.filter((r) => r.status !== r.py.status || r.score !== r.py.score).length   // doit afficher 0
```
