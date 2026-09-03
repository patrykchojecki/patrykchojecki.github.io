---
title: "Cherry Terminal"
excerpt: "A local-first stock tracker for holdings, allocation, research watchlists, and multi-currency exposure."
summary: "A local-first stock tracker for holdings, cash, allocation, research watchlists, and direct or ETF look-through exposure—with portfolio data kept in IndexedDB."
collection: portfolio
order: 4
year: 2026
status: "active"
repo_visibility: "private"
demo: "https://cherry-terminal.pages.dev"
tech:
  - React 19
  - TypeScript
  - IndexedDB
  - Cloudflare Pages
image: "/images/projects/cherry-terminal.png"
image_variants: "avif"
image_alt: "Screenshot of the Cherry Terminal portfolio overview"
---

<figure class="project-detail-image">
  <img src="/images/projects/cherry-terminal.png" alt="Screenshot of the Cherry Terminal portfolio overview">
</figure>

Cherry Terminal has grown into a local-first stock tracker for understanding what I own now. It brings holdings, cash, gains, allocation, currency exposure, research watchlists, and direct or ETF look-through exposure into one focused workspace without requiring an account.

[Live site](https://cherry-terminal.pages.dev){: .btn}

## What it is

A React 19 and TypeScript app built with Vite and React Router. Dexie stores portfolio data in IndexedDB; TanStack Query manages market requests; Zustand handles transient interface state; and Zod and Decimal.js keep imported data and money calculations predictable. The app uses same-origin Cloudflare Functions for public market data, but quantities, costs, cash, accounts, and notes stay on the device.

The main surfaces cover the portfolio overview, current holdings and concentration, underlying company exposure through ETFs, multiple research watchlists, backups and exports, appearance controls, and diagnostics. It supports global symbols and currencies through a deliberately layered set of public market-data sources.

## Why I made it

I wanted a calmer way to review positions, concentration, ETF overlap, currency exposure, and ideas without creating another financial account or placing sensitive portfolio data in a server-side database. I originally built the tool for myself, then expanded it into a public app that other investors can use with the same local-first privacy model.

## What I learned

- How to migrate a browser product from localStorage to a versioned IndexedDB domain model without losing existing data.
- How to combine incomplete market, FX, regulatory, and ETF-holdings sources while keeping provenance and limitations visible.
- How to keep a data-heavy React interface fast, accessible, responsive, and testable across routes, text sizes, and local states.
