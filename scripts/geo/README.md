# Search visibility operations

These tools and notes maintain discovery and measurement without editing public page copy. `scripts/` is excluded from Jekyll publishing. Store dashboard exports, observations, and generated reports in `.geo/`, which is ignored by Git and excluded from the site. Do not commit authentication information or private analytics.

## Google indexing

Use the exact domain property `sc-domain:chojecki.net` in [Search Console](https://search.google.com/search-console?resource_id=sc-domain%3Achojecki.net). The canonical page list and sitemap are in `targets.json`.

For each target URL, record the observation date, indexing verdict, last crawl, fetch outcome, indexing permission, user-declared canonical, and Google-selected canonical. Keep indexed-state evidence separate from a live URL test: a successful fetch does not mean Google indexed the page. A missing URL in the index can reflect discovery or selection, not necessarily a technical defect.

Check the Sitemaps report for `https://chojecki.net/sitemap.xml`. The existing sitemap was submitted with the owner's approval on 6 September 2026; Search Console returned **Success**, with 12 URLs discovered. Submission is a discovery signal, not an indexing guarantee. Do not repeatedly resubmit a healthy sitemap.

The blog and publication archives intentionally use `noindex`. Do not remove these exclusions as part of an indexing repair. Prefer investigating a specific target's reported failure over changing site-wide crawler rules.

Reference: [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

## Cloudflare crawler access

In AI Crawl Control → Security, inspect each search crawler in `targets.json`, its block control, and allowed/unsuccessful requests for a stated time window. Record the HTTP status breakdown in Metrics. Verify real crawler identity through Cloudflare's verified-bot classification or the provider's published IP/signature method before considering any firewall exception. A local request with a crawler user-agent only checks response behavior; it does not prove a real crawler can reach the site.

On 6 September 2026, the controls for Googlebot, BingBot, OAI-SearchBot, Claude-SearchBot and PerplexityBot were off (not blocked). The 24-hour report contained successful requests for the first two, but no requests for the three AI search bots. Their actual access remains unobserved in that window. No Cloudflare policy was changed. Preserve unrelated crawler restrictions unless a specific failure justifies changing them.

Keep detailed counts and account-specific evidence in `.geo/`. Check again after a real search-bot visit; distinguish a 404 from a firewall rejection and inspect the requested path before changing access rules.

Reference: [Cloudflare verified bots](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/).

## Structured data

`python3 scripts/check-site.py _site` validates JSON syntax, the site's schema relationships, canonical URLs, identity links, indexability of sitemap pages, and consistent revision dates. It is a regression check for this site's templates, not a complete Schema.org validator. Run its negative regression cases with `python3 -m unittest discover -s scripts -p 'test_*.py'`.

The live homepage passed Google's Rich Results Test on 6 September 2026 with one valid ProfilePage item. Schema.org's URL fetch failed; its code-input fallback accepted the five published JSON-LD blocks with no errors or warnings. A code-input result does not establish crawler access. Keep result links and detailed observations in `.geo/`.

Use [Rich Results Test](https://search.google.com/test/rich-results) for Google-supported features and [Schema.org Validator](https://validator.schema.org/) for general vocabulary validation. Project CreativeWork markup need not produce a Google rich result. Do not add unsupported types or visible claims merely to obtain a validator badge.

## Deployment checks

`npm run test:seo` tests the checkers with malformed metadata, blocked robots, redirects, HTTP failures, stale deployments, and date mismatches. `npm run check:live -- --expected-dir _site --report .geo/live-site.json` checks the published sitemap's URLs plus robots.txt and sitemap.xml against a production build. Omit `--expected-dir` for a standalone health check, or use `--base-url http://127.0.0.1:8000` to test a locally served production build while keeping public canonical expectations.

The Pages workflow records the build's sitemap, metadata fingerprints and static-asset hashes, then checks the public domain after a successful deployment. It retries three times, 20 seconds apart, to allow cache propagation, and fails the verification job with specific URLs if a problem remains. No API keys are required. This detects a problem after deployment; it does not roll back the site. The new job takes effect only once this workflow is pushed.

PDF sitemap timestamps derive from checkout modification time, so the checker verifies the PDF bytes instead of comparing those dates across builds. HTML revision dates must still agree with their JSON-LD and the build manifest. Passing these checks establishes HTTP and metadata health, not indexing or AI citation.

## Fortnightly citation and referral baseline

Create a private observation file with `python3 scripts/geo/baseline.py init .geo/baseline-YYYY-MM-DD.json --date YYYY-MM-DD`. It includes five fixed queries for each of ChatGPT, Claude, Perplexity, Gemini, and Google AI Overviews, and a referral-report section. It never overwrites an existing baseline. The next review is 14 days later; this records a due date, not an automatic scheduled task.

Run each prompt from `queries.json` in a fresh conversation, with web search enabled where available. Record language, country, product/model, account state, and personalization settings; use unpersonalized/temporary sessions when supported. Preserve the exact prompt and version for comparison. These are branded identity and project diagnostics, not unbranded discovery or market-share measurements.

For each answer, record `observed`, the independent name-mention verdict, actual citation destination URLs, factual accuracy notes, and evidence (a result link or a dated local observation). A mention without a link is not a citation. Count a chojecki.net citation only when the link destination is that exact host. Mark unavailable products explicitly; keep unrun tests `pending`. For Google, record `no_ai_overview` when the result page has no AI overview—ordinary search links are not AI citations. Never score an unavailable answer as a zero.

Run `python3 scripts/geo/baseline.py summary .geo/baseline-YYYY-MM-DD.json` to validate completeness and calculate each engine's citation rate using observed answers only. Compare both the rate and the completed-query denominator. Review accuracy manually against the current public pages; do not turn uncertain claims into page copy without approval.

In Cloudflare Web Analytics → Visits → Referers, use the same two-week date range and timezone each time. Record counts for actual referring hosts such as chatgpt.com, claude.ai, perplexity.ai and gemini.google.com, using exact hosts or their subdomains, not substring matching. Keep Google referrals separate: the referrer alone does not distinguish AI Overviews from ordinary Google Search. Preserve the source window, raw referrers, and dashboard sampling/coverage caveats in the private baseline. Missing referrers can appear as direct traffic; zero attributed AI referrals is not proof of zero AI visits. Keep crawler requests separate from visitor referrals.
