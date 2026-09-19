---
title: "Méthode"
date: 2026-09-19
description: "Qui a écrit ce site, comment, avec quelles sources, et quelles en sont les limites. Y compris celles qui tiennent au fait que l'auteur est un modèle de langage."
keywords: ["méthode", "IA", "sources", "vérification", "licence", "Claude"]
refs:
  - text: "Rita Segato décrit sa propre accoutumance à l'horreur lors de ses enquêtes au Guatemala, El País, janvier 2025."
    url: "https://english.elpais.com/international/2025-01-15/rita-segato-the-present-is-sinister-we-are-all-threatened.html"
  - text: "Sayak Valencia : « ne pas croire le récit ni reproduire la carte postale catastrophiste », entretien de mars 2026."
    url: "https://huelladelsur.ar/2026/03/14/entrevista-a-sayak-valencia-del-capitalismo-gore-al-necropatriarcado/"
---

## Qui écrit

Les textes de ce site ont été **rédigés par Claude (Opus 5)**, un modèle de langage développé par Anthropic, à la demande et sous l'édition de **ouaisfieu**.

Ce n'est pas une coquetterie ni une décharge de responsabilité. C'est une information dont vous avez besoin pour lire ce qui suit, et elle est reprise dans les données structurées de chaque page (`creator`, `author`) afin qu'un moteur ou un agent qui indexe ce site la reçoive aussi.

## Comment

Le travail s'est déroulé en trois temps.

**1. Un corpus de départ.** Deux notes de synthèse en français sur le nécropatriarcat, fournies par l'éditeur, ont servi de point d'entrée et de cartographie initiale du champ.

**2. Un croisement documentaire.** Chaque affirmation factuelle a été recherchée dans des sources primaires ou secondaires accessibles en ligne : textes des auteur·es, arrêts, textes législatifs, rapports d'institutions et d'ONG, articles de revues. Les chiffres ont été repris de leur source de publication et non de citations de seconde main — CEPAL pour les féminicides latino-américains, TGEU pour les meurtres de personnes trans, SESNSP et les observatoires mexicains, RTBF et l'Observatoire féministe pour la Belgique.

**3. Une réécriture complète.** Aucun passage des notes initiales n'a été repris tel quel. Les textes ont été écrits à partir des sources vérifiées, avec un appareil de renvois numérotés visible en bas de chaque page.

## Ce que vous pouvez vérifier

Chaque dossier, chaque notion, chaque cas porte sa liste de sources, avec les liens. Les renvois dans le texte sont cliquables dans les deux sens.

Trois principes ont été suivis :

- **Les chiffres sont datés et attribués.** « Au moins 3 828 féminicides en 2024 selon la CEPAL » et non « des milliers de femmes meurent chaque année ».
- **Les thèses contestées sont présentées comme telles.** Le chapitre sur le droit de mutiler expose les objections qui lui ont été faites ; celui sur la prostitution expose deux positions sans les fusionner.
- **Les mots des auteur·es sont cités dans leur langue quand la traduction est en jeu**, et les traductions françaises sont signalées comme telles.

## Limites

Elles sont réelles, et il vaut mieux les écrire que les laisser découvrir.

**Un modèle de langage peut se tromper.** Il peut attribuer une citation à la mauvaise personne, confondre deux éditions, produire une référence plausible mais inexacte. Les sources listées permettent de contrôler ; si vous trouvez une erreur, elle se signale sur le [dépôt du site](https://github.com/ouaisfieu/necropatriarcat/issues).

**Les sources sont majoritairement accessibles en ligne.** Des travaux essentiels publiés uniquement sur papier — ou dans des revues fermées — sont sous-représentés. C'est un biais d'accessibilité, pas un jugement de valeur.

**La couverture géographique est inégale.** L'Amérique latine et l'Europe occidentale dominent, parce que c'est là que le concept a été forgé et que les données sont les plus disponibles. L'Asie du Sud, l'Afrique subsaharienne et le monde arabe sont largement absents, alors que les mêmes mécanismes y sont documentés par d'autres littératures.

**Un site n'est pas un terrain.** Tout ce qui est ici est de seconde main. Les savoirs les plus solides sur ces violences sont produits par celles qui les subissent et par les organisations qui les accompagnent. Ce site renvoie vers elles ; il ne les remplace pas.

## Une précaution d'écriture

Rita Segato raconte qu'après avoir entendu les témoignages des survivantes guatémaltèques, elle a été malade une semaine, qu'elle les transcrivait la deuxième et qu'elle en parlait publiquement la troisième{{1}}. Elle cite cet épisode comme une démonstration de l'accoutumance — y compris chez celle qui l'étudie.

Documenter la violence, c'est risquer d'y contribuer. La règle suivie ici est simple : **aucun détail qui n'explique rien**. Les descriptions de sévices sont réduites à ce qui est nécessaire à la démonstration. Il n'y a aucune image de victime sur ce site.

Et, pour reprendre la consigne de Sayak Valencia : ne pas croire le récit, ni reproduire la carte postale catastrophiste{{2}}. C'est pourquoi le dernier dossier porte sur ce qui fonctionne.

## Technique

Site entièrement statique : des fichiers HTML servis tels quels, sans générateur côté serveur, sans framework, sans base de données. Une feuille de style, un fichier JavaScript facultatif (thème sombre et recherche), aucune police externe, **aucun traceur, aucun cookie, aucune requête vers un tiers**.

Les données du site sont publiées en JSON-LD : un [thésaurus SKOS](/necropatriarcat/data/vocabulaire.jsonld) des notions, un [corpus schema.org](/necropatriarcat/data/corpus.jsonld) de toutes les pages, un [flux Atom](/necropatriarcat/feed.xml).

## Licence et réutilisation

Les contenus sont publiés sous licence **Creative Commons BY-SA 4.0** : vous pouvez les copier, les modifier et les rediffuser, y compris commercialement, à condition de créditer la source et de partager aux mêmes conditions.

Citation suggérée :

> Claude (Opus 5), *Nécropatriarcat — atlas critique d'une économie de la mort*, éd. ouaisfieu, 2026, https://ouaisfieu.github.io/necropatriarcat/

