# Cloudflare Pages migration

Migration started on 2026-10-24 (Asia/Taipei). The canonical address remains
`https://chojecki.net`. GitHub remains the source repository and build runner;
Cloudflare Pages serves the generated static files on its Free plan.

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

## Deployment configuration

- Pages project: `chojecki-net` (Direct Upload, production branch `master`).
- Preview origin: `https://chojecki-net.pages.dev`.
- Workflow: `.github/workflows/cloudflare.yml` (pushes to `master`, the existing
  six-hour schedule, and manual runs). GitHub Pages is manual rollback only.
- Repository variable `CLOUDFLARE_ACCOUNT_ID`: the Cloudflare account ID.
- Repository secret `CLOUDFLARE_API_TOKEN`: a token limited to **Account →
  Cloudflare Pages → Edit** for the owner's account. It needs no DNS access.
- Repository variable `CLOUDFLARE_CUSTOM_DOMAIN_ACTIVE`: `true`, enabling
  additional production-domain checks after every deployment.
- `OPENXBL_API_KEY` remains in GitHub; the build fetches activity before upload.
- Wrangler is pinned to `4.152.0`; no Pages Functions or Workers are deployed.

For a manual local upload, first build and validate the site, then run:

```sh
npm run check
python3 scripts/prepare-cloudflare.py
npx --yes wrangler@4.152.0 pages deploy _site --project-name chojecki-net --branch master
python3 scripts/check-live-site.py --base-url https://chojecki-net.pages.dev --expected-dir _site
python3 scripts/check-hosting.py --base-url https://chojecki-net.pages.dev --site-dir _site
```

The preparation step enforces the Free plan's file count/size limits, requires a
real 404 page, rejects runtime functions, and generates HTTP redirects from
Jekyll's existing aliases. The canonical URLs remain on `https://chojecki.net`.
The HTML alias files remain usable on GitHub Pages for rollback.

## Production DNS and hostname redirect

Both `chojecki.net` and `www.chojecki.net` are associated with the Pages project.
Their CNAME targets are `chojecki-net.pages.dev`, Proxied, TTL Auto.

The zone Single Redirect **chojecki.net canonical www redirect** is enabled:

- Match: `(http.host eq "www.chojecki.net")`.
- Dynamic target: `concat("https://chojecki.net", http.request.uri.path)`.
- Status: `301`; preserve query string: enabled.

This rule covers both HTTP and HTTPS. Domain-level redirects are not supported
in Pages' `_redirects` file, so that generated file contains path aliases only.
The existing HTTP-to-HTTPS behavior on the apex remains enabled.

## Validation log

- `b327798`: repaired GitHub build, deployment, and live verification succeeded
  in Actions run `40075278718`.
- The successful GitHub artifact contains 61 files, 6,755,643 bytes total;
  the largest file is 2,990,752 bytes (well below Pages' 25 MiB limit).
- Uploaded the same artifact to Pages, then added generated HTTP redirects.
- Pages deployment `a8aaabbc.chojecki-net.pages.dev` passed 55 page/asset checks,
  eight legacy redirect checks, one real-404 check, and 14 discovery resources.
- The four migration regression tests and all 46 pre-existing tests pass.
- Automated Cloudflare publishing passed in Actions run `40075989328`, using
  the scoped deployment token stored in GitHub Actions; Xbox activity refreshed
  successfully in that run.
- Switched the apex CNAME on 2026-10-24 around 08:02 UTC. The first request
  returned HTTP 522 during activation; HTTPS was serving normally within about
  25 seconds and all 14 live discovery checks passed.
- Production validation passed in Actions run `40076530498`: the exact build
  passed the preview and custom-domain gates, including the `www` and HTTPS
  redirects. OpenXBL returned no profile in this run, invoking the existing
  optional-card fallback also observed on GitHub before migration.
- The push-triggered production run `40076623700` passed all 50 regression tests,
  generated-site validation, 55 page/asset checks, 12 production redirect/404
  checks, and 14 discovery-resource checks. Xbox activity refreshed successfully.
- Both custom domains report **Active**, with SSL enabled. The previously broken
  `www` hostname now returns the intended permanent redirect.
- Browser checks on the production domain passed: homepage rendering, dark/light
  theme switching and persistence, CV/Now navigation, and the live Xbox card.
- Public DNS checks confirm the eight mail/verification records and both
  nameservers match the pre-migration values. GitHub Pages retains its previous
  successful deployment and custom-domain association for rollback.
- Updated README, product constraints, project metadata, privacy hosting text,
  package metadata, and `llms.txt` to reflect the completed migration.

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

The dashboard showed these website records before cutover:

| Type | Name | Original target | Proxy | TTL |
| --- | --- | --- | --- | --- |
| CNAME | `chojecki.net` | `patrykchojecki.github.io` | Proxied | Auto |
| CNAME | `www.chojecki.net` | `chojecki.net` | Proxied | Auto |

The zone has ten records total. The other eight records serve iCloud Mail
(MX, SPF, DKIM, DMARC), Apple/Google verification, and the Bluesky handle. Preserve
them unchanged. The pre-existing `www` hostname returned HTTP 526; attaching it
to Pages and redirecting it to the apex is included in the migration.

Keep the last working GitHub Pages deployment and its custom-domain association
intact. If production verification fails, restore the website DNS records above
and verify `https://chojecki.net` again.
Do not change unrelated zone records to recover website hosting.
The zone `www` redirect can remain enabled during a GitHub rollback. To publish
a newer GitHub rollback build, run `.github/workflows/static.yml` manually after
restoring the apex DNS target; its final check expects the canonical domain to
serve that GitHub build. Pause the Cloudflare workflow if continuing on GitHub.

For later Cloudflare deployments, use Pages' rollback to the preceding verified
production deployment. A source rollback should use a normal revert commit.

## References

- [Direct Upload with CI](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)
- [Custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)
- [Serving pages and 404 behavior](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Free plan limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Single Redirect settings](https://developers.cloudflare.com/rules/url-forwarding/single-redirects/settings/)
