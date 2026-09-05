/* ==========================================================================
   Site scripts
   ========================================================================== */

(function () {
  "use strict";

  var resizeCallbacks = [];
  var resizePending = false;
  var requestFrame = window.requestAnimationFrame || function (callback) {
    return window.setTimeout(callback, 16);
  };

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
    requestFrame(function () {
      resizePending = false;
      resizeCallbacks.forEach(function (callback) {
        callback();
      });
    });
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

      if (!parent) {
        return;
      }

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

      function closeAuthorLinks(returnFocus) {
        var wasOpen = button.classList.contains("open");
        setOpen(false);

        if (returnFocus && wasOpen && isButtonVisible()) {
          button.focus();
        }
      }

      setOpen(false);
      onResize(syncAuthorLinks);

      wrapper.addEventListener("focusout", function (event) {
        if (!wrapper.contains(event.relatedTarget)) {
          closeAuthorLinks(false);
        }
      });

      button.addEventListener("click", function () {
        setOpen(!button.classList.contains("open"));
      });

      document.addEventListener("click", function (event) {
        if (!wrapper.contains(event.target)) {
          closeAuthorLinks(false);
        }
      });

      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && button.classList.contains("open")) {
          closeAuthorLinks(true);
        }
      });
    });
  }

  function initGreedyNav() {
    var nav = document.getElementById("site-nav");
    var button;
    var visibleLinks;
    var hiddenLinks;

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

    function closeHiddenLinks(returnFocus) {
      var wasExpanded = hiddenLinks.classList.contains("hidden") === false;
      hiddenLinks.classList.add("hidden");
      setMenuExpanded(false);

      if (returnFocus && wasExpanded && !button.classList.contains("hidden")) {
        button.focus();
      }
    }

    function updateNav() {
      var focused = document.activeElement;
      var availableSpace;

      nav.classList.remove("greedy-nav--stacked");
      // Recalculate from the complete list so one resize restores every link
      // that fits, even after a large viewport or text-size change.
      while (hiddenLinks.firstElementChild) {
        visibleLinks.appendChild(hiddenLinks.firstElementChild);
      }
      button.classList.add("hidden");
      availableSpace = width(nav);

      if (width(visibleLinks) > availableSpace) {
        button.classList.remove("hidden");
        availableSpace -= width(button) + 30;

        // Keep the site name visible as a reliable route back home.
        while (visibleLinks.children.length > 1 && width(visibleLinks) > availableSpace) {
          hiddenLinks.insertBefore(visibleLinks.lastElementChild, hiddenLinks.firstElementChild);
        }
      }

      if (!hiddenLinks.children.length) {
        button.classList.add("hidden");
        closeHiddenLinks(false);
      }

      button.setAttribute("count", hiddenLinks.children.length);
      nav.classList.toggle("greedy-nav--stacked",
        hiddenLinks.children.length > 0 && width(visibleLinks) > availableSpace);

      if (focused && nav.contains(focused)) {
        if (focused === button && button.classList.contains("hidden")) {
          visibleLinks.querySelector("a").focus();
        } else if (hiddenLinks.contains(focused) && hiddenLinks.classList.contains("hidden")) {
          button.focus();
        } else if (document.activeElement !== focused) {
          focused.focus();
        }
      }
    }

    function scheduleNavUpdate() {
      requestFrame(updateNav);
    }

    button.addEventListener("click", function () {
      var expanded = hiddenLinks.classList.toggle("hidden") === false;
      setMenuExpanded(expanded);
    });

    document.addEventListener("click", function (event) {
      if (!nav.contains(event.target)) {
        closeHiddenLinks(false);
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeHiddenLinks(true);
      }
    });

    nav.addEventListener("focusout", function (event) {
      if (!nav.contains(event.relatedTarget)) {
        closeHiddenLinks(false);
      }
    });

    onResize(scheduleNavUpdate);
    window.addEventListener("load", scheduleNavUpdate);

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(scheduleNavUpdate).catch(function () {});
    }

    updateNav();
  }

  window.addEventListener("resize", runResizeCallbacks, { passive: true });

  ready(function () {
    // Keep the accessible static layout until the interactive bundle has loaded.
    document.documentElement.classList.remove("no-js");
    document.documentElement.classList.add("js");
    initResponsiveVideos();
    initAuthorLinks();
    initGreedyNav();
  });
}());
