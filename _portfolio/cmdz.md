---
title: "CmdZ"
excerpt: "A Chrome extension that brings Safari-style tab restoration to Command+Z without breaking Undo."
summary: "A privacy-focused Chrome extension that restores the most recently closed tab with Command+Z or Ctrl+Z while preserving a website's normal Undo behavior."
collection: portfolio
order: 5
year: 2026
status: "active"
github: "https://github.com/patrykchojecki/CmdZ"
tech:
  - JavaScript
  - Chrome Extension APIs
  - Manifest V3
image: "/images/projects/cmdz.png"
image_alt: "CmdZ promotional graphic showing a recently closed browser tab restored with Command+Z"
image_width: 1280
image_height: 800
---

<figure class="project-detail-image">
  <img src="/images/projects/cmdz.png" alt="CmdZ promotional graphic showing a recently closed browser tab restored with Command+Z">
</figure>

CmdZ is a small Chrome extension that brings Safari's Command+Z tab restoration behavior to Chrome without stealing Undo from text fields or web apps.

[GitHub](https://github.com/patrykchojecki/CmdZ){: .btn}

## What it is

A dependency-free Manifest V3 extension built with plain JavaScript. It gives the current page the first chance to handle Command+Z on macOS or Ctrl+Z on Windows and Linux. If the page has nothing to undo, CmdZ restores the most recently closed individual tab. The toolbar icon provides a fallback in browser surfaces where Chrome does not allow page-level shortcut listeners.

## Why I made it

Safari makes reopening an accidentally closed tab feel immediate with Command+Z. I wanted the same behavior in Chrome without replacing the Undo shortcut that people expect to keep working inside text fields, editors, and web apps.

## What I learned

- How to distinguish page-level Undo from a browser action using trusted keyboard and `historyUndo` events.
- How to coordinate a content script and service worker while keeping extension permissions focused.
- How to design a browser extension with no tracking, network requests, settings, or third-party dependencies.
