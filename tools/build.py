#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du site « Nécropatriarcat ».

Ce script est un OUTIL D'AUTEUR, pas une étape de déploiement : il produit,
dans ./docs, un site entièrement statique (HTML + CSS + un fichier JS
facultatif), sans dépendance à l'exécution, sans framework et sans build côté
hébergeur. GitHub Pages n'a qu'à servir les fichiers tels quels.

    python3 tools/build.py

Dépendances (pour régénérer uniquement) : pyyaml, markdown, pillow.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

import markdown as md_lib
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"

# --------------------------------------------------------------------------
# Configuration du site
# --------------------------------------------------------------------------

SITE = {
    "name": "Nécropatriarcat",
    "tagline": "Atlas critique d'une économie de la mort",
    "base_path": "/necropatriarcat",
    "origin": "https://ouaisfieu.github.io",
    "lang": "fr",
    "locale": "fr_FR",
    "author_name": "Claude (Opus 5)",
    "author_note": "modèle de langage d'Anthropic",
    "editor": "ouaisfieu",
    "editor_url": "https://ouaisfieu.github.io/",
    "repo": "https://github.com/ouaisfieu/necropatriarcat",
    "license_name": "CC BY-SA 4.0",
    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.fr",
    "description": (
        "Encyclopédie critique du nécropatriarcat : généalogie du concept "
        "(Mbembe, Valencia, Segato), mécanismes du capitalisme gore, "
        "pédagogie de la cruauté, féminicides et transféminicides, "
        "débilitation, violence lente, injustice épistémique, "
        "contre-pédagogies et politiques post-mortem."
    ),
}

BASE = SITE["origin"] + SITE["base_path"]
BP = SITE["base_path"]

SECTIONS = {
    "dossiers": {
        "title": "Dossiers",
        "plural": "dossiers",
        "singular": "dossier",
        "slug": "dossiers",
        "lede": "Des analyses longues, sourcées et reliées entre elles : la charpente théorique et empirique du nécropatriarcat.",
        "order": 1,
    },
    "notions": {
        "title": "Notions",
        "plural": "notions",
        "singular": "notion",
        "slug": "notions",
        "lede": "Le vocabulaire critique, défini terme à terme et publié comme un thésaurus SKOS réutilisable.",
        "order": 2,
    },
    "figures": {
        "title": "Figures",
        "plural": "figures",
        "singular": "figure",
        "slug": "figures",
        "lede": "Celles et ceux qui ont forgé les concepts — et celles qui en sont mortes.",
        "order": 3,
    },
    "cas": {
        "title": "Cas",
        "plural": "cas",
        "singular": "cas",
        "slug": "cas",
        "lede": "Des situations documentées, du champ de coton de Ciudad Juárez aux commissariats européens.",
        "order": 4,
    },
}

PAGES_ORDER = ["chronologie", "bibliographie", "recherche", "methode", "plan-du-site"]


# --------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------

