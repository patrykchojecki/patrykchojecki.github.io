/* ==========================================================================
   Site scripts
   ========================================================================== */

(function () {
  "use strict";

  var resizeCallbacks = [];
  var resizePending = false;

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  function onResize(callback) {
    resizeCallbacks.push(callback);
  }

  function runResizeCallbacks() {
    if (resizePending) {
      return;
    }

    resizePending = true;
    window.requestAnimationFrame(function () {
      resizePending = false;
      resizeCallbacks.forEach(function (callback) {
        callback();
      });
    });
  }

  function outerHeight(element) {
    var styles = window.getComputedStyle(element);
    return element.offsetHeight + parseFloat(styles.marginTop || 0) + parseFloat(styles.marginBottom || 0);
  }

  function initStickyFooter() {
    var footer = document.querySelector(".page__footer");

    if (!footer) {
      return;
    }

    function bumpIt() {
      document.body.style.marginBottom = outerHeight(footer) + "px";
    }

    bumpIt();
    onResize(bumpIt);
    window.addEventListener("load", bumpIt);
  }

  function initResponsiveVideos() {
    var main = document.getElementById("main");
    var style = document.getElementById("fit-vids-style");

    if (!main) {
      return;
    }

    if (!style) {
      style = document.createElement("style");
      style.id = "fit-vids-style";
      style.textContent = ".fluid-width-video-wrapper{width:100%;position:relative;padding:0;}" +
        ".fluid-width-video-wrapper iframe,.fluid-width-video-wrapper object,.fluid-width-video-wrapper embed{" +
        "position:absolute;top:0;left:0;width:100%;height:100%;}";
      document.head.appendChild(style);
    }

    Array.prototype.forEach.call(main.querySelectorAll([
      'iframe[src*="player.vimeo.com"]',
      'iframe[src*="youtube.com"]',
      'iframe[src*="youtube-nocookie.com"]',
      'iframe[src*="kickstarter.com"][src*="video.html"]',
      "object",
      "embed"
    ].join(",")), function (video, index) {
      var tagName = video.tagName.toLowerCase();
      var parent = video.parentElement;
      var width;
      var height;
      var ratio;
      var wrapper;

      if (
        video.closest(".fitvidsignore") ||
        (parent && parent.classList.contains("fluid-width-video-wrapper")) ||
        (tagName === "embed" && video.closest("object")) ||
        (tagName === "object" && parent && parent.closest("object"))
      ) {
        return;
      }

      width = parseInt(video.getAttribute("width"), 10) || video.getBoundingClientRect().width || 16;
      height = parseInt(video.getAttribute("height"), 10) || video.getBoundingClientRect().height || 9;
      ratio = height / width;

      if (!isFinite(ratio) || ratio <= 0) {
        ratio = 9 / 16;
      }

      if (!video.id) {
        video.id = "fitvid" + index;
      }

      wrapper = document.createElement("div");
      wrapper.className = "fluid-width-video-wrapper";
      wrapper.style.paddingTop = (ratio * 100) + "%";

      parent.insertBefore(wrapper, video);
      wrapper.appendChild(video);
      video.removeAttribute("height");
      video.removeAttribute("width");
    });
  }

  function initAuthorLinks() {
    Array.prototype.forEach.call(document.querySelectorAll(".author__urls-wrapper"), function (wrapper) {
      var button = wrapper.querySelector("button");
      var urls = wrapper.querySelector(".author__urls");

      if (!button || !urls) {
        return;
      }

      function isButtonVisible() {
        var styles = window.getComputedStyle(button);
        return styles.display !== "none" && styles.visibility !== "hidden";
      }

      function setOpen(open) {
        if (!isButtonVisible()) {
          urls.style.display = "block";
          button.classList.remove("open");
          button.setAttribute("aria-expanded", "true");
          return;
        }

        urls.style.display = open ? "block" : "none";
        button.classList.toggle("open", open);
        button.setAttribute("aria-expanded", open ? "true" : "false");
      }

      function syncAuthorLinks() {
        setOpen(button.classList.contains("open"));
      }

      setOpen(false);
      onResize(syncAuthorLinks);

      button.addEventListener("click", function () {
        setOpen(!button.classList.contains("open"));
      });

      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          setOpen(false);
        }
      });
    });
  }

  function initGreedyNav() {
    var nav = document.getElementById("site-nav");
    var button;
    var visibleLinks;
    var hiddenLinks;
    var breaks = [];

    if (!nav) {
      return;
    }

    button = nav.querySelector("button");
    visibleLinks = nav.querySelector(".visible-links");
    hiddenLinks = nav.querySelector(".hidden-links");

    if (!button || !visibleLinks || !hiddenLinks) {
      return;
    }

    function width(element) {
      return element.getBoundingClientRect().width;
    }

    function setMenuExpanded(expanded) {
      button.classList.toggle("close", expanded);
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
    }

    function closeHiddenLinks() {
      hiddenLinks.classList.add("hidden");
      setMenuExpanded(false);
    }

    function updateNav() {
      var availableSpace = button.classList.contains("hidden") ? width(nav) : width(nav) - width(button) - 30;

      if (width(visibleLinks) > availableSpace && visibleLinks.children.length > 0) {
        breaks.push(width(visibleLinks));
        hiddenLinks.insertBefore(visibleLinks.lastElementChild, hiddenLinks.firstElementChild);
        button.classList.remove("hidden");
      } else if (breaks.length && availableSpace > breaks[breaks.length - 1] && hiddenLinks.children.length > 0) {
        visibleLinks.appendChild(hiddenLinks.firstElementChild);
        breaks.pop();
      }

      if (breaks.length < 1) {
        button.classList.add("hidden");
        closeHiddenLinks();
      }

      button.setAttribute("count", breaks.length);

      if (visibleLinks.children.length > 0 && width(visibleLinks) > availableSpace) {
        updateNav();
      }
    }

    function scheduleNavUpdate() {
      window.requestAnimationFrame(updateNav);
    }

    button.addEventListener("click", function () {
      var expanded = hiddenLinks.classList.toggle("hidden") === false;
      setMenuExpanded(expanded);
    });

    document.addEventListener("click", function (event) {
      if (!nav.contains(event.target)) {
        closeHiddenLinks();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeHiddenLinks();
      }
    });

    onResize(scheduleNavUpdate);
    window.addEventListener("load", scheduleNavUpdate);

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(scheduleNavUpdate);
    }

    updateNav();
  }

  function initSmoothScroll() {
    document.addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest("a[href*='#']") : null;
      var url;
      var target;
      var id;
      var top;

      if (!link || event.defaultPrevented || (link.target && link.target !== "_self")) {
        return;
      }

      try {
        url = new URL(link.href, window.location.href);
      } catch (error) {
        return;
      }

      if (
        url.origin !== window.location.origin ||
        url.pathname.replace(/\/$/, "") !== window.location.pathname.replace(/\/$/, "") ||
        url.hash.length < 2
      ) {
        return;
      }

      id = decodeURIComponent(url.hash.slice(1));
      target = document.getElementById(id) || document.getElementsByName(id)[0];

      if (!target) {
        return;
      }

      event.preventDefault();
      top = target.getBoundingClientRect().top + window.pageYOffset - 20;
      window.scrollTo({ top: top, behavior: "smooth" });
      window.history.pushState(null, "", url.hash);
    });
  }

  window.addEventListener("resize", runResizeCallbacks, { passive: true });

  ready(function () {
    initStickyFooter();
    initResponsiveVideos();
    initAuthorLinks();
    initGreedyNav();
    initSmoothScroll();
  });
}());
