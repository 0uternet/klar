/* Musterwil – client-side search over window.SEARCH_INDEX */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  var form = document.querySelector('[data-search-form]');
  if (!form) { return; }
  var input = form.querySelector('input[type="search"]');
  var list = document.querySelector('[data-search-results]');
  var status = document.querySelector('[data-search-status]');
  var index = window.SEARCH_INDEX || [];

  function norm(s) {
    return s.toLowerCase()
      .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue')
      .normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  function msg(name, n, q) {
    return (status.getAttribute(name) || '').replace('{n}', n).replace('{q}', q);
  }
  function run(query) {
    var q = query.trim();
    list.innerHTML = '';
    if (!q) { status.textContent = msg('data-msg-empty', 0, ''); return; }
    var terms = norm(q).split(/\s+/);
    var hits = index.filter(function (entry) {
      var hay = norm(entry.title + ' ' + entry.text + ' ' + (entry.keywords || ''));
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    });
    status.textContent = hits.length ? msg('data-msg-count', hits.length, q) : msg('data-msg-none', 0, q);
    hits.forEach(function (hit) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      var p = document.createElement('p');
      a.href = hit.url;
      a.textContent = hit.title;
      p.textContent = hit.text;
      li.appendChild(a);
      li.appendChild(p);
      list.appendChild(li);
    });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    run(input.value);
    try {
      window.history.replaceState(null, '', '?q=' + encodeURIComponent(input.value.trim()));
    } catch (err) {
      /* history API unavailable (for example on some file URLs) */
    }
  });

  var initial = new URLSearchParams(window.location.search).get('q');
  if (initial) { input.value = initial; }
  run(initial || '');
});