def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[\s_-]+", "-", value).strip("-")


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def url(path: str) -> str:
    """URL absolue-racine, préfixée par le chemin du projet GitHub Pages."""
    if path.startswith(("http://", "https://", "#", "mailto:")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return (BP + path).replace("//", "/")


def canonical(path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    return SITE["origin"] + url(path)


def read_docs(folder: Path):
    docs = []
    if not folder.exists():
        return docs
    for fp in sorted(folder.glob("*.md")):
        raw = fp.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            raise SystemExit(f"Front matter manquant : {fp}")
        _, fm, body = raw.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        meta["_body"] = body.strip()
        meta["_file"] = fp
        meta.setdefault("slug", fp.stem)
        docs.append(meta)
    return docs


# --------------------------------------------------------------------------
# Rendu Markdown
# --------------------------------------------------------------------------

MD = md_lib.Markdown(
    extensions=["extra", "sane_lists", "smarty", "attr_list", "toc"],
    extension_configs={
        "smarty": {"substitutions": {"left-single-quote": "‘", "right-single-quote": "’"}},
        "toc": {"anchorlink": False, "permalink": "§", "permalink_class": "anchor",
                "permalink_title": "Lien permanent vers cette section"},
    },
    output_format="html5",
)

LINK_RE = re.compile(r"\[\[([a-z]+)/([a-z0-9\-]+)(?:\|([^\]]+))?\]\]")
REF_RE = re.compile(r"\{\{(\d+)\}\}")


USED_REFS: set[int] = set()


def render_markdown(body: str, index: dict) -> tuple[str, str]:
    USED_REFS.clear()
    USED_REFS.update(int(n) for n in REF_RE.findall(body))
    def link_sub(m):
        kind, slug, label = m.group(1), m.group(2), m.group(3)
        target = index.get(f"{kind}/{slug}")
        if target is None:
            print(f"  ! lien interne cassé : {kind}/{slug}", file=sys.stderr)
            return label or slug
        text = label or target["title"]
        cls = ' class="xref"'
        return f'<a href="{url("/" + kind + "/" + slug + "/")}"{cls}>{text}</a>'

    def ref_sub(m):
        n = m.group(1)
        return (f'<sup class="ref"><a href="#source-{n}" id="renvoi-{n}" '
                f'aria-label="Voir la source {n}">{n}</a></sup>')

    body = LINK_RE.sub(link_sub, body)
    body = REF_RE.sub(ref_sub, body)
    MD.reset()
    out = MD.convert(body)
    toc = getattr(MD, "toc", "")
    return out, toc


def render_sources(refs, used=None) -> str:
    if not refs:
        return ""
    used = set() if used is None else used
    items = []
    for i, ref in enumerate(refs, start=1):
        if isinstance(ref, str):
            ref = {"text": ref}
        text = ref.get("text") or ref.get("title", "")
        link = ref.get("url")
        inner = text
        if link:
            inner = f'{text} <a class="src-link" href="{esc(link)}" rel="noopener nofollow">↗</a>'
        back = (f'<a class="backref" href="#renvoi-{i}" aria-label="Retour au texte">↩</a> '
                if i in used else '<span class="backref backref-off" aria-hidden="true">·</span> ')
        items.append(
            f'<li id="source-{i}" value="{i}">{back}'
            f'<span class="src-text">{inner}</span></li>'
        )
    return (
        '<section class="sources" id="sources" aria-labelledby="sources-titre">\n'
        '<h2 id="sources-titre">Sources</h2>\n'
        '<ol class="source-list">\n' + "\n".join(items) + "\n</ol>\n</section>"
    )


# --------------------------------------------------------------------------
# Gabarits HTML
# --------------------------------------------------------------------------

def nav_html(active: str) -> str:
    links = []
    for key, sec in sorted(SECTIONS.items(), key=lambda kv: kv[1]["order"]):
        cur = ' aria-current="page"' if active == key else ""
        links.append(f'<li><a href="{url("/" + sec["slug"] + "/")}"{cur}>{sec["title"]}</a></li>')
    for page, label in [("chronologie", "Chronologie"), ("bibliographie", "Bibliographie"),
                        ("methode", "Méthode")]:
        cur = ' aria-current="page"' if active == page else ""
        links.append(f'<li><a href="{url("/" + page + "/")}"{cur}>{label}</a></li>')
    links.append(f'<li><a href="{url("/recherche/")}" class="nav-search">Rechercher</a></li>')
    return "\n".join(links)


def breadcrumb_html(trail) -> str:
    """trail : liste de (label, href|None)."""
    parts = []
    for i, (label, href) in enumerate(trail):
        if href:
            parts.append(f'<li><a href="{url(href)}">{esc(label)}</a></li>')
        else:
            parts.append(f'<li><span aria-current="page">{esc(label)}</span></li>')
    return ('<nav class="breadcrumb" aria-label="Fil d\'Ariane"><ol>'
            + "".join(parts) + "</ol></nav>")


def breadcrumb_jsonld(trail) -> dict:
    items = []
    for i, (label, href) in enumerate(trail, start=1):
        entry = {"@type": "ListItem", "position": i, "name": label}
        if href:
            entry["item"] = canonical(href)
        items.append(entry)
    return {"@type": "BreadcrumbList", "itemListElement": items}


AUTHOR_LD = {
    "@type": "SoftwareApplication",
    "@id": BASE + "/methode/#auteur",
    "name": "Claude (Opus 5)",
    "applicationCategory": "Modèle de langage",
    "operatingSystem": "Web",
    "creator": {"@type": "Organization", "name": "Anthropic", "url": "https://www.anthropic.com"},
    "description": "Texte rédigé par un modèle de langage, à partir d'un corpus de sources vérifiables listées à chaque page.",
}

PUBLISHER_LD = {
    "@type": "Person",
    "@id": BASE + "/#editeur",
    "name": "ouaisfieu",
    "url": SITE["editor_url"],
}

WEBSITE_LD = {
    "@type": "WebSite",
    "@id": BASE + "/#site",
    "name": SITE["name"],
    "alternateName": "Nécropatriarcat — atlas critique",
    "url": BASE + "/",
    "inLanguage": "fr",
    "description": SITE["description"],
    "publisher": {"@id": BASE + "/#editeur"},
    "license": SITE["license_url"],
    "potentialAction": {
        "@type": "SearchAction",
        "target": {"@type": "EntryPoint", "urlTemplate": BASE + "/recherche/?q={search_term_string}"},
        "query-input": "required name=search_term_string",
    },
}


def page(
    *,
    path: str,
    title: str,
    description: str,
    body: str,
    active: str = "",
    trail=None,
    jsonld=None,
    keywords=None,
    og_image: str = "/assets/og/default.png",
    og_type: str = "website",
    published: str = "",
    modified: str = "",
    toc: str = "",
    head_extra: str = "",
    body_class: str = "",
):
    trail = trail or []
    graph = [WEBSITE_LD, PUBLISHER_LD]
    if trail:
        graph.append(breadcrumb_jsonld(trail))
    if jsonld:
        graph.extend(jsonld if isinstance(jsonld, list) else [jsonld])
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph},
                    ensure_ascii=False, indent=1)

    full_title = title if path == "/" else f"{title} — {SITE['name']}"
    kw = ", ".join(keywords or [])

    toc_block = ""
    if toc and toc.count("<li") > 2:
        toc_block = (
            '<aside class="toc" aria-labelledby="toc-titre">'
            '<h2 id="toc-titre" class="toc-titre">Sur cette page</h2>'
            + toc.replace('<div class="toc">', "").replace("</div>", "")
            + "</aside>"
        )

    doc = f"""<!DOCTYPE html>
<html lang="fr" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
{'<meta name="keywords" content="' + esc(kw) + '">' if kw else ''}
<link rel="canonical" href="{canonical(path)}">
<meta name="author" content="{esc(SITE['author_name'])}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#faf8f5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#111015" media="(prefers-color-scheme: dark)">

<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical(path)}">
<meta property="og:image" content="{canonical(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)} — {esc(SITE['name'])}">
{'<meta property="article:published_time" content="' + esc(published) + '">' if published else ''}
{'<meta property="article:modified_time" content="' + esc(modified) + '">' if modified else ''}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{canonical(og_image)}">

<meta name="DC.title" content="{esc(title)}">
<meta name="DC.creator" content="{esc(SITE['author_name'])}">
<meta name="DC.publisher" content="{esc(SITE['editor'])}">
<meta name="DC.language" content="fr">
<meta name="DC.type" content="Text">
<meta name="DC.format" content="text/html">
<meta name="DC.rights" content="{esc(SITE['license_name'])}">
{'<meta name="DC.date" content="' + esc(published) + '">' if published else ''}
<meta name="DC.identifier" content="{canonical(path)}">
<meta name="DC.description" content="{esc(description)}">

<link rel="license" href="{SITE['license_url']}">
<link rel="alternate" type="application/atom+xml" title="Nécropatriarcat — nouveautés" href="{url('/feed.xml')}">
<link rel="alternate" type="application/ld+json" title="Corpus en JSON-LD" href="{url('/data/corpus.jsonld')}">
<link rel="describedby" type="application/ld+json" href="{url('/data/vocabulaire.jsonld')}">
<link rel="stylesheet" href="{url('/assets/style.css')}">
<link rel="icon" href="{url('/assets/favicon.svg')}" type="image/svg+xml">
<link rel="manifest" href="{url('/manifest.webmanifest')}">
{head_extra}
<script type="application/ld+json">
{ld}
</script>
</head>
<body class="{body_class}">
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="wordmark" href="{url('/')}">
      <span class="wordmark-main">Nécropatriarcat</span>
      <span class="wordmark-sub">atlas critique</span>
    </a>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Basculer le thème sombre ou clair" title="Thème clair / sombre">
      <span aria-hidden="true">◐</span>
    </button>
    <nav class="site-nav" aria-label="Navigation principale">
      <ul>
{nav_html(active)}
      </ul>
    </nav>
  </div>
</header>
<main id="contenu" class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div class="footer-col">
      <h2>Nécropatriarcat</h2>
      <p>Encyclopédie critique en accès libre. Texte rédigé par <a href="{url('/methode/')}">Claude&nbsp;(Opus&nbsp;5)</a>, édition&nbsp;: <a href="{esc(SITE['editor_url'])}" rel="noopener">ouaisfieu</a>.</p>
      <p class="license">Contenus sous licence <a href="{SITE['license_url']}" rel="license noopener">Creative Commons BY-SA 4.0</a>.</p>
    </div>
    <div class="footer-col">
      <h2>Parcourir</h2>
      <ul>
        <li><a href="{url('/dossiers/')}">Dossiers</a></li>
        <li><a href="{url('/notions/')}">Notions</a></li>
        <li><a href="{url('/figures/')}">Figures</a></li>
        <li><a href="{url('/cas/')}">Cas</a></li>
        <li><a href="{url('/chronologie/')}">Chronologie</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h2>Données</h2>
      <ul>
        <li><a href="{url('/bibliographie/')}">Bibliographie</a></li>
        <li><a href="{url('/data/vocabulaire.jsonld')}">Thésaurus SKOS</a></li>
        <li><a href="{url('/data/corpus.jsonld')}">Corpus JSON-LD</a></li>
        <li><a href="{url('/feed.xml')}">Flux Atom</a></li>
        <li><a href="{url('/plan-du-site/')}">Plan du site</a></li>
        <li><a href="{esc(SITE['repo'])}" rel="noopener">Code source</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h2>Se protéger</h2>
      <p>Belgique&nbsp;: <strong>0800 30 030</strong> (violences conjugales), <strong>112</strong> (urgence).<br>
      France&nbsp;: <strong>3919</strong>. Urgence&nbsp;: <strong>17</strong> ou <strong>114</strong> par SMS.</p>
    </div>
  </div>
  <div class="wrap footer-base">
    <p>Dernière génération&nbsp;: <time datetime="{date.today().isoformat()}">{date.today().strftime('%d/%m/%Y')}</time>. Site statique, sans traceur, sans cookie, sans script tiers.</p>
  </div>
</footer>
<script src="{url('/assets/site.js')}" defer></script>
</body>
</html>
"""
    target = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")
    return doc


