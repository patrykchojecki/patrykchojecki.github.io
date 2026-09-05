# chojecki.net

Source for [chojecki.net](https://chojecki.net), Patryk Chojecki’s personal website. The site is built with Jekyll and deployed to GitHub Pages from the `master` branch.

The project began as a fork of [Academic Pages](https://github.com/academicpages/academicpages.github.io), which is based on the [Minimal Mistakes Jekyll theme](https://mmistakes.github.io/minimal-mistakes/).

## Prerequisites

Install the versions pinned by the repository:

- Ruby 3.4.4
- Bundler 4.0.9
- Node.js 26
- npm 10 or newer

Using a Ruby and Node version manager is recommended. Confirm the active toolchain before installing dependencies:

```sh
ruby --version
bundle --version
node --version
npm --version
```

## Setup

```sh
git clone https://github.com/patrykchojecki/patrykchojecki.github.io.git
cd patrykchojecki.github.io
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

## Build and test

Run the same JavaScript and production Jekyll build used for a local check:

```sh
npm run check
```

Test the OpenXBL data normalization separately:

```sh
npm test
```

The generated site is written to `_site/`.

## Xbox activity

The `/now` page displays Xbox activity from `_data/xbox.json`. GitHub Actions generates this ignored file with `scripts/fetch-openxbl.mjs`; local development falls back to the tracked preview data.

Live Xbox activity requires an `OPENXBL_API_KEY` repository secret linked to an OpenXBL account whose Xbox profile and title history are visible. The key is not required to serve or build the site locally with preview data. If a production refresh fails or the secret is missing, the site still deploys with the activity card omitted. Unavailable achievement data does not hide a successfully fetched profile and game.

## Deployment

Pushing to `master` triggers `.github/workflows/static.yml`, which:

1. Installs the pinned Node and Ruby dependencies.
2. Builds the JavaScript assets and tests the OpenXBL mapping.
3. Fetches the latest Xbox activity.
4. Builds and deploys the site to GitHub Pages.

The workflow also refreshes the deployment every six hours and can be run manually from GitHub Actions.

## Troubleshooting

### Bundler cannot find the required version

Confirm that `ruby --version` reports Ruby 3.4.4 and that `which ruby` points to the intended version manager, then reinstall the locked Bundler version:

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

- [Configure a custom GitHub Pages domain with Cloudflare](https://ictsolved.github.io/configure-custom-domain-and-sub-domain-with-github-pages-in-cloudflare/)
