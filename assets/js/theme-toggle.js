(function () {
  'use strict';

  var STORAGE_KEY = 'theme';
  var DARK        = 'dark';
  var LIGHT       = 'light';
  var mql         = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  var activeTransition = null;

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || LIGHT;
  }

  function storedTheme() {
    try {
      var theme = localStorage.getItem(STORAGE_KEY);
      return theme === DARK || theme === LIGHT ? theme : null;
    } catch (e) {
      return null;
    }
  }

  function setTheme(theme, persist) {
    document.documentElement.setAttribute('data-theme', theme);
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) {}
    }
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
    btn.setAttribute('aria-pressed', theme === DARK ? 'true' : 'false');
  }

  // Update the browser chrome / PWA theme colour meta tag
  function updateThemeColor(theme) {
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    Array.prototype.forEach.call(metas, function (meta) {
      meta.setAttribute('content', theme === DARK ? '#141414' : '#de7536');
    });
  }

  // Enable smooth cross-fade only after first paint so the FOUC script's
  // initial theme application is instant
  function enableTransitions() {
    document.documentElement.classList.add('theme-transitions');
  }

  function reducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function toggleTheme(event, button) {
    var nextTheme = currentTheme() === DARK ? LIGHT : DARK;

    if (!document.startViewTransition || reducedMotion()) {
      setTheme(nextTheme, true);
      return;
    }

    if (activeTransition && activeTransition.skipTransition) {
      activeTransition.skipTransition();
    }

    var rect = button.getBoundingClientRect();
    var x = event.clientX || rect.left + rect.width / 2;
    var y = event.clientY || rect.top + rect.height / 2;
    var endRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    );

    document.documentElement.classList.add('theme-transitioning');
    document.documentElement.style.setProperty('--theme-reveal-x', x + 'px');
    document.documentElement.style.setProperty('--theme-reveal-y', y + 'px');

    var transition;

    try {
      transition = document.startViewTransition(function () {
        setTheme(nextTheme, true);
      });
    } catch (error) {
      document.documentElement.classList.remove('theme-transitioning');
      setTheme(nextTheme, true);
      return;
    }
    activeTransition = transition;

    transition.ready.then(function () {
      document.documentElement.animate({
        clipPath: [
          'circle(0px at ' + x + 'px ' + y + 'px)',
          'circle(' + endRadius + 'px at ' + x + 'px ' + y + 'px)'
        ]
      }, {
        duration: 460,
        easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
        fill: 'both',
        pseudoElement: '::view-transition-new(root)'
      });
    }).catch(function () {});

    transition.finished.then(function () {
      if (activeTransition !== transition) return;
      document.documentElement.classList.remove('theme-transitioning');
      activeTransition = null;
    }).catch(function () {
      if (activeTransition !== transition) return;
      document.documentElement.classList.remove('theme-transitioning');
      activeTransition = null;
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Sync button state with whatever theme was applied by the FOUC script
    updateButton(currentTheme());

    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', function (event) {
        toggleTheme(event, btn);
      });
    }

    // Small delay so the transition class is added after first paint
    setTimeout(enableTransitions, 100);
  });

  // Follow system preference changes when the user has no stored override
  function handleSystemThemeChange(e) {
    if (!storedTheme()) {
      setTheme(e.matches ? DARK : LIGHT, false);
    }
  }

  if (mql) {
    if (mql.addEventListener) {
      mql.addEventListener('change', handleSystemThemeChange);
    } else if (mql.addListener) {
      mql.addListener(handleSystemThemeChange);
    }
  }
}());