# --------------------------------------------------------------------------
# Chargement du contenu
# --------------------------------------------------------------------------

def load_all():
    data = {}
    for key in SECTIONS:
        data[key] = read_docs(CONTENT / key)
    data["pages"] = read_docs(CONTENT / "pages")
    index = {}
    for key in SECTIONS:
        for d in data[key]:
            index[f"{key}/{d['slug']}"] = d
    return data, index


def item_path(kind: str, slug: str) -> str:
    return f"/{kind}/{slug}/"


def summary_of(doc) -> str:
    return doc.get("description") or doc.get("definition") or ""


# --------------------------------------------------------------------------
# JSON-LD par type
# --------------------------------------------------------------------------

def article_ld(doc, kind, path, refs):
    types = {"dossiers": "ScholarlyArticle", "cas": "Article", "notions": "DefinedTerm",
             "figures": "Person"}
    citations = []
    for ref in refs or []:
        if isinstance(ref, str):
            ref = {"text": ref}
        c = {"@type": "CreativeWork", "name": ref.get("text") or ref.get("title") or ""}
        if ref.get("url"):
            c["url"] = ref["url"]
        citations.append(c)

    if kind == "notions":
        node = {
            "@type": "DefinedTerm",
            "@id": canonical(path) + "#terme",
            "name": doc["title"],
            "alternateName": doc.get("alt", []),
            "description": doc.get("definition", doc.get("description", "")),
            "inDefinedTermSet": {"@id": BASE + "/notions/#thesaurus"},
            "url": canonical(path),
            "termCode": doc["slug"],
        }
        if doc.get("wikidata"):
            node["sameAs"] = doc["wikidata"]
        return [node, web_page_ld(doc, path, citations)]

    if kind == "figures":
        node = {
            "@type": "Person",
            "@id": canonical(path) + "#personne",
            "name": doc["title"],
            "description": doc.get("description", ""),
            "url": canonical(path),
        }
        for k, v in (("jobTitle", doc.get("role")), ("birthDate", doc.get("naissance")),
                     ("deathDate", doc.get("deces")), ("nationality", doc.get("pays"))):
            if v:
                node[k] = str(v)
        sameas = [x for x in [doc.get("wikidata"), *(doc.get("sameAs") or [])] if x]
        if sameas:
            node["sameAs"] = sameas
        if doc.get("oeuvres"):
            node["knowsAbout"] = doc.get("themes", [])
        return [node, web_page_ld(doc, path, citations)]

    node = {
        "@type": types.get(kind, "Article"),
        "@id": canonical(path) + "#article",
        "headline": doc["title"],
        "name": doc["title"],
        "description": doc.get("description", ""),
        "url": canonical(path),
        "mainEntityOfPage": canonical(path),
        "inLanguage": "fr",
        "isPartOf": {"@id": BASE + "/#site"},
        "author": AUTHOR_LD,
        "editor": {"@id": BASE + "/#editeur"},
        "publisher": {"@id": BASE + "/#editeur"},
        "license": SITE["license_url"],
        "datePublished": str(doc.get("date", date.today())),
        "dateModified": str(doc.get("updated", doc.get("date", date.today()))),
        "keywords": ", ".join(doc.get("keywords", [])),
        "articleSection": SECTIONS[kind]["title"],
        "image": canonical(doc.get("og") or f"/assets/og/{kind}-{doc['slug']}.png"),
        "citation": citations,
        "wordCount": doc.get("_words", 0),
        "isAccessibleForFree": True,
        "copyrightHolder": {"@id": BASE + "/#editeur"},
        "discussionUrl": SITE["repo"] + "/issues",
    }
    if doc.get("abstract"):
        node["abstract"] = doc["abstract"]
    about = []
    for slug in doc.get("about", []):
        about.append({"@id": canonical(f"/notions/{slug}/") + "#terme"})
    if about:
        node["about"] = about
    if doc.get("mentions"):
        node["mentions"] = [{"@id": canonical(f"/figures/{s}/") + "#personne"}
                            for s in doc["mentions"]]
    return [node]


def web_page_ld(doc, path, citations):
    return {
        "@type": "WebPage",
        "@id": canonical(path) + "#page",
        "name": doc["title"],
        "description": doc.get("description", ""),
        "url": canonical(path),
        "inLanguage": "fr",
        "isPartOf": {"@id": BASE + "/#site"},
        "author": AUTHOR_LD,
        "publisher": {"@id": BASE + "/#editeur"},
        "license": SITE["license_url"],
        "datePublished": str(doc.get("date", date.today())),
        "dateModified": str(doc.get("updated", doc.get("date", date.today()))),
        "citation": citations,
    }


# --------------------------------------------------------------------------
# Construction des pages
# --------------------------------------------------------------------------

def related_block(doc, index, kind):
    groups = []
    for field, label, target_kind in [
        ("about", "Notions liées", "notions"),
        ("mentions", "Figures", "figures"),
        ("cas", "Cas", "cas"),
        ("dossiers", "Dossiers", "dossiers"),
    ]:
        slugs = doc.get(field) or []
        items = []
        for s in slugs:
            t = index.get(f"{target_kind}/{s}")
            if not t:
                continue
            items.append(
                f'<li><a href="{url(item_path(target_kind, s))}">{esc(t["title"])}</a>'
                f'<span class="rel-desc">{esc(summary_of(t))}</span></li>'
            )
        if items:
            groups.append(f'<div class="rel-group"><h3>{label}</h3><ul>' + "".join(items) + "</ul></div>")
    if not groups:
        return ""
    return ('<section class="related" aria-labelledby="rel-titre">'
            '<h2 id="rel-titre">Poursuivre</h2>'
            '<div class="rel-grid">' + "".join(groups) + "</div></section>")


