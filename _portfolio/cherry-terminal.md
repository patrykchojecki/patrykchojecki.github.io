---
title: "Cherry Terminal"
excerpt: "A local-first portfolio tracker for private multi-currency P/L, quotes, indexes, and allocation."
summary: "A local-first portfolio tracker for private multi-currency P/L, quotes, indexes, allocation, and currency exposure. It runs in the browser with local storage and a small quote proxy."
collection: portfolio
order: 4
year: 2026
status: "active"
repo_visibility: "private"
demo: "https://cherry-terminal.pages.dev"
tech:
  - JavaScript
  - Cloudflare Pages
  - Local storage
  - Yahoo Finance API
image: "/images/projects/cherry-terminal.png"
image_alt: "Screenshot of the Cherry Terminal portfolio tracker"
---

<figure class="project-detail-image">
  <img src="/images/projects/cherry-terminal.png" alt="Screenshot of the Cherry Terminal portfolio tracker">
</figure>

Cherry Terminal is a local-first web app for tracking portfolio positions, live quotes, global indexes, allocation, and currency exposure.

[Live site](https://cherry-terminal.pages.dev){: .btn}

## What it is

A private browser-based portfolio tracker with static HTML pages, native JavaScript modules, local browser storage, and a small Yahoo Finance proxy for quotes and symbol search.

## Why I made it

I wanted a focused way to track positions, currency exposure, indexes, and history without creating an account or putting portfolio data into a server-side database. I originally created this tool for myself. After some consideration and positive feedback, I've decided to make it public and let others benefit from it too.

## What I learned

- How to keep a browser app useful while storing user data locally.
- How to normalize quote data behind a small internal API surface.
- How to test responsive financial UI without adding a heavy frontend framework.
