# Cloudflare Pages migration

Migration started on 2026-10-24 (Asia/Taipei). The canonical address remains
`https://chojecki.net`. GitHub remains the source repository and build runner;
Cloudflare Pages will serve the generated static files on its Free plan.

## Execution schedule and gates

Run these phases in order during the migration session. Times are estimates,
not deadlines; a failed gate postpones the DNS switch.

1. **Access and baseline (10–15 minutes):** verify GitHub repository admin access,
   Cloudflare account/zone access, current DNS, and live-site checks. Capture the
   old DNS values before editing them.
2. **Build and preview (20–40 minutes):** repair the existing CI prerequisite,
   preserve the OpenXBL secret and six-hour refresh, build the same Jekyll output,
   deploy to Pages, and check routes, assets, redirects, 404s, metadata, and PDFs.
3. **Domain switch (10–20 minutes after preview passes):** attach custom domains,
   change only the website records, and verify HTTPS and canonical redirects.
   Leave email, domain verification, registrar, nameservers, and DNSSEC unchanged.
4. **Production verification and handoff (10–20 minutes):** verify the exact build
   at the custom domain, check browser behavior, document results, and commit the
   final hosting documentation. Keep GitHub Pages available for rollback.

Each significant code/configuration phase receives a separate reviewed commit.
Do not switch DNS until the Cloudflare deployment passes the preview gate.

## Starting state

- Repository: `patrykchojecki/patrykchojecki.github.io`, production branch `master`.
- Starting commit: `6f96ae5161c24706a26a22b917542d8325111cbe`.
- GitHub CLI is authenticated as `patrykchojecki` with repository admin access.
- The separate ChatGPT GitHub connector has no write permission to this repo;
  use the authenticated local GitHub CLI for repository administration.
- Cloudflare manages the domain registration and authoritative DNS.
- Nameservers: `celeste.ns.cloudflare.com`, `keenan.ns.cloudflare.com`.
- GitHub Pages uses GitHub Actions and the custom domain `chojecki.net`.
- Live checks passed for 14 resources before migration.
- Recent CI runs fail because Ruby 3.4.4 is unavailable on the new
  `ubuntu-latest` (26.04) runner. Repair the runner/build prerequisite first.
- `OPENXBL_API_KEY` is already a GitHub Actions secret. It must stay there.
- Existing local dependency, watcher, and documentation changes predate this
  migration and must be preserved separately.

## Rollback procedure

Before switching DNS, record the exact old website record types, values, proxy
settings, and TTLs in this runbook. Keep the last working GitHub Pages deployment
and its custom-domain association intact. If production verification fails,
restore those website DNS records and verify `https://chojecki.net` again.
Do not change unrelated zone records to recover website hosting.

For later Cloudflare deployments, use Pages' rollback to the preceding verified
production deployment. A source rollback should use a normal revert commit.

## References

- [Direct Upload with CI](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)
- [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)
- [Serving pages and 404 behavior](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Free plan limits](https://developers.cloudflare.com/pages/platform/limits/)
