# Story Radar : comment on récupère les données et comment on calcule

*Fiche d'explication pour l'équipe 21 (Christine, Fiona, Gabin, Gabriel). À lire avant les
questions du jury. Données du 26 novembre 2026.*

## En une phrase

Chaque semaine, on récupère des données publiques sur des livres et des webtoons, on calcule pour
chaque histoire **si son buzz accélère, s'il se propage et si le grand public l'ignore encore**, et
on en tire un **score sur 100** et un **statut** (Act now, Prepare, Watch, Already adapted).

## 1. D'où viennent les données

Uniquement des sources publiques, via leurs API (des services en ligne qui renvoient des données).
**Aucune donnée personnelle** : on ne garde que des chiffres par histoire, jamais des noms
d'utilisateurs.

| Source | Ce qu'on récupère | Rôle |
|---|---|---|
| **AniList** (communauté de fans de manga et de webtoons) | Les 60 webtoons coréens les plus actifs en ce moment. Pour chacun : son nombre de fans aujourd'hui et il y a 30, 60, 90 et 180 jours, son activité actuelle, et si un anime est déjà annoncé | Signal « communauté » pour les webtoons |
| **Open Library** (bibliothèque en ligne, les lecteurs y notent ce qu'ils veulent lire ou lisent) | Les romans récents (depuis 2022) qui montent le plus dans 5 genres : fantasy, romance, young adult, thriller et policier, science-fiction. Pour chacun : le nombre d'ajouts de lecteurs sur les dernières 24 h et sur chacun des 7 jours d'avant | Signal « communauté » pour les livres |
| **Wikipedia** | Si l'histoire a une page en anglais : ses vues par mois sur 2 ans, et si la page signale déjà une adaptation | Mesure du grand public |
| **Google Trends** | L'intérêt de recherche Google mois par mois (indice de 0 à 100) | Test sur le passé |

YouTube, Reddit et la liste des best-sellers du New York Times sont **déjà codés**, mais il faut
créer des clés d'accès gratuites (prochaine étape).

### Le nettoyage

- On retire les **volumes de manga** (« One Piece 114 »…), les **titres hors alphabet latin**, les
  livres **sans aucune activité** sur 8 jours, et les livres écrits par l'équipe d'Open Library
  elle-même (leur activité est gonflée en interne).
- On n'accepte une **page Wikipedia** que si c'est vraiment la bonne : même titre, une description
  qui dit « roman », « manhwa » ou « webtoon », le même auteur et la même année quand c'est
  indiqué. Exemple : la page « Want (novel) » parle d'un autre livre de 2017, elle est refusée pour
  le livre « Want » de 2024.

## 2. Le calcul de la liste de la semaine

Pour chaque histoire, on calcule **trois notes entre 0 et 1**, une par question du radar.

### ① Le buzz accélère-t-il ? → note « accélération »

- **Webtoons** : 70 % pour la croissance des fans sur 90 jours, 30 % pour l'activité actuelle sur
  AniList.
- **Livres** : 70 % pour l'activité des dernières 24 h comparée à la semaine d'avant, 30 % pour le
  volume d'activité.
- On **classe** ensuite chaque histoire parmi celles de son format (livres avec livres, webtoons
  avec webtoons). Une note de 0,95 veut dire : « elle accélère plus que 95 % des autres ».

### ② Se propage-t-elle ? → note « diffusion »

- **1** si sa page Wikipedia a moins d'un an, ou si ses vues ont augmenté d'au moins 25 % (moyenne
  des 3 derniers mois comparée aux 6 mois d'avant) ;
- **0** sinon.

### ③ Le grand public l'ignore-t-il encore ? → note « méconnaissance »

- **Pas de page Wikipedia** : la note vaut **1**.
- **Sinon**, on mesure la notoriété sur une échelle logarithmique (chaque palier multiplie les vues
  par 10) : 100 vues par mois = 0, 10 000 = 0,5, 1 million = 1. Puis
  **méconnaissance = 0,9 × (1 − notoriété)**.
- En pratique, « le grand public l'ignore encore » veut dire **moins d'environ 6 000 vues par mois**.

### Le score sur 100

> **Score = 100 × (0,6 × accélération + 0,25 × méconnaissance + 0,15 × diffusion)**

### Le statut (règles appliquées dans cet ordre)

| Statut | Règle | Ce qu'on fait |
|---|---|---|
| **Already adapted** | Un anime est listé sur AniList, ou Wikipedia signale une adaptation (série, film) | Rien : les droits sont probablement pris |
| **Act now** | Dans les **10 %** qui accélèrent le plus **et** le grand public l'ignore encore | Contacter l'ayant droit |
| **Prepare** | Dans les **40 %** qui accélèrent le plus | La lire, vérifier qui a les droits |
| **Watch** | Tout le reste | La garder sur la liste |

### Deux exemples réels à connaître

| | Dragonnap (webtoon) | Alchemised (livre) |
|---|---|---|
| Signal communauté | +31,6 % de fans en 90 jours → en tête des webtoons | lecteurs ×3 en 24 h → en tête des livres |
| Accélération | 1 | 1 |
| Wikipedia | pas de page | 23 000 vues par mois, en hausse |
| Méconnaissance | 1 | 0,9 × (1 − 0,59) = 0,37 |
| Diffusion | 0 | 1 |
| **Score** | 100 × (0,6 + 0,25 + 0) = **85** | 100 × (0,6 + 0,09 + 0,15) = **84** |
| **Statut** | **Act now** | **Prepare** : le grand public la connaît déjà |

Le score sert à classer ; c'est le **statut** qui dit quoi faire.

## 3. Le test sur le passé

**Question :** avec des données gratuites, aurait-on repéré des succès récents avant qu'un studio
achète les droits ?

### La règle, fixée avant de regarder les résultats

- On compare la moyenne des recherches Google des **3 derniers mois** à celle des **6 mois d'avant**.
- **Alerte** si ce rapport vaut au moins **2** (les recherches ont doublé), **deux mois de suite**,
  avec un niveau minimum pour ignorer le bruit.

### Les garde-fous

- **Pas de triche sur le futur** : un mois ne compte qu'une fois terminé.
- **Pas d'homonymes** : on ignore les mois d'avant la publication (des recherches sur un autre sens
  du même mot, comme « heartstopper »).
- **L'avance** se compte de la fin du mois d'alerte jusqu'à l'annonce du contrat.

### Résultats

| Histoire | Alerte du radar | Contrat annoncé | Avance |
|---|---|---|---|
| Solo Leveling | décembre 2018 | juillet 2022 (anime) | **42 mois** |
| A Good Girl's Guide to Murder | avril 2020 | septembre 2022 (BBC Three) | **28 mois** |
| Fourth Wing | juin 2023 | octobre 2023 (Amazon MGM) | **3,5 mois** |
| Heartstopper | pas d'alerte | janvier 2021 (Netflix) | **raté** : croissance trop lente |

À retenir aussi : quand Netflix a commandé Heartstopper, l'histoire n'avait **aucune page
Wikipedia**. Un outil grand public ne l'aurait pas vue.

## 4. Le test des fausses alertes

**Question :** la même règle sonne-t-elle aussi pour des histoires qui n'ont jamais été adaptées ?

- **Le groupe témoin**, choisi **avant** de regarder les courbes : les 8 webtoons de 2018 à 2022
  qui ont le plus de fans sur AniList et les 8 livres de 2019 à 2022 les plus demandés sur Open
  Library, tous sans adaptation connue.
- **La période observée** : de 12 mois avant à 46 mois après la sortie (46 mois = le délai médian
  entre la sortie et le contrat pour nos 4 adaptations).
- **La vérification** : on a cherché chaque titre dans la presse professionnelle.

| Résultat | Valeur |
|---|---|
| Histoires vraiment jamais adaptées qui ont quand même déclenché une alerte | **11 sur 12** |
| Alertes suivies d'un contrat (précision) | **29 %** |
| « Témoins » qui avaient en fait été achetés | **4** : *The Midnight Library* (2020) et la série *Twisted*, achetée par Netflix en janvier 2025, que la règle avait signalée **environ 3 ans avant** |

**Ce qu'on en retient :** la hausse des recherches repère les succès, mais elle sonne pour presque
toutes les histoires populaires. C'est un **premier filtre, pas une décision**. D'où le score à trois
questions, le classement relatif (seuls les 10 % les plus forts passent en Act now) et la
**vérification des droits à la main** avant tout contact.

## 5. Les limites à connaître (et à assumer devant le jury)

- **Échantillons** : AniList penche vers l'action et la fantasy coréennes ; Open Library est une
  petite communauté anglophone. YouTube et Reddit vont élargir.
- **TikTok** n'a pas d'accès public pour ce type de projet : on capte BookTok indirectement (via
  YouTube, Reddit, Open Library).
- **Adaptations** : AniList ne liste que les animes, pas les séries en prises de vues réelles, et
  notre détection automatique a raté 4 contrats sur 16. **Les droits se vérifient à la main.**
- **Le score est relatif** : chaque semaine, le haut de la liste est le signal le plus fort de
  *cette* semaine, pas une garantie de succès.
- **L'avance est mesurée jusqu'à l'annonce publique** : les options sont souvent signées avant,
  donc la vraie fenêtre est plus courte.

## 6. Comment tout relancer

Depuis le dossier du projet (après `pip install -r requirements.txt`, ou en double-cliquant sur
`lancer_app.bat` pour l'app) :

| Commande | Ce qu'elle fait | Durée |
|---|---|---|
| `python scripts/run_watchlist.py` | Récupère les données du jour et recalcule la liste | ~10 min (Wikipedia limite les requêtes) |
| `python scripts/run_watchlist.py --offline` | Recalcule les scores sans rien retélécharger | quelques secondes |
| `python scripts/run_poc.py` | Le test sur le passé | ~3 min |
| `python scripts/run_control_test.py` | Le test des fausses alertes | ~10 min |
| `python scripts/export_static.py` | Régénère l'interface à envoyer par mail (story_radar.html) | quelques secondes |
| `streamlit run app/streamlit_app.py` | Ouvre le prototype | quelques secondes |

## 7. Où sont les fichiers

| Quoi | Où |
|---|---|
| Les règles de calcul (code) | `src/radar/watchlist.py` (liste) et `src/radar/indicators.py` (test sur le passé) |
| La récupération des données (code) | `src/radar/sources/` : un fichier par source |
| Les résultats | `data/processed/` (la liste, le test sur le passé, le test des fausses alertes) |
| La méthode détaillée (en anglais) | `docs/04_method.md` |
| Les sources des contrats et des vérifications | `data/seeds/backtest_titles.csv` et `data/seeds/control_checks.csv` |
