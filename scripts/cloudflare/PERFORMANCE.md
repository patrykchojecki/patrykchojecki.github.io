# Cloudflare delivery review

Reviewed on 2026-10-24 (Asia/Taipei), starting at commit `b3e7a3d`.
The site remains on free static Pages hosting.

## Baseline

Cloudflare dashboard inspection confirmed HTTP/2, HTTP/3, HTTP/2 to Origin,
TLS 1.3, Always Use HTTPS, Early Hints, and existing real-user analytics are on.
Rocket Loader is also on (a legacy setting last changed three years ago).
Speed Brain and Cloudflare Fonts are off. Paid image optimization is unavailable
on the current plan. Fonts are already self-hosted.

Three sequential public GETs per resource, using fresh curl connections with
compression negotiation, produced these median time-to-first-byte samples:

| Resource | Median TTFB | Transferred bytes in final sample |
| --- | ---: | ---: |
| `/` | 574.6 ms | 5,090 |
| `/cv/` | 606.7 ms | 5,477 |
| `/projects/` | 829.8 ms | 5,179 |
| `/now/` | 330.1 ms | 5,206 |
| `/assets/css/main.css` | 323.4 ms | 42,463 |
| `/assets/js/main.min.js` | 459.5 ms | 1,531 |
| `/assets/js/theme-toggle.js` | 537.9 ms | 1,591 |
| `/assets/js/site-delight.js` | 281.9 ms | 571 |
| `/images/bio-photo-600.jpg` | 300.2 ms | 87,655 |
| `/assets/webfonts/fa-solid-900.woff2` | 516.2 ms | 158,220 |

These are network samples, not browser LCP measurements or an SLA. Connections
can reach different Cloudflare locations, so cache correctness and eliminated
requests are more reliable evidence than small timing differences.

- HTML uses `public, max-age=0, must-revalidate` and has no preload Link header.
- The sampled assets use `public, max-age=14400, must-revalidate`.
- Gzip is delivered; a separate `Accept-Encoding: br` request confirms Brotli.
- The HTML includes Cloudflare's extra Rocket Loader script and rewritten script
  types, although the site's three external scripts already use native `defer`.
- CSS and JavaScript query versions derive from build time, so the six-hour
  activity refresh changes their URLs even when their bytes are identical.

## Implementation and verification sequence

1. Disable the redundant Rocket Loader transformation; retain native script
   order and the inline theme bootstrap. Verify live pages and theme behavior.
2. Give the generated CSS, JavaScript, and referenced fonts content-hashed
   filenames and long browser caching. Keep original URLs available and keep
   HTML and discovery resources fresh. Add an exact stylesheet preload hint.
3. Validate a preview deployment before publishing the same build to production;
   extend regression and live checks for fingerprints, headers, and hints.
4. Record the resulting headers, eliminated requests, browser checks, and CI run.

Avoid blanket HTML caching or Cache Everything rules, which could serve stale
pages or bypass redirects. Pages already provides CDN caching and Tiered Cache.
Keep Speed Brain off: its documented Pages incompatibility makes it unsuitable
here. Do not enable paid products or change DNS, mail, security, or analytics.

## Rollback

Revert the relevant source commit and let the normal workflow publish it. Original
asset URLs stay available during this change. Rocket Loader can be restored at
Speed → Settings → Content Optimization if needed; its original value is On.
Use the existing [hosting rollback procedure](README.md#rollback-procedure) for
a wider hosting incident.

## References

- [Pages caching defaults and immutable assets](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- [Pages custom headers](https://developers.cloudflare.com/pages/configuration/headers/)
- [Pages Early Hints](https://developers.cloudflare.com/pages/configuration/early-hints/)
- [Speed Brain requirements and caveats](https://developers.cloudflare.com/speed/optimization/content/speed-brain/)
