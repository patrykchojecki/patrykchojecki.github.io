source "https://rubygems.org"

gem "jekyll", "~> 3.10"
gem "jekyll-sass-converter", "~> 1.5"
gem "kramdown-parser-gfm"

# Gems removed from Ruby stdlib in 3.4+
gem "base64"
gem "bigdecimal"
gem "csv"
gem "logger"

gem "wdm", "~> 0.1.0" if Gem.win_platform?

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-sitemap"
  gem "jekyll-paginate"
  gem "jekyll-gist"
  gem "jekyll-redirect-from"
  gem "jekyll-seo-tag"
  gem "jekyll-include-cache"
end

group :development do
  gem "webrick"
  gem "hawkins"
end
