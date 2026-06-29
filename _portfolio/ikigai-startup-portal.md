---
title: "ikigai Startup Portal"
excerpt: "A private founder reporting portal for 886 Studios startups."
summary: "A private founder reporting surface and 886 admin workspace for collecting startup traction updates, reviewing progress, managing access, and keeping KPI definitions consistent."
collection: portfolio
order: 3
year: 2026
status: "active"
repo_visibility: "private"
tech:
  - React
  - TypeScript
  - Supabase
  - Cloudflare Pages
image: "/images/projects/ikigai-startup-portal.png"
image_alt: "Screenshot of the ikigai Startup Portal founder metrics workspace"
---

<figure class="project-detail-image">
  <img src="/images/projects/ikigai-startup-portal.png" alt="Screenshot of the ikigai Startup Portal founder metrics workspace">
</figure>

ikigai Startup Portal is a private internal product for 886 Studios. It gives founders a structured place to submit traction updates while giving the 886 team a focused workspace to review progress, manage access, and keep metrics consistent across startups.

## What it is

A Vite, React, and TypeScript app backed by Supabase Auth, Postgres, Row Level Security, and RPC functions. Founders submit progress reports, admins manage startup membership and metric definitions, and mentors can review submissions with meeting notes.

## Why I made it

The accelerator workflow needed something more structured than scattered notes and spreadsheets, but still smaller than a full CRM. The portal keeps recurring reporting lightweight while making historical updates and KPI trends easier to review.

## What I learned

- How to design an invite-only product where authorization lives in Postgres policies rather than the client.
- How to separate founder, admin, and mentor workflows without turning a small app into a heavy platform.
- How to make startup-specific KPI definitions reusable while preserving flexibility for each company.
