# Nécropatriarcat — atlas critique d'une économie de la mort

Encyclopédie critique en ligne consacrée au **nécropatriarcat** : généalogie du concept
(Mbembe, Valencia, Segato), mécanismes du capitalisme gore, pédagogie de la cruauté,
féminicides et transféminicides, débilitation et violence lente, injustice épistémique,
contre-pédagogies et politiques post-mortem.

→ **https://ouaisfieu.github.io/necropatriarcat/**

---

## Ce que c'est

Un site **statique**, servi tel quel : des fichiers HTML, une feuille de style, un fichier
JavaScript facultatif. Pas de framework, pas de générateur côté serveur, pas de base de
données, **aucun traceur, aucun cookie, aucune requête vers un tiers**, aucune police
externe.

**94 entrées** réparties en quatre rubriques, plus cinq pages transversales :

| Rubrique | Nombre | Contenu |
|---|---|---|
| Dossiers | 14 | Analyses longues, sourcées, reliées entre elles |
| Notions | 42 | Glossaire, également publié en thésaurus SKOS |
| Figures | 22 | Théoricien·nes et figures de lutte |
| Cas | 16 | Situations documentées, avec chiffres et jurisprudence |
| Pages | 5 | Chronologie, bibliographie, méthode, recherche, plan du site |

Chaque page porte ses sources, une par une, avec les liens.

## Mise en ligne (GitHub Pages)

Le site généré se trouve dans **`docs/`**. Aucune action, aucun build côté GitHub.

1. `Settings` → `Pages`
2. **Source** : `Deploy from a branch`
3. **Branch** : `main`, **dossier** : `/docs`
4. Enregistrer

Le fichier `docs/.nojekyll` est présent : GitHub sert les fichiers sans passer par Jekyll.

Le site est publié à la racine `/necropatriarcat/`. Pour le déployer ailleurs (domaine
propre, autre nom de dépôt), changer `base_path` et `origin` en tête de `tools/build.py`
puis régénérer.

## SEO et web sémantique

- **JSON-LD** sur chaque page : `ScholarlyArticle`, `Article`, `DefinedTerm`, `Person`,
  `CollectionPage`, `DefinedTermSet`, `ItemList`, `Event`, `BreadcrumbList`, `WebSite`
  avec `SearchAction`.
- Les **sources de chaque page** sont exposées dans `schema.org/citation`, machine-lisibles.
- **Dublin Core**, **Open Graph**, **Twitter Card** dans chaque `<head>`.
- **Thésaurus SKOS** des 42 notions : [`docs/data/vocabulaire.jsonld`](docs/data/vocabulaire.jsonld)
  — `prefLabel`, `altLabel`, `definition`, `broader`, `related`, `closeMatch` vers Wikidata.
- **Corpus schema.org** de toutes les pages : [`docs/data/corpus.jsonld`](docs/data/corpus.jsonld)
  (`DataCatalog` + `Dataset` + `DataDownload`).
- `sitemap.xml`, `robots.txt`, flux **Atom** (`feed.xml`), `manifest.webmanifest`,
  `humans.txt`, page 404.
- Une **image Open Graph** générée par page (1200×630).
- URLs stables et lisibles, canonicals absolus, fil d'Ariane sur chaque page.

## Accessibilité

HTML5 sémantique (`header`, `nav`, `main`, `article`, `aside`, `footer`), lien d'évitement,
points de repère ARIA, contrastes vérifiés en clair et en sombre, thème respectant
`prefers-color-scheme` avec bascule manuelle persistée, `prefers-reduced-motion`,
navigation clavier avec `:focus-visible`, feuille de style d'impression.

Le site est **entièrement consultable sans JavaScript** : celui-ci n'ajoute que la bascule
de thème et la recherche, et la page « plan du site » sert d'alternative à la recherche.

## Structure du dépôt

```
content/          le texte, en Markdown avec front matter YAML
  dossiers/       14 analyses longues
  notions/        42 entrées de glossaire
  figures/        22 notices
  cas/            16 études de cas
  pages/          chronologie, bibliographie, méthode, recherche, plan du site
assets/           style.css, site.js, favicon.svg
tools/build.py    le générateur (outil d'auteur, pas une étape de déploiement)
docs/             le site généré — c'est ce que GitHub Pages sert
```

### Modifier le site

Deux façons, au choix.

**Sans rien installer** : éditer directement les fichiers HTML de `docs/`. Le site n'a
besoin d'aucun outil pour fonctionner.

**Avec le générateur** (recommandé si vous ajoutez des pages, pour garder les données
structurées cohérentes) :

```bash
pip install pyyaml markdown pillow
python3 tools/build.py
```

Le générateur reconstruit `docs/` à partir de `content/` et `assets/` : pages, index,
JSON-LD, sitemap, flux, thésaurus, index de recherche et images Open Graph.

### Écrire une entrée

Un fichier Markdown avec un front matter YAML :

```yaml
---
title: "Titre de l'entrée"
date: 2026-09-19
description: "Une phrase, reprise en meta description et dans les listes."
keywords: ["mot-clé", "autre"]
about: ["slug-de-notion"]        # liens vers les notions
mentions: ["slug-de-figure"]     # liens vers les figures
refs:
  - text: "Auteur, Titre, éditeur, année."
    url: "https://..."
---
```

Dans le corps :

- `[[notions/capitalisme-gore|le capitalisme gore]]` — lien interne vérifié à la génération
  (un lien cassé est signalé sur la sortie d'erreur) ;
- `{{3}}` — renvoi vers la troisième source, avec retour cliquable.

## Auteur et licence

Textes rédigés par **Claude (Opus 5)**, modèle de langage d'Anthropic, édition **ouaisfieu**.
La méthode suivie, les sources et les limites — y compris celles qui tiennent à ce mode de
rédaction — sont exposées sur la page [Méthode](https://ouaisfieu.github.io/necropatriarcat/methode/).

Contenus sous licence **[CC BY-SA 4.0](LICENSE)**. Les citations et données de tiers restent
la propriété de leurs auteurs.

Une erreur, une source manquante, une nuance à ajouter : les
[issues](https://github.com/ouaisfieu/necropatriarcat/issues) sont là pour ça.
