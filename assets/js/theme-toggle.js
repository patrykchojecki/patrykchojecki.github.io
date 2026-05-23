(function () {
  'use strict';

  var STORAGE_KEY = 'theme';
  var DARK        = 'dark';
  var LIGHT       = 'light';

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || LIGHT;
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
    updateButton(theme);
    updateThemeColor(theme);
  }

  function updateButton(theme) {
    var btn  = document.getElementById('theme-toggle');
    if (!btn) return;

    var icon = btn.querySelector('i');
    if (icon) {
      icon.className = theme === DARK
        ? 'fas fa-fw fa-sun'
        : 'fas fa-fw fa-moon';
    }
    btn.setAttribute('aria-label',
      theme === DARK ? 'Switch to light mode' : 'Switch to dark mode');
  }

  // Update the browser chrome / PWA theme colour meta tag
  function updateThemeColor(theme) {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute('content', theme === DARK ? '#141414' : '#de7536');
    }
  }

  // Enable smooth cross-fade only after first paint so the FOUC script's
  // initial theme application is instant
  function enableTransitions() {
    document.documentElement.classList.add('theme-transitions');
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Sync button state with whatever theme was applied by the FOUC script
    updateButton(currentTheme());

    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', function () {
        applyTheme(currentTheme() === DARK ? LIGHT : DARK);
      });
    }

    // Small delay so the transition class is added after first paint
    setTimeout(enableTransitions, 100);
  });

  // Follow system preference changes when the user has no stored override
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      try {
        if (!localStorage.getItem(STORAGE_KEY)) {
          applyTheme(e.matches ? DARK : LIGHT);
        }
      } catch (err) {}
    });
  }
}());
