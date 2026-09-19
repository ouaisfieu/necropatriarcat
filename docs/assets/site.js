/* Nécropatriarcat — script unique, facultatif.
   Le site fonctionne intégralement sans JavaScript ; ce fichier n'ajoute que
   le basculement de thème et la recherche côté client. Aucune dépendance,
   aucun traceur, aucune requête réseau hors du site lui-même. */
(function () {
  'use strict';

  /* ---------------- thème clair / sombre ---------------- */
  var KEY = 'necro-theme';
  var root = document.documentElement;

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function store(v) {
    try { localStorage.setItem(KEY, v); } catch (e) { /* mode privé : on ignore */ }
  }

  var saved = stored();
  if (saved === 'dark' || saved === 'light') root.setAttribute('data-theme', saved);

  var toggle = document.querySelector('[data-theme-toggle]');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var dark = root.getAttribute('data-theme') === 'dark' ||
        (!root.hasAttribute('data-theme') &&
          window.matchMedia('(prefers-color-scheme: dark)').matches);
      var next = dark ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store(next);
      toggle.setAttribute('aria-label',
        next === 'dark' ? 'Passer au thème clair' : 'Passer au thème sombre');
    });
  }

  /* ---------------- recherche ---------------- */
  var input = document.getElementById('q');
  if (!input) return;

  var results = document.getElementById('search-results');
  var status = document.getElementById('search-status');
  var base = (document.querySelector('link[rel="stylesheet"]').getAttribute('href') || '')
    .replace(/assets\/style\.css.*$/, '');
  var data = null;
  var pending = null;

  function fold(s) {
    return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function load() {
    if (data) return Promise.resolve(data);
    if (pending) return pending;
    pending = fetch(base + 'data/index.json')
      .then(function (r) { return r.json(); })
      .then(function (j) {
        data = j.map(function (e) {
          e._t = fold(e.t); e._d = fold(e.d || ''); e._x = fold(e.x || '');
          return e;
        });
        return data;
      })
      .catch(function () {
        status.textContent = "L'index de recherche n'a pas pu être chargé.";
        return [];
      });
    return pending;
  }

  function excerpt(entry, q) {
    var i = entry._x.indexOf(q);
    if (i < 0) return entry.d || '';
    var start = Math.max(0, i - 70);
    var raw = entry.x.substring(start, start + 220);
    return (start > 0 ? '…' : '') + raw + '…';
  }

  function highlight(text, q) {
    var folded = fold(text);
    var i = folded.indexOf(q);
    if (i < 0) return escapeHtml(text);
    return escapeHtml(text.slice(0, i)) + '<mark>' +
      escapeHtml(text.slice(i, i + q.length)) + '</mark>' +
      escapeHtml(text.slice(i + q.length));
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function search(raw) {
    var q = fold(raw.trim());
    results.innerHTML = '';
    if (q.length < 2) {
      status.textContent = 'Tapez au moins deux lettres.';
      return;
    }
    load().then(function (list) {
      var hits = [];
      for (var i = 0; i < list.length; i++) {
        var e = list[i], score = 0;
        if (e._t.indexOf(q) === 0) score += 120;
        else if (e._t.indexOf(q) > -1) score += 80;
        if (e._d.indexOf(q) > -1) score += 25;
        var pos = e._x.indexOf(q);
        if (pos > -1) score += 12;
        if (score > 0) hits.push([score, e]);
      }
      hits.sort(function (a, b) { return b[0] - a[0]; });
      status.textContent = hits.length
        ? hits.length + (hits.length > 1 ? ' résultats' : ' résultat')
        : 'Aucun résultat pour « ' + raw + ' ».';
      var frag = document.createDocumentFragment();
      hits.slice(0, 40).forEach(function (pair) {
        var e = pair[1];
        var li = document.createElement('li');
        li.innerHTML = '<span class="res-kind">' + escapeHtml(e.k) + '</span>' +
          '<a href="' + escapeHtml(e.u) + '">' + highlight(e.t, q) + '</a>' +
          '<p>' + highlight(excerpt(e, q), q) + '</p>';
        frag.appendChild(li);
      });
      results.appendChild(frag);
    });
  }

  var timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    var v = input.value;
    timer = setTimeout(function () { search(v); }, 120);
  });

  var initial = new URLSearchParams(location.search).get('q');
  if (initial) { input.value = initial; search(initial); }
  load();
})();
