---
title: "CmdZ"
excerpt: "A Chromium extension that brings Safari-style tab restoration to Command+Z without breaking Undo."
summary: "A privacy-focused, dependency-free Chromium extension that restores the most recently closed tab with Command+Z or Ctrl+Z while preserving normal page Undo."
collection: portfolio
order: 5
year: 2026
status: "active"
github: "https://github.com/patrykchojecki/CmdZ"
tech:
  - JavaScript
  - Chrome Extension APIs
  - Manifest V3
  - Node.js tests
image: "/images/projects/cmdz.png"
image_variants: "avif"
image_alt: "CmdZ promotional graphic showing a recently closed browser tab restored with Command+Z"
image_width: 1280
image_height: 800
---

<figure class="project-detail-image">
  <img src="/images/projects/cmdz.png" alt="CmdZ promotional graphic showing a recently closed browser tab restored with Command+Z">
</figure>

CmdZ is a small extension for Chrome and other Chromium-powered desktop browsers that brings Safari's Command+Z tab restoration behavior across platforms without stealing Undo from text fields, editors, or web apps.

[GitHub](https://github.com/patrykchojecki/CmdZ){: .btn}

## What it is

A dependency-free Manifest V3 extension built with plain JavaScript. It gives the current page the first chance to handle Command+Z on macOS or Ctrl+Z on Windows and Linux. If neither the page nor Chrome's native Undo system consumes the shortcut, CmdZ restores the most recently closed individual tab. A dynamically attached listener also covers pages that were already open when the extension was installed or reloaded, while the toolbar icon remains a fallback for browser surfaces where Chrome does not allow page-level listeners.

## Why I made it

Safari makes reopening an accidentally closed tab feel immediate with Command+Z. I wanted the same behavior in Chrome without replacing the Undo shortcut that people expect to keep working inside text fields, editors, and web apps.

## What I learned

- How to distinguish page-level Undo from a browser action using trusted keyboard and `historyUndo` events.
- How to coordinate a content script and service worker safely across installation, upgrades, and extension reloads.
- How to exercise browser-extension behavior with focused Node tests and Chrome end-to-end checks.
- How to design a browser extension with no tracking, network requests, settings, or third-party dependencies.
