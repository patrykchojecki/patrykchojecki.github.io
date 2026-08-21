(function () {
  'use strict';

  var root = document.documentElement;
  var progressBar = document.querySelector('.site-progress__bar');
  var updateQueued = false;

  function updateProgress() {
    updateQueued = false;
    if (!progressBar) return;

    var scrollRange = root.scrollHeight - window.innerHeight;
    var hasProgress = scrollRange > 160;
    var progress = hasProgress ? window.scrollY / scrollRange : 0;

    root.classList.toggle('has-site-progress', hasProgress);
    root.style.setProperty('--site-progress', Math.max(0, Math.min(1, progress)));
  }

  function queueProgressUpdate() {
    if (updateQueued) return;
    updateQueued = true;
    window.requestAnimationFrame(updateProgress);
  }

  function initResilientImages() {
    Array.prototype.forEach.call(document.querySelectorAll('img[data-resilient-image]'), function (image) {
      function hideUnavailableImage() {
        image.hidden = true;
        image.removeEventListener('error', hideUnavailableImage);
      }

      image.addEventListener('error', hideUnavailableImage);

      if (image.complete && image.naturalWidth === 0) {
        hideUnavailableImage();
      }
    });
  }

  if (progressBar) {
    updateProgress();
    window.addEventListener('scroll', queueProgressUpdate, { passive: true });
    window.addEventListener('resize', queueProgressUpdate);
  }

  initResilientImages();
}());
