---
title: "886 Studios Website"
excerpt: "The production website and publishing platform for 886 Studios."
summary: "The production website for 886 Studios: accelerator programs, portfolio, events, founder resources, and a two-source blog in a maintainable Astro codebase."
collection: portfolio
order: 2
year: 2026
status: "active"
github: "https://github.com/886-Studios/886studios-redesign"
demo: "https://www.886studios.com"
tech:
  - Astro 7
  - TypeScript
  - Vercel
  - Node.js
image: "/images/projects/886studios-redesign.png"
image_variants: "avif"
image_alt: "Screenshot of the current 886 Studios homepage"
---

<figure class="project-detail-image">
  <img src="/images/projects/886studios-redesign.png" alt="Screenshot of the current 886 Studios homepage">
</figure>

The 886 Studios website has grown from a visual redesign into the production publishing platform for our accelerator and venture work. It now brings together program information, the startup portfolio, events, founder resources, team profiles, and original writing in one coherent site.

[GitHub](https://github.com/886-Studios/886studios-redesign){: .btn}
[Live site](https://www.886studios.com){: .btn}

## What it is

An Astro 7 static site with thin route files, reusable page components, shared layouts, and centralized typed content. The blog merges ikigai Insights posts from Substack with local Markdown articles, while a scheduled GitHub Actions workflow keeps the public Luma event archive current. The build also runs regression checks for metadata, structured data, internal links, images, robots directives, and sitemap parity before deployment to Vercel.

## Why I made it

Together with my colleague, I wanted a credible home for 886 Studios that we could keep improving without treating every page as a one-off. The previous website was essentially a [Notion](https://www.notion.com/) page, which made both the brand and the content difficult to develop. The rebuild gave us a stronger identity and an operating system for publishing new programs, events, portfolio companies, and resources.

## What I learned

- How to structure a growing Astro site around reusable page-level components and typed content.
- How to automate event and blog publishing while keeping the production output static and fast.
- How to pair a new visual identity with durable SEO, analytics, accessibility, and content-maintenance checks.
