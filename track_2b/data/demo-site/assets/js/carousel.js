/* Musterwil – image carousel (auto-advance; optional pause button) */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  document.querySelectorAll('[data-carousel]').forEach(function (root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll('.slide'));
    var dots = Array.prototype.slice.call(root.querySelectorAll('.carousel-dot'));
    var delay = parseInt(root.getAttribute('data-interval'), 10) || 5000;
    var index = 0;
    var timer = null;
    if (!slides.length) { return; }

    function show(n) {
      index = (n + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        var active = i === index;
        slide.classList.toggle('is-active', active);
        slide.setAttribute('aria-hidden', active ? 'false' : 'true');
      });
      dots.forEach(function (dot, i) { dot.classList.toggle('is-active', i === index); });
    }
    function stop() {
      if (timer) { window.clearInterval(timer); timer = null; }
    }
    function start() {
      stop();
      timer = window.setInterval(function () { show(index + 1); }, delay);
    }

    var prev = root.querySelector('[data-carousel-prev]');
    var next = root.querySelector('[data-carousel-next]');
    if (prev) { prev.addEventListener('click', function () { show(index - 1); }); }
    if (next) { next.addEventListener('click', function () { show(index + 1); }); }

    var pause = root.querySelector('[data-carousel-pause]');
    if (pause) {
      var label = pause.querySelector('[data-label]');
      var iconPause = pause.querySelector('[data-icon-pause]');
      var iconPlay = pause.querySelector('[data-icon-play]');
      pause.addEventListener('click', function () {
        var running = pause.getAttribute('data-state') !== 'paused';
        if (running) {
          stop();
          pause.setAttribute('data-state', 'paused');
          label.textContent = pause.getAttribute('data-label-play');
        } else {
          start();
          pause.setAttribute('data-state', 'running');
          label.textContent = pause.getAttribute('data-label-pause');
        }
        if (iconPause) { iconPause.hidden = running; }
        if (iconPlay) { iconPlay.hidden = !running; }
      });
    }

    show(0);
    start();
  });
});
