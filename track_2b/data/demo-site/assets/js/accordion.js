/* Musterwil – FAQ accordion */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  document.querySelectorAll('.acc-toggle').forEach(function (toggle) {
    toggle.addEventListener('click', function () {
      var item = toggle.closest('.acc-item');
      var open = !item.classList.contains('is-open');
      item.classList.toggle('is-open', open);
      if (toggle.tagName === 'BUTTON') {
        toggle.setAttribute('aria-expanded', String(open));
        var panel = document.getElementById(toggle.getAttribute('aria-controls'));
        if (panel) { panel.hidden = !open; }
      }
    });
  });
});
