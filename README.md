# chojecki.net

Source for [chojecki.net](https://chojecki.net), Patryk Chojecki’s personal website. The site is built with Jekyll and deployed to Cloudflare Pages on its Free plan from the `master` branch. GitHub hosts the repository and runs the builds.

The project began as a fork of [Academic Pages](https://github.com/academicpages/academicpages.github.io), which is based on the [Minimal Mistakes Jekyll theme](https://mmistakes.github.io/minimal-mistakes/).

## Prerequisites

Install the versions pinned by the repository:

- Ruby 3.4.11
- Bundler 4.0.9
- Node.js 26
- npm 10 or newer
- Python 3.9 or newer (for generated-site checks; no Python packages required)

Using a Ruby and Node version manager is recommended. Confirm the active toolchain before installing dependencies:

```sh
ruby --version
bundle --version
node --version
npm --version
```

## Setup

```sh
git clone https://github.com/patrykchojecki/chojecki.net.git
cd chojecki.net
gem install bundler -v 4.0.9
bundle install
npm ci
```

No environment variables are required for normal local development.

## Local development

Start Jekyll with development overrides:

```sh
npm run serve
```

Open [http://127.0.0.1:4001](http://127.0.0.1:4001). Development mode disables analytics, generates expanded CSS with source maps, and uses `_data/xbox_preview.yml` when live Xbox data is unavailable.

Restart the server after changing `_config.yml` or `_config.dev.yml`; Jekyll does not reload configuration changes automatically.

Run `npm run watch:js` in another terminal to rebuild `assets/js/main.min.js` when
its source, `assets/js/_main.js`, changes. The watcher uses Node's built-in file
watching and handles file replacement on save. Other JavaScript files are served
directly and do not need minification.

## Build and test

Run the same JavaScript and production Jekyll build used for a local check:

```sh
npm run check
```

Test the OpenXBL data normalization separately:

```sh
npm test
```

The generated site is written to `_site/`. The build checks its internal links, assets, fragment targets, page landmarks, sitemap destinations, and publication exclusions. Run `npm run check:site` to repeat these checks against an existing build.

## Xbox activity

The `/now` page displays Xbox activity from `_data/xbox.json`. GitHub Actions generates this ignored file with `scripts/fetch-openxbl.mjs`; local development falls back to the tracked preview data.

Live Xbox activity requires an `OPENXBL_API_KEY` repository secret linked to an OpenXBL account whose Xbox profile and title history are visible. The key is not required to serve or build the site locally with preview data. If a production refresh fails or the secret is missing, the site still deploys with the activity card omitted. Unavailable achievement data does not hide a successfully fetched profile and game.

Authenticated API requests reject redirects, and errors omit response bodies and parser details to keep private data out of build logs. If OpenXBL changes its API address, verify the new official endpoint and update `API_ROOT` in `scripts/openxbl-client.mjs`. Keep the key in GitHub Actions secrets; if it is ever exposed, revoke it at the provider and replace the repository secret.

## Deployment

Pushing to `master` triggers `.github/workflows/cloudflare.yml`, which:

1. Installs the pinned Node and Ruby dependencies and runs the regression tests.
2. Builds JavaScript and fetches the latest Xbox activity.
3. Builds Jekyll, checks the generated site, and prepares redirects, content-hashed assets, caching headers, and stylesheet preload hints.
4. Uploads and verifies a Cloudflare Pages preview, then publishes the same build to production only after it passes.
5. Verifies pages, asset bytes, PDFs, metadata, redirects, and 404 behavior on both the Pages origin and `https://chojecki.net`.

The workflow also refreshes the deployment every six hours (`17 */6 * * *`, UTC)
and can be run manually from GitHub Actions. It reads Ruby from `.ruby-version`.
No Workers or Pages Functions are required.

Configure the repository variable `CLOUDFLARE_ACCOUNT_ID`, the encrypted Actions
secret `CLOUDFLARE_API_TOKEN` (Account → Cloudflare Pages → Edit for the owner's
account), and `CLOUDFLARE_CUSTOM_DOMAIN_ACTIVE=true`. The token needs no DNS access.
The existing `OPENXBL_API_KEY` secret remains unchanged.

Both website CNAME records point to `chojecki-net.pages.dev`, with Cloudflare
proxying enabled. A zone Single Redirect sends `www.chojecki.net` to the HTTPS
apex while preserving paths and queries. Mail and verification DNS records are
independent of hosting. See [the migration runbook](scripts/cloudflare/README.md)
for configuration, validation history, and rollback instructions.

The repository is `patrykchojecki/chojecki.net`. The old
`patrykchojecki.github.io` website address is retired; use `https://chojecki.net`.
Old GitHub repository links redirect to the renamed repository.

The previous `.github/workflows/static.yml` is a manual GitHub Pages rollback
workflow. Its custom-domain association and `CNAME` file are retained; it no
longer runs on pushes or a schedule.

Actions are pinned to verified commit hashes. Dependabot checks GitHub Actions,
npm, and Bundler dependencies weekly, grouping version updates into a separate
pull request for each ecosystem; review and merge those updates normally.
The Cloudflare workflow has read-only repository access and publishes using the scoped deployment token.

The existing `check:site` gate also rejects environment files, private keys, credential JSON files, and sensitive configuration directories anywhere in `_site/`. It reports paths only. Keep private files outside published content; adding a new secret filename convention requires updating the exclusions in `_config.yml` and `.gitignore` and the patterns in `scripts/check-site.py`.

## Troubleshooting

### Bundler cannot find the required version

Confirm that `ruby --version` reports Ruby 3.4.11 and that `which ruby` points to the intended version manager, then reinstall the locked Bundler version:

```sh
gem install bundler -v 4.0.9
bundle install
```

### The local server cannot start on port 4001

Stop the process already using the port, or start Jekyll on another port:

```sh
bundle exec jekyll serve --config _config.yml,_config.dev.yml --host 127.0.0.1 --port 4002
```

### Xbox activity is missing in production

Check that the `OPENXBL_API_KEY` GitHub secret is configured, the OpenXBL account is linked to Xbox, and the Xbox profile’s title-history privacy setting is visible.

## Privacy and license

The live site uses Cloudflare’s basic analytics. No additional visitor information is collected by this repository.

The inherited themes and this repository are available under the [MIT License](LICENSE).

## Reference

- [Cloudflare Pages Direct Upload with CI](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)
- [Cloudflare Pages custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)