def build_item(doc, kind, index):
    path = item_path(kind, doc["slug"])
    body_html, toc = render_markdown(doc["_body"], index)
    used = set(USED_REFS)
    doc["_words"] = len(re.sub(r"<[^>]+>", " ", body_html).split())
    sources = render_sources(doc.get("refs"), used)
    sec = SECTIONS[kind]
    trail = [("Accueil", "/"), (sec["title"], f"/{sec['slug']}/"), (doc["title"], None)]

    meta_bits = []
    if doc.get("date"):
        meta_bits.append(f'<time datetime="{esc(doc["date"])}">{esc(doc["date"])}</time>')
    if doc.get("_words"):
        mins = max(1, round(doc["_words"] / 220))
        meta_bits.append(f'<span>{doc["_words"]} mots · {mins} min</span>')
    if doc.get("refs"):
        meta_bits.append(f'<span>{len(doc["refs"])} sources</span>')

    head_bits = ""
    if kind == "figures":
        rows = []
        for label, key in [("Rôle", "role"), ("Pays", "pays"), ("Naissance", "naissance"),
                           ("Mort", "deces"), ("Concepts", "concepts")]:
            v = doc.get(key)
            if v:
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v)
                rows.append(f"<div><dt>{label}</dt><dd>{esc(v)}</dd></div>")
        if rows:
            head_bits = '<dl class="fiche">' + "".join(rows) + "</dl>"
        if doc.get("oeuvres"):
            lis = "".join(f"<li>{esc(o)}</li>" for o in doc["oeuvres"])
            head_bits += f'<div class="oeuvres"><h2>Œuvres clés</h2><ul>{lis}</ul></div>'
    if kind == "notions":
        bits = []
        if doc.get("alt"):
            bits.append(f'<p class="alt-labels"><strong>Aussi&nbsp;:</strong> {esc(", ".join(doc["alt"]))}</p>')
        if doc.get("auteur"):
            bits.append(f'<p class="alt-labels"><strong>Forgé par&nbsp;:</strong> {esc(doc["auteur"])}</p>')
        if doc.get("definition"):
            bits.insert(0, f'<p class="definition">{esc(doc["definition"])}</p>')
        head_bits = "".join(bits)
    if kind == "cas":
        rows = []
        for label, key in [("Lieu", "lieu"), ("Période", "periode"), ("Acteurs", "acteurs"),
                           ("Statut", "statut")]:
            v = doc.get(key)
            if v:
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v)
                rows.append(f"<div><dt>{label}</dt><dd>{esc(v)}</dd></div>")
        if rows:
            head_bits = '<dl class="fiche">' + "".join(rows) + "</dl>"

    lede = f'<p class="lede">{esc(doc.get("lede", doc.get("description","")))}</p>' if doc.get("lede") or doc.get("description") else ""

    body = f"""
{breadcrumb_html(trail)}
<article class="prose" itemscope itemtype="https://schema.org/{'DefinedTerm' if kind=='notions' else 'Person' if kind=='figures' else 'Article'}">
  <header class="article-head">
    <p class="kicker">{esc(SECTIONS[kind]['singular'].capitalize())}{' · ' + esc(doc['rubrique']) if doc.get('rubrique') else ''}</p>
    <h1 itemprop="name">{esc(doc['title'])}</h1>
    {lede}
    <p class="byline">Par <a href="{url('/methode/')}">Claude (Opus 5)</a> · {" · ".join(meta_bits)}</p>
    {head_bits}
  </header>
  {toc_placeholder()}
  <div class="article-body" itemprop="{'description' if kind=='notions' else 'text'}">
{body_html}
  </div>
  {sources}
</article>
{related_block(doc, index, kind)}
<nav class="pager" aria-label="Navigation dans la rubrique">
  <a class="pager-back" href="{url('/' + SECTIONS[kind]['slug'] + '/')}">← Tous les {esc(SECTIONS[kind]['plural'])}</a>
</nav>
"""
    og = f"/assets/og/{kind}-{doc['slug']}.png"
    doc["_og"] = og
    html_doc = page(
        path=path,
        title=doc["title"],
        description=doc.get("description", "")[:300],
        body=body,
        active=kind,
        trail=trail,
        jsonld=article_ld(doc, kind, path, doc.get("refs")),
        keywords=doc.get("keywords"),
        og_image=og,
        og_type="article",
        published=str(doc.get("date", "")),
        modified=str(doc.get("updated", doc.get("date", ""))),
        toc=toc,
    )
    # insertion du sommaire au bon endroit
    if toc and toc.count("<li") > 2:
        block = ('<aside class="toc" aria-labelledby="toc-titre">'
                 '<h2 id="toc-titre" class="toc-titre">Sur cette page</h2>'
                 + toc.replace('<div class="toc">', "").replace("</div>", "") + "</aside>")
    else:
        block = ""
    target = OUT / path.strip("/") / "index.html"
    target.write_text(html_doc.replace(TOC_TOKEN, block), encoding="utf-8")
    doc["_path"] = path
    doc["_text"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body_html)).strip()
    return doc


TOC_TOKEN = "<!--TOC-->"


def toc_placeholder():
    return TOC_TOKEN


