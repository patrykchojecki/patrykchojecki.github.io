(function () {
  'use strict';

  var dialog = document.querySelector('.project-preview');
  var previews = Array.from(document.querySelectorAll('[data-project-preview]'));
  if (!dialog || typeof dialog.showModal !== 'function' || !previews.length) return;

  var image = dialog.querySelector('img');
  var title = dialog.querySelector('h2');
  var position = dialog.querySelector('[data-preview-position]');
  var error = dialog.querySelector('.project-preview__error');
  var previous = dialog.querySelector('[data-preview-previous]');
  var next = dialog.querySelector('[data-preview-next]');
  var index = 0;
  var opener;
  var animation;

  function showProject(nextIndex) {
    index = (nextIndex + previews.length) % previews.length;
    var preview = previews[index];
    title.textContent = preview.dataset.projectTitle;
    image.hidden = false;
    error.hidden = true;
    image.alt = preview.querySelector('img').alt;
    image.src = preview.href;
    position.textContent = preview.dataset.projectTitle + ' · ' + (index + 1) + ' of ' + previews.length;
  }

  image.addEventListener('error', function () {
    image.hidden = true;
    error.hidden = false;
  });

  previews.forEach(function (preview, previewIndex) {
    preview.setAttribute('aria-haspopup', 'dialog');
    preview.addEventListener('click', function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
      event.preventDefault();
      opener = preview;
      showProject(previewIndex);
      var source = preview.getBoundingClientRect();
      dialog.showModal();
      document.body.classList.add('project-preview-open');

      if (animation) animation.cancel();
      if (typeof dialog.animate !== 'function') return;
      var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var target = dialog.getBoundingClientRect();
      var x = source.left + source.width / 2 - target.left - target.width / 2;
      var y = source.top + source.height / 2 - target.top - target.height / 2;
      animation = dialog.animate(reducedMotion ? [
        { opacity: 0 }, { opacity: 1 }
      ] : [
        { opacity: 0, transform: 'translate(' + x + 'px, ' + y + 'px) scale(' + source.width / target.width + ')' },
        { opacity: 1, transform: 'translate(0, 0) scale(1)' }
      ], {
        duration: reducedMotion ? 120 : 280,
        easing: 'cubic-bezier(0.16, 1, 0.3, 1)'
      });
    });
  });

  previous.addEventListener('click', function () { showProject(index - 1); });
  next.addEventListener('click', function () { showProject(index + 1); });
  dialog.querySelector('[data-preview-close]').addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('keydown', function (event) {
    if (event.key === 'Tab') {
      var close = dialog.querySelector('[data-preview-close]');
      if (event.shiftKey && document.activeElement === close) {
        event.preventDefault();
        next.focus();
      } else if (!event.shiftKey && document.activeElement === next) {
        event.preventDefault();
        close.focus();
      }
      return;
    }
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      showProject(index + (event.key === 'ArrowLeft' ? -1 : 1));
    }
  });
  // Close only when both ends of a click are on the backdrop, not an image drag.
  var backdropPressed = false;
  function onBackdrop(event) {
    var bounds = dialog.getBoundingClientRect();
    return event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom);
  }
  dialog.addEventListener('pointerdown', function (event) { backdropPressed = onBackdrop(event); });
  dialog.addEventListener('click', function (event) {
    if (backdropPressed && onBackdrop(event)) dialog.close();
    backdropPressed = false;
  });
  dialog.addEventListener('close', function () {
    if (animation) animation.cancel();
    document.body.classList.remove('project-preview-open');
    if (opener) opener.focus({ preventScroll: true });
  });
}());
