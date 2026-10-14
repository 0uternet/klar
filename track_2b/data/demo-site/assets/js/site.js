/* Musterwil – shared behaviour: mobile menu, print, practice view, feedback form */
(function () {
  'use strict';

  function showFeedbackThanks(form) {
    if (!form) { return; }
    var status = form.querySelector('[data-feedback-status]');
    if (status) {
      status.hidden = false;
      status.textContent = status.getAttribute('data-msg') || '';
    }
    form.reset();
  }

  window.sendFeedback = function (el) {
    showFeedbackThanks(el.closest('form'));
  };

  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.querySelector('[data-nav-toggle]');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var open = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!open));
        document.body.classList.toggle('nav-open', !open);
      });
    }

    document.querySelectorAll('[data-print]').forEach(function (btn) {
      btn.addEventListener('click', function () { window.print(); });
    });

    document.querySelectorAll('[data-practice]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var out = document.getElementById(btn.getAttribute('data-practice'));
        if (out) { out.textContent = btn.getAttribute('data-practice-msg') || ''; }
      });
    });

    document.querySelectorAll('form[data-feedback-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        showFeedbackThanks(form);
      });
    });
  });
})();