def build_section_index(kind, docs, index):
    sec = SECTIONS[kind]
    trail = [("Accueil", "/"), (sec["title"], None)]
    groups = {}
    for d in docs:
        groups.setdefault(d.get("rubrique", ""), []).append(d)

    blocks = []
    for gname in sorted(groups, key=lambda g: (g == "", g)):
        items = groups[gname]
        lis = []
        for d in items:
            num = f'<span class="idx-num">{esc(d.get("numero",""))}</span>' if d.get("numero") else ""
            lis.append(
                f'<li class="idx-item">'
                f'<a class="idx-link" href="{url(item_path(kind, d["slug"]))}">'
                f'{num}<span class="idx-title">{esc(d["title"])}</span></a>'
                f'<p class="idx-desc">{esc(summary_of(d))}</p>'
                + (f'<p class="idx-meta">{esc(d.get("meta",""))}</p>' if d.get("meta") else "")
                + "</li>"
            )
        head = f'<h2 class="group-title">{esc(gname)}</h2>' if gname else ""
        blocks.append(head + '<ul class="idx-list">' + "".join(lis) + "</ul>")

    extra = ""
    if kind == "notions":
        extra = (f'<p class="data-note">Ce glossaire est également publié comme thésaurus '
                 f'<a href="{url("/data/vocabulaire.jsonld")}">SKOS en JSON-LD</a>, '
                 f'réutilisable sous licence CC BY-SA.</p>')

    body = f"""
{breadcrumb_html(trail)}
<header class="section-head">
  <p class="kicker">Rubrique</p>
  <h1>{esc(sec['title'])}</h1>
  <p class="lede">{esc(sec['lede'])}</p>
  <p class="count">{len(docs)} {esc(sec['plural'])}</p>
  {extra}
</header>
{''.join(blocks)}
"""
    ld = {
        "@type": "CollectionPage",
        "@id": canonical(f"/{sec['slug']}/") + "#collection",
        "name": sec["title"],
        "description": sec["lede"],
        "url": canonical(f"/{sec['slug']}/"),
        "inLanguage": "fr",
        "isPartOf": {"@id": BASE + "/#site"},
        "hasPart": [{"@id": canonical(item_path(kind, d["slug"])) + ("#terme" if kind == "notions" else "#personne" if kind == "figures" else "#article")} for d in docs],
    }
    extra_ld = [ld]
    if kind == "notions":
        extra_ld.append({
            "@type": "DefinedTermSet",
            "@id": BASE + "/notions/#thesaurus",
            "name": "Vocabulaire critique du nécropatriarcat",
            "description": "Thésaurus des notions mobilisées par l'analyse nécropatriarcale.",
            "url": canonical("/notions/"),
            "inLanguage": "fr",
            "license": SITE["license_url"],
            "hasDefinedTerm": [{"@id": canonical(item_path("notions", d["slug"])) + "#terme"} for d in docs],
        })
    doc_html = page(
        path=f"/{sec['slug']}/",
        title=sec["title"],
        description=sec["lede"],
        body=body,
        active=kind,
        trail=trail,
        jsonld=extra_ld,
        og_image=f"/assets/og/section-{kind}.png",
    )
    (OUT / sec["slug"] / "index.html").write_text(doc_html.replace(TOC_TOKEN, ""), encoding="utf-8")


# --------------------------------------------------------------------------
# Pages spéciales
# --------------------------------------------------------------------------

def build_home(data, index):
    dossiers = data["dossiers"]
    featured = dossiers[:6]
    cards = []
    for d in featured:
        cards.append(f"""
<article class="card">
  <p class="card-kicker">{esc(d.get('rubrique','Dossier'))}</p>
  <h3><a href="{url(item_path('dossiers', d['slug']))}">{esc(d['title'])}</a></h3>
  <p>{esc(summary_of(d))}</p>
</article>""")

    notions_head = "".join(
        f'<li><a href="{url(item_path("notions", n["slug"]))}">{esc(n["title"])}</a></li>'
        for n in data["notions"][:18]
    )
    figures_head = "".join(
        f'<li><a href="{url(item_path("figures", f["slug"]))}">{esc(f["title"])}</a>'
        f'<span>{esc(f.get("role",""))}</span></li>'
        for f in data["figures"][:10]
    )
    cas_head = "".join(
        f'<li><a href="{url(item_path("cas", c["slug"]))}">{esc(c["title"])}</a>'
        f'<span>{esc(c.get("lieu",""))}</span></li>'
        for c in data["cas"][:8]
    )

    body = f"""
<section class="hero">
  <p class="kicker">Encyclopédie critique · {sum(len(data[k]) for k in SECTIONS)} entrées</p>
  <h1>Nécropatriarcat</h1>
  <p class="hero-lede">Il existe un nom pour le moment où la virilité, ayant perdu les moyens de se prouver
  par ce qu'elle produit, se prouve par ce qu'elle détruit. Sayak Valencia l'a appelé le
  <strong>nécropatriarcat</strong>&nbsp;: le privilège, accordé au corps masculin par l'ordre patriarcal,
  d'exercer pour son propre compte les techniques de la nécropolitique.</p>
  <p class="hero-sub">Ce site rassemble la généalogie du concept, ses mécanismes, ses chiffres,
  ses cas documentés et les contre-pédagogies qui lui font face. Tout y est sourcé, daté et librement réutilisable.</p>
  <p class="hero-actions">
    <a class="btn" href="{url('/dossiers/necropatriarcat-definition/')}">Commencer par la définition</a>
    <a class="btn btn-ghost" href="{url("/dossiers/")}">Les {len(dossiers)} dossiers</a>
  </p>
</section>

<section class="home-block" aria-labelledby="h-dossiers">
  <div class="block-head">
    <h2 id="h-dossiers">Dossiers</h2>
    <a class="more" href="{url('/dossiers/')}">Les {len(dossiers)} dossiers →</a>
  </div>
  <div class="cards">{''.join(cards)}</div>
</section>

<section class="home-block two-col" aria-labelledby="h-notions">
  <div>
    <div class="block-head"><h2 id="h-notions">Notions</h2><a class="more" href="{url('/notions/')}">Glossaire →</a></div>
    <ul class="taglist">{notions_head}</ul>
  </div>
  <div>
    <div class="block-head"><h2 id="h-figures">Figures</h2><a class="more" href="{url('/figures/')}">Toutes →</a></div>
    <ul class="minilist">{figures_head}</ul>
  </div>
</section>

<section class="home-block" aria-labelledby="h-cas">
  <div class="block-head"><h2 id="h-cas">Cas documentés</h2><a class="more" href="{url('/cas/')}">Tous les cas →</a></div>
  <ul class="minilist cols">{cas_head}</ul>
</section>

<section class="home-block note" aria-labelledby="h-note">
  <h2 id="h-note">Comment ce site est fait</h2>
  <p>Chaque page indique ses sources, une par une, avec leur lien. Le texte a été rédigé par
  <strong>Claude (Opus 5)</strong>, un modèle de langage&nbsp;; la méthode, ses limites et ce qu'il faut
  en penser sont exposés sans détour dans la page <a href="{url('/methode/')}">Méthode</a>.
  Les données du site — thésaurus, corpus, bibliographie — sont publiées en
  <a href="{url('/data/vocabulaire.jsonld')}">JSON-LD</a> pour être réutilisées ailleurs.</p>
</section>
"""
    doc_html = page(
        path="/",
        title="Nécropatriarcat — atlas critique d'une économie de la mort",
        description=SITE["description"],
        body=body,
        active="home",
        jsonld=[{
            "@type": "CollectionPage",
            "@id": BASE + "/#accueil",
            "name": "Nécropatriarcat",
            "url": BASE + "/",
            "inLanguage": "fr",
            "description": SITE["description"],
            "isPartOf": {"@id": BASE + "/#site"},
            "author": AUTHOR_LD,
            "publisher": {"@id": BASE + "/#editeur"},
            "license": SITE["license_url"],
            "about": {"@id": canonical("/notions/necropatriarcat/") + "#terme"},
        }],
        keywords=["nécropatriarcat", "capitalisme gore", "nécropolitique", "Sayak Valencia",
                  "Rita Segato", "Achille Mbembe", "féminicide", "pédagogie de la cruauté",
                  "transféminisme", "violence lente", "injustice épistémique"],
    )
    (OUT / "index.html").write_text(doc_html.replace(TOC_TOKEN, ""), encoding="utf-8")


