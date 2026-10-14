/* Musterwil – online counter forms.
   data-form-mode="simple": validate, then go straight to the confirmation page.
   data-form-mode="review": validate with field messages, show a review step, require confirmation. */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  function problemOf(input) {
    var value = input.value.trim();
    if ((input.hasAttribute('data-required') || input.required) && !value) { return 'required'; }
    var pattern = input.getAttribute('data-pattern');
    if (value && pattern && !(new RegExp(pattern)).test(value)) { return 'format'; }
    if (value && input.getAttribute('data-kind') === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) { return 'format'; }
    return '';
  }

  function checkedFields(form) {
    return Array.prototype.slice.call(
      form.querySelectorAll('[data-required], [required], [data-pattern], [data-kind]')
    ).filter(function (el) { return el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA'; });
  }

  function setupSimple(form) {
    var summary = form.querySelector('[data-error-summary]');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var invalid = 0;
      checkedFields(form).forEach(function (field) {
        var problem = problemOf(field);
        var errorEl = field.getAttribute('data-error-id') ? document.getElementById(field.getAttribute('data-error-id')) : null;
        field.classList.toggle('is-invalid', !!problem);
        if (errorEl) {
          errorEl.hidden = !problem;
          errorEl.textContent = problem ? errorEl.getAttribute('data-msg') : '';
        }
        if (problem) { invalid += 1; }
      });
      if (invalid) {
        summary.textContent = form.getAttribute('data-msg-error');
        summary.hidden = false;
        summary.scrollIntoView({ block: 'center', behavior: 'smooth' });
        return;
      }
      summary.hidden = true;
      window.location.href = form.getAttribute('data-success');
    });
  }

  function setupReview(form) {
    var summary = form.querySelector('[data-error-summary]');
    var editStep = form.querySelector('[data-step-edit]');
    var review = form.querySelector('[data-review]');
    var reviewList = form.querySelector('[data-review-list]');
    var confirmBox = form.querySelector('[data-confirm]');
    var confirmError = form.querySelector('[data-confirm-error]');
    var back = form.querySelector('[data-review-back]');

    function toEdit() {
      form.setAttribute('data-phase', 'edit');
      review.hidden = true;
      editStep.hidden = false;
      var first = editStep.querySelector('input');
      if (first) { first.focus(); }
    }
    if (back) { back.addEventListener('click', toEdit); }

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      if (form.getAttribute('data-phase') === 'review') {
        if (!confirmBox.checked) {
          confirmError.hidden = false;
          confirmBox.setAttribute('aria-invalid', 'true');
          confirmBox.focus();
          return;
        }
        window.location.href = form.getAttribute('data-success');
        return;
      }

      var errors = [];
      checkedFields(form).forEach(function (field) {
        var problem = problemOf(field);
        var errorEl = document.getElementById(field.getAttribute('data-error-id'));
        if (problem) {
          var message = field.getAttribute(problem === 'required' ? 'data-msg-required' : 'data-msg-format');
          if (errorEl) { errorEl.textContent = message; errorEl.hidden = false; }
          field.setAttribute('aria-invalid', 'true');
          field.classList.add('is-invalid');
          errors.push({ field: field, message: message });
        } else {
          if (errorEl) { errorEl.textContent = ''; errorEl.hidden = true; }
          field.removeAttribute('aria-invalid');
          field.classList.remove('is-invalid');
        }
      });

      if (errors.length) {
        summary.innerHTML = '';
        var heading = document.createElement('p');
        heading.textContent = form.getAttribute('data-msg-summary').replace('{n}', errors.length);
        var list = document.createElement('ul');
        errors.forEach(function (err) {
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = '#' + err.field.id;
          a.textContent = err.message;
          li.appendChild(a);
          list.appendChild(li);
        });
        heading.style.margin = '0';
        summary.appendChild(heading);
        summary.appendChild(list);
        summary.hidden = false;
        summary.focus();
        return;
      }

      summary.hidden = true;
      reviewList.innerHTML = '';
      form.querySelectorAll('[data-review-label]').forEach(function (field) {
        var value = field.value.trim();
        if (!value) { return; }
        var dt = document.createElement('dt');
        var dd = document.createElement('dd');
        dt.textContent = field.getAttribute('data-review-label');
        dd.textContent = value;
        reviewList.appendChild(dt);
        reviewList.appendChild(dd);
      });
      editStep.hidden = true;
      review.hidden = false;
      form.setAttribute('data-phase', 'review');
      var title = review.querySelector('h2');
      if (title) { title.focus(); }
    });
  }

  document.querySelectorAll('form[data-form-mode]').forEach(function (form) {
    form.setAttribute('novalidate', '');
    if (form.getAttribute('data-form-mode') === 'review') { setupReview(form); } else { setupSimple(form); }
  });
});
