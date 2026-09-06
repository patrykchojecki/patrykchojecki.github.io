# Search visibility operations

These tools and notes maintain discovery and measurement without editing public page copy. `scripts/` is excluded from Jekyll publishing. Store dashboard exports, observations, and generated reports in `.geo/`, which is ignored by Git and excluded from the site. Do not commit authentication information or private analytics.

## Google indexing

Use the exact domain property `sc-domain:chojecki.net` in [Search Console](https://search.google.com/search-console?resource_id=sc-domain%3Achojecki.net). The canonical page list and sitemap are in `targets.json`.

For each target URL, record the observation date, indexing verdict, last crawl, fetch outcome, indexing permission, user-declared canonical, and Google-selected canonical. Keep indexed-state evidence separate from a live URL test: a successful fetch does not mean Google indexed the page. A missing URL in the index can reflect discovery or selection, not necessarily a technical defect.

Check the Sitemaps report for `https://chojecki.net/sitemap.xml`. The existing sitemap was submitted with the owner's approval on 6 September 2026; Search Console returned **Success**, with 12 URLs discovered. Submission is a discovery signal, not an indexing guarantee. Do not repeatedly resubmit a healthy sitemap.

The blog and publication archives intentionally use `noindex`. Do not remove these exclusions as part of an indexing repair. Prefer investigating a specific target's reported failure over changing site-wide crawler rules.

Reference: [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
