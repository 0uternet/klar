/* Musterwil – filters a list on the same page */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';
  document.querySelectorAll('[data-filter-target]').forEach(function (select) {
    var list = document.getElementById(select.getAttribute('data-filter-target'));
    var status = document.getElementById(select.getAttribute('data-filter-status'));
    if (!list) { return; }
    function apply() {
      var value = select.value;
      var count = 0;
      list.querySelectorAll('[data-category]').forEach(function (item) {
        var visible = value === 'all' || item.getAttribute('data-category') === value;
        item.hidden = !visible;
        if (visible) { count += 1; }
      });
      if (status) { status.textContent = status.getAttribute('data-template').replace('{n}', count); }
    }
    select.addEventListener('change', apply);
    apply();
  });
});