def build_simple_page(doc, index, data):
    slug = doc["slug"]
    path = f"/{slug}/"
    body_html, toc = render_markdown(doc["_body"], index)
    sources = render_sources(doc.get("refs"), set(USED_REFS))
    trail = [("Accueil", "/"), (doc["title"], None)]
    extra = ""

    if slug == "chronologie":
        extra = chronologie_html(doc)
    if slug == "bibliographie":
        extra = bibliographie_html(doc)
    if slug == "plan-du-site":
        extra = plan_html(data)
    if slug == "recherche":
        extra = recherche_html()

    body = f"""
{breadcrumb_html(trail)}
<article class="prose">
  <header class="article-head">
    <p class="kicker">Page</p>
    <h1>{esc(doc['title'])}</h1>
    {'<p class="lede">' + esc(doc.get('description','')) + '</p>' if doc.get('description') else ''}
  </header>
  {TOC_TOKEN}
  <div class="article-body">
{body_html}
{extra}
  </div>
  {sources}
</article>
"""
    ld = [{
        "@type": "WebPage",
        "@id": canonical(path) + "#page",
        "name": doc["title"],
        "url": canonical(path),
        "description": doc.get("description", ""),
        "inLanguage": "fr",
        "isPartOf": {"@id": BASE + "/#site"},
        "author": AUTHOR_LD,
        "publisher": {"@id": BASE + "/#editeur"},
        "license": SITE["license_url"],
    }]
    if slug == "chronologie":
        ld.append(chronologie_ld(doc))
    if slug == "bibliographie":
        ld.append(bibliographie_ld(doc))

    doc_html = page(
        path=path, title=doc["title"], description=doc.get("description", ""),
        body=body, active=slug, trail=trail, jsonld=ld,
        keywords=doc.get("keywords"), og_image=f"/assets/og/page-{slug}.png",
        toc=toc,
    )
    block = ""
    if toc and toc.count("<li") > 2 and slug not in ("recherche",):
        block = ('<aside class="toc" aria-labelledby="toc-titre">'
                 '<h2 id="toc-titre" class="toc-titre">Sur cette page</h2>'
                 + toc.replace('<div class="toc">', "").replace("</div>", "") + "</aside>")
    (OUT / slug / "index.html").write_text(doc_html.replace(TOC_TOKEN, block), encoding="utf-8")
    doc["_path"] = path
    doc["_text"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body_html)).strip()


def chronologie_html(doc):
    rows = []
    for ev in doc.get("events", []):
        tags = "".join(f'<span class="tl-tag">{esc(t)}</span>' for t in ev.get("tags", []))
        link = ""
        if ev.get("link"):
            link = f' <a class="tl-link" href="{url(ev["link"])}">→</a>'
        rows.append(f"""
<li class="tl-item" id="ev-{esc(slugify(str(ev['annee']) + '-' + ev['titre'][:24]))}">
  <div class="tl-date"><time datetime="{esc(ev.get('iso', ev['annee']))}">{esc(ev['annee'])}</time></div>
  <div class="tl-body">
    <h3>{esc(ev['titre'])}{link}</h3>
    <p>{esc(ev['texte'])}</p>
    <p class="tl-tags">{tags}</p>
  </div>
</li>""")
    return '<ol class="timeline">' + "".join(rows) + "</ol>"


def chronologie_ld(doc):
    items = []
    for i, ev in enumerate(doc.get("events", []), start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Event",
                "name": ev["titre"],
                "startDate": str(ev.get("iso", ev["annee"])),
                "description": ev["texte"],
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            },
        })
    return {"@type": "ItemList", "@id": canonical("/chronologie/") + "#liste",
            "name": "Chronologie du nécropatriarcat", "numberOfItems": len(items),
            "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "itemListElement": items}


def bibliographie_html(doc):
    groups = {}
    for e in doc.get("entries", []):
        groups.setdefault(e.get("groupe", "Divers"), []).append(e)
    out = []
    for gname in doc.get("ordre", list(groups)):
        entries = groups.get(gname)
        if not entries:
            continue
        lis = []
        for e in sorted(entries, key=lambda x: (x.get("auteur", ""), str(x.get("annee", "")))):
            link = f' <a href="{esc(e["url"])}" rel="noopener nofollow">↗</a>' if e.get("url") else ""
            note = f'<span class="bib-note">{esc(e["note"])}</span>' if e.get("note") else ""
            lis.append(
                f'<li class="bib-item" itemscope itemtype="https://schema.org/CreativeWork">'
                f'<span class="bib-auteur" itemprop="author">{esc(e.get("auteur",""))}</span>, '
                f'<cite itemprop="name">{esc(e.get("titre",""))}</cite>'
                f'{", " + esc(e["editeur"]) if e.get("editeur") else ""}'
                f'{", " + str(e["annee"]) if e.get("annee") else ""}.{link}{note}</li>'
            )
        out.append(f'<h2 id="{slugify(gname)}">{esc(gname)}</h2><ul class="biblio">' + "".join(lis) + "</ul>")
    return "".join(out)


def bibliographie_ld(doc):
    items = []
    for i, e in enumerate(doc.get("entries", []), start=1):
        w = {"@type": "CreativeWork", "name": e.get("titre", "")}
        if e.get("auteur"):
            w["author"] = {"@type": "Person", "name": e["auteur"]}
        if e.get("annee"):
            w["datePublished"] = str(e["annee"])
        if e.get("editeur"):
            w["publisher"] = {"@type": "Organization", "name": e["editeur"]}
        if e.get("url"):
            w["url"] = e["url"]
        items.append({"@type": "ListItem", "position": i, "item": w})
    return {"@type": "ItemList", "@id": canonical("/bibliographie/") + "#liste",
            "name": "Bibliographie", "numberOfItems": len(items), "itemListElement": items}


def plan_html(data):
    out = []
    for key, sec in sorted(SECTIONS.items(), key=lambda kv: kv[1]["order"]):
        lis = "".join(
            f'<li><a href="{url(item_path(key, d["slug"]))}">{esc(d["title"])}</a></li>'
            for d in data[key]
        )
        out.append(f'<h2>{esc(sec["title"])}</h2><ul class="plan-list">{lis}</ul>')
    lis = "".join(f'<li><a href="{url("/" + p + "/")}">{esc(p.replace("-", " ").capitalize())}</a></li>'
                  for p in PAGES_ORDER)
    out.append(f"<h2>Pages</h2><ul class=\"plan-list\">{lis}</ul>")
    out.append(f"""<h2>Données ouvertes</h2><ul class="plan-list">
<li><a href="{url('/data/vocabulaire.jsonld')}">vocabulaire.jsonld</a> — thésaurus SKOS des notions</li>
<li><a href="{url('/data/corpus.jsonld')}">corpus.jsonld</a> — l'ensemble des pages en schema.org</li>
<li><a href="{url('/data/index.json')}">index.json</a> — index de recherche</li>
<li><a href="{url('/sitemap.xml')}">sitemap.xml</a></li>
<li><a href="{url('/feed.xml')}">feed.xml</a> — flux Atom</li>
</ul>""")
    return "".join(out)


def recherche_html():
    return f"""
<div class="search-app">
  <form class="search-form" role="search" onsubmit="return false;">
    <label for="q">Chercher dans les {'{n}'} pages du site</label>
    <input type="search" id="q" name="q" autocomplete="off" spellcheck="false"
           placeholder="féminicide, endriago, violence lente, Segato…" autofocus>
  </form>
  <p class="search-status" id="search-status" role="status">Tapez au moins deux lettres.</p>
  <ol class="search-results" id="search-results"></ol>
  <noscript><p>La recherche nécessite JavaScript. Sans JavaScript, utilisez le
  <a href="{url('/plan-du-site/')}">plan du site</a>, qui liste toutes les pages.</p></noscript>
</div>
"""


# --------------------------------------------------------------------------
# Fichiers annexes
# --------------------------------------------------------------------------

def write_sitemap(entries):
    now = date.today().isoformat()
    urls = []
    for e in entries:
        urls.append(f"""  <url>
    <loc>{canonical(e['path'])}</loc>
    <lastmod>{e.get('lastmod', now)}</lastmod>
    <changefreq>{e.get('freq','monthly')}</changefreq>
    <priority>{e.get('prio','0.7')}</priority>
  </url>""")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    (OUT / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_robots():
    txt = f"""User-agent: *
Allow: /

Sitemap: {SITE['origin']}{url('/sitemap.xml')}
"""
    (OUT / "robots.txt").write_text(txt, encoding="utf-8")


def write_feed(data):
    items = []
    pool = [(d, "dossiers") for d in data["dossiers"]] + [(d, "cas") for d in data["cas"]]
    pool.sort(key=lambda t: str(t[0].get("date", "")), reverse=True)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for d, kind in pool[:40]:
        u = canonical(item_path(kind, d["slug"]))
        dt = str(d.get("date", date.today())) + "T09:00:00Z"
        items.append(f"""  <entry>
    <title type="text">{esc(d['title'])}</title>
    <link href="{u}"/>
    <id>{u}</id>
    <updated>{dt}</updated>
    <published>{dt}</published>
    <author><name>{esc(SITE['author_name'])}</name></author>
    <category term="{esc(SECTIONS[kind]['title'])}"/>
    <summary type="text">{esc(summary_of(d))}</summary>
    <rights>{esc(SITE['license_name'])}</rights>
  </entry>""")
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="fr">
  <title>Nécropatriarcat — atlas critique</title>
  <subtitle>{esc(SITE['description'][:200])}</subtitle>
  <link href="{BASE}/" rel="alternate"/>
  <link href="{SITE['origin']}{url('/feed.xml')}" rel="self"/>
  <id>{BASE}/</id>
  <updated>{updated}</updated>
  <rights>{esc(SITE['license_name'])}</rights>
{chr(10).join(items)}
</feed>
"""
    (OUT / "feed.xml").write_text(xml, encoding="utf-8")


def write_data(data, index):
    (OUT / "data").mkdir(parents=True, exist_ok=True)

    # --- Thésaurus SKOS -----------------------------------------------------
    concepts = []
    for n in data["notions"]:
        node = {
            "@id": canonical(item_path("notions", n["slug"])) + "#concept",
            "@type": "skos:Concept",
            "skos:prefLabel": {"@language": "fr", "@value": n["title"]},
            "skos:definition": {"@language": "fr", "@value": n.get("definition", n.get("description", ""))},
            "skos:inScheme": {"@id": BASE + "/notions/#scheme"},
            "foaf:page": canonical(item_path("notions", n["slug"])),
        }
        if n.get("alt"):
            node["skos:altLabel"] = [{"@language": "fr", "@value": a} for a in n["alt"]]
        if n.get("en"):
            node["skos:prefLabel"] = [node["skos:prefLabel"],
                                      {"@language": "en", "@value": n["en"]}]
        if n.get("broader"):
            node["skos:broader"] = [{"@id": canonical(item_path("notions", s)) + "#concept"}
                                    for s in n["broader"] if f"notions/{s}" in index]
        if n.get("about"):
            node["skos:related"] = [{"@id": canonical(item_path("notions", s)) + "#concept"}
                                    for s in n["about"] if f"notions/{s}" in index]
        if n.get("wikidata"):
            node["skos:closeMatch"] = {"@id": n["wikidata"]}
        concepts.append(node)

    skos = {
        "@context": {
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "dct": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
        },
        "@graph": [{
            "@id": BASE + "/notions/#scheme",
            "@type": "skos:ConceptScheme",
            "dct:title": {"@language": "fr", "@value": "Vocabulaire critique du nécropatriarcat"},
            "dct:description": {"@language": "fr", "@value":
                                "Thésaurus des notions mobilisées par l'analyse nécropatriarcale."},
            "dct:license": SITE["license_url"],
            "dct:creator": SITE["author_name"],
            "dct:publisher": SITE["editor"],
            "dct:modified": date.today().isoformat(),
            "skos:hasTopConcept": [{"@id": canonical(item_path("notions", "necropatriarcat")) + "#concept"}],
        }] + concepts,
    }
    (OUT / "data" / "vocabulaire.jsonld").write_text(
        json.dumps(skos, ensure_ascii=False, indent=1), encoding="utf-8")

    # --- Corpus schema.org --------------------------------------------------
    parts = []
    for kind in SECTIONS:
        for d in data[kind]:
            parts.append({
                "@type": {"dossiers": "ScholarlyArticle", "cas": "Article",
                          "notions": "DefinedTerm", "figures": "Person"}[kind],
                "@id": canonical(item_path(kind, d["slug"])),
                "name": d["title"],
                "description": summary_of(d),
                "url": canonical(item_path(kind, d["slug"])),
                "inLanguage": "fr",
                "genre": SECTIONS[kind]["title"],
                "datePublished": str(d.get("date", "")),
            })
    corpus = {
        "@context": "https://schema.org",
        "@type": "DataCatalog",
        "@id": BASE + "/data/corpus.jsonld",
        "name": "Corpus Nécropatriarcat",
        "description": "L'ensemble des pages du site, décrites en schema.org.",
        "url": BASE + "/",
        "license": SITE["license_url"],
        "creator": AUTHOR_LD,
        "publisher": PUBLISHER_LD,
        "dateModified": date.today().isoformat(),
        "dataset": {
            "@type": "Dataset",
            "name": "Entrées de l'atlas",
            "description": "Dossiers, notions, figures et cas.",
            "license": SITE["license_url"],
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "application/ld+json",
                 "contentUrl": BASE + "/data/corpus.jsonld"},
                {"@type": "DataDownload", "encodingFormat": "application/ld+json",
                 "contentUrl": BASE + "/data/vocabulaire.jsonld"},
            ],
        },
        "hasPart": parts,
    }
    (OUT / "data" / "corpus.jsonld").write_text(
        json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8")

    # --- Index de recherche -------------------------------------------------
    idx = []
    for kind in SECTIONS:
        for d in data[kind]:
            idx.append({
                "u": url(item_path(kind, d["slug"])),
                "t": d["title"],
                "k": SECTIONS[kind]["singular"],
                "d": summary_of(d)[:220],
                "x": (d.get("_text", "")[:2400]).lower(),
            })
    for d in data["pages"]:
        idx.append({"u": url(f"/{d['slug']}/"), "t": d["title"], "k": "page",
                    "d": d.get("description", "")[:220],
                    "x": (d.get("_text", "")[:1800]).lower()})
    (OUT / "data" / "index.json").write_text(
        json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(idx)


def write_humans():
    txt = """/* AUTEUR */
    Texte : Claude (Opus 5), modèle de langage d'Anthropic
    Édition : ouaisfieu
    Site : https://ouaisfieu.github.io/necropatriarcat/
    Code : https://github.com/ouaisfieu/necropatriarcat

/* TECHNIQUE */
    Site statique, HTML servi tel quel
    Aucun framework, aucun traceur, aucun cookie, aucune requête tierce
    Polices système uniquement
    Données ouvertes : /data/vocabulaire.jsonld (SKOS), /data/corpus.jsonld

/* LICENCE */
    Contenus : CC BY-SA 4.0
"""
    (OUT / "humans.txt").write_text(txt, encoding="utf-8")


def write_manifest():
    m = {
        "name": "Nécropatriarcat — atlas critique",
        "short_name": "Nécropatriarcat",
        "description": SITE["description"][:200],
        "start_url": url("/"),
        "scope": url("/"),
        "display": "minimal-ui",
        "background_color": "#faf8f5",
        "theme_color": "#111015",
        "lang": "fr",
        "icons": [{"src": url("/assets/favicon.svg"), "sizes": "any", "type": "image/svg+xml"}],
    }
    (OUT / "manifest.webmanifest").write_text(json.dumps(m, ensure_ascii=False, indent=1),
                                              encoding="utf-8")


def write_404():
    body = """
<section class="hero">
  <p class="kicker">Erreur 404</p>
  <h1>Cette page n'existe pas</h1>
  <p class="hero-lede">Le lien est peut-être ancien, ou l'adresse mal recopiée.</p>
  <p class="hero-actions">
    <a class="btn" href="%s">Retour à l'accueil</a>
    <a class="btn btn-ghost" href="%s">Plan du site</a>
    <a class="btn btn-ghost" href="%s">Rechercher</a>
  </p>
</section>
""" % (url("/"), url("/plan-du-site/"), url("/recherche/"))
    doc = page(path="/404", title="Page introuvable", description="Erreur 404.", body=body)
    (OUT / "404.html").write_text(doc.replace(TOC_TOKEN, ""), encoding="utf-8")
    shutil.rmtree(OUT / "404", ignore_errors=True)


# --------------------------------------------------------------------------
# Images Open Graph
# --------------------------------------------------------------------------

def make_og_images(data):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  · Pillow absent : images OG non régénérées")
        return
    outdir = OUT / "assets" / "og"
    outdir.mkdir(parents=True, exist_ok=True)

    serif = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    serif_b = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not Path(serif_b).exists():
        print("  · polices absentes : images OG non régénérées")
        return

    BGC = (17, 16, 21)
    FG = (240, 237, 231)
    ACC = (200, 78, 66)
    MUT = (150, 145, 138)

    def draw_card(filename, kicker, title):
        img = Image.new("RGB", (1200, 630), BGC)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 1200, 8], fill=ACC)
        f_k = ImageFont.truetype(sans, 24)
        f_b = ImageFont.truetype(sans, 22)
        d.text((72, 70), kicker.upper(), font=f_k, fill=ACC)

        size = 62 if len(title) < 46 else (52 if len(title) < 76 else 44)
        f_t = ImageFont.truetype(serif_b, size)
        words, lines, cur = title.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textlength(test, font=f_t) > 1056:
                lines.append(cur)
                cur = w
            else:
                cur = test
        lines.append(cur)
        lines = lines[:5]
        y = 160
        for line in lines:
            d.text((72, y), line, font=f_t, fill=FG)
            y += int(size * 1.32)
        d.line([(72, 540), (1128, 540)], fill=(58, 56, 64), width=1)
        d.text((72, 562), "NÉCROPATRIARCAT — ATLAS CRITIQUE", font=f_b, fill=MUT)
        d.text((820, 562), "ouaisfieu.github.io", font=f_b, fill=MUT)
        img.save(outdir / filename, "PNG", optimize=True)

    draw_card("default.png", "Encyclopédie critique",
              "Nécropatriarcat — atlas critique d'une économie de la mort")
    for kind, sec in SECTIONS.items():
        draw_card(f"section-{kind}.png", "Rubrique", sec["title"])
        for d in data[kind]:
            draw_card(f"{kind}-{d['slug']}.png", sec["singular"], d["title"])
    for p in data["pages"]:
        draw_card(f"page-{p['slug']}.png", "Page", p["title"])
    print(f"  · images Open Graph : {len(list(outdir.glob('*.png')))}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    data, index = load_all()
    counts = {k: len(v) for k, v in data.items()}
    print("Contenu :", counts)

    for kind in SECTIONS:
        for doc in data[kind]:
            build_item(doc, kind, index)
        build_section_index(kind, data[kind], index)

    for doc in data["pages"]:
        build_simple_page(doc, index, data)

    build_home(data, index)
    write_404()

    # assets
    assets_src = ROOT / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, OUT / "assets", dirs_exist_ok=True)

    n = write_data(data, index)
    # injecte le nombre de pages dans la page recherche
    rp = OUT / "recherche" / "index.html"
    if rp.exists():
        rp.write_text(rp.read_text(encoding="utf-8").replace("{n}", str(n)), encoding="utf-8")

    entries = [{"path": "/", "prio": "1.0", "freq": "weekly"}]
    for kind, sec in SECTIONS.items():
        entries.append({"path": f"/{sec['slug']}/", "prio": "0.9", "freq": "weekly"})
        for d in data[kind]:
            entries.append({"path": item_path(kind, d["slug"]), "prio": "0.8",
                            "lastmod": str(d.get("updated", d.get("date", date.today())))})
    for p in PAGES_ORDER:
        entries.append({"path": f"/{p}/", "prio": "0.6"})
    write_sitemap(entries)
    write_robots()
    write_feed(data)
    write_manifest()
    write_humans()
    make_og_images(data)

    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    for extra in ("LICENSE", "CITATION.cff"):
        src = ROOT / extra
        if src.exists():
            shutil.copy(src, OUT / extra)

    total = sum(1 for _ in OUT.rglob("*.html"))
    print(f"OK — {total} pages HTML générées dans {OUT}")


if __name__ == "__main__":
    main()
