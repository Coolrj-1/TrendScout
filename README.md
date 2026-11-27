# TrendScout

**A lightweight, open-source radar for rising GitHub projects.**

Live dashboard: https://trendscout.pages.dev/ · [Explore discoveries](https://trendscout.pages.dev/dashboard/) · [AI GitHub project watchlist](https://trendscout.pages.dev/guides/ai-github-projects-to-watch/) · [Latest report](https://trendscout.pages.dev/reports/latest.md) · [Methodology](https://trendscout.pages.dev/about/)

TrendScout collects public GitHub repository data across fast-moving developer topics, stores daily snapshots, compares current stars with older snapshots, and produces a ranked Markdown report plus JSON data.

## Why this project?

A November 27, 2026 scan of public trend trackers showed strong momentum around AI coding agents, agent skills and MCP integrations, computer-use agents, AI-assisted creator tools, and local/self-hosted AI tooling. TrendScout builds its own dated dataset instead of treating a trending list as timeless truth.

## Features

- Searches GitHub's public repository API by configurable topic queries
- Captures stars, forks, language, description, topics, creation/push dates, homepage, license, default branch, open issues, watchers, repository size, visibility, archive status, wiki/Pages flags and owner type when GitHub provides them
- Saves dated snapshots in `data/snapshots/`
- Estimates 7-day star growth when a snapshot from roughly a week earlier exists\n- Provides searchable project cards with repository metadata, topic tags and clone commands\n- Samples public pull-request discussions and review states (approvals, changes requested and comments) for recent PRs\n- Includes step-by-step guides for using TrendScout, evaluating AI coding agents and understanding MCP servers
- Ranks projects using star growth, growth rate and freshness
- Writes `reports/latest.md` and `reports/latest.json`
- Runs daily with GitHub Actions
- Uses only Python's standard library

## Quick start

Requires Python 3.10+.

```bash
python -m trendscout --once
```

Optional GitHub token (recommended for higher API limits):

```bash
# macOS/Linux
export GITHUB_TOKEN="YOUR_TOKEN"
python -m trendscout --once

# PowerShell
$env:GITHUB_TOKEN="YOUR_TOKEN"
python -m trendscout --once
```

No token is required for a small public scan, but GitHub rate limits apply.

## Configure topics

Edit `config/topics.json`. Each entry is a GitHub repository search query. Keep queries focused; GitHub Search API has a limit of 10 requests per minute for unauthenticated search.

## How the score works

When a comparable snapshot exists:

- `stars_7d` = current stars minus stars in the nearest snapshot 6–8 days old
- `growth_rate_7d` = `stars_7d / max(previous_stars, 1)`
- `trend_score` combines absolute growth, growth rate and repository freshness

This is a heuristic, not a measure of product quality. Star counts can be noisy, snapshots may be incomplete, and new repositories can have unusually high percentage growth. Reports label missing comparisons as `new/untracked` rather than inventing growth.

## Using TrendScout\n\n1. Open the [live dashboard](https://trendscout.pages.dev/dashboard/).\n2. Search by repository name, keyword, language or topic.\n3. Filter by category and sort by trend score, lifetime stars, measured 7-day growth or last push.\n4. Expand **Repository details** to inspect metadata and copy the Git clone command.\n5. Open the project on GitHub and read its README, license, releases, issues and security policy before installing it.\n\nGuides: [How to use TrendScout](https://trendscout.pages.dev/guides/using-trendscout/) · [AI coding agents](https://trendscout.pages.dev/guides/ai-coding-agents/) · [MCP servers](https://trendscout.pages.dev/guides/mcp-servers/)\n\n## Repository metadata\n\nThe scanner stores GitHub fields including `full_name`, `description`, `html_url`, `stars`, `forks`, `language`, `topics`, `created_at`, `pushed_at`, `homepage`, `license`, `default_branch`, `open_issues`, `watchers`, `size_kb`, `visibility`, `archived`, `has_wiki`, `has_pages`, and `owner_type`. Optional fields may be empty or unavailable depending on the GitHub response. Public review summaries are sampled from up to three recently updated pull requests per selected repository; they are not lifetime review totals or private feedback. TrendScout does not fetch or execute repository source code.\n\n## Dashboard and latest report

The dashboard is deployed on Cloudflare Pages. The build also publishes an SEO-friendly homepage, methodology page, `robots.txt`, and `sitemap.xml`. In Cloudflare, connect this repository with build command `bash scripts/build_pages.sh` and build output directory `public` (no framework preset and no root-directory override). The build script publishes the dashboard and its JSON/Markdown reports together, so the dashboard data path works on the deployed site. The site root redirects visitors to `/dashboard/`.


- Dashboard source: [dashboard/index.html](dashboard/index.html)
- Latest report: [reports/latest.md](reports/latest.md)
- Latest machine-readable snapshot: [reports/latest.json](reports/latest.json)

To preview the dashboard locally, run a static server from the repository root:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/dashboard/`. The dashboard loads its data from `reports/latest.json`.

## Website discovery

The public site includes descriptive page titles, canonical URLs, Open Graph metadata, a crawlable homepage, a methodology page, `robots.txt`, and an XML sitemap. Submit `https://trendscout.pages.dev/sitemap.xml` to Google Search Console and Bing Webmaster Tools to request indexing; indexing and rankings are controlled by those search engines and are not guaranteed.

## Traffic analytics

TrendScout can use Cloudflare Web Analytics without adding a third-party advertising tracker. To enable it:

1. In the Cloudflare dashboard, open **Analytics & Logs → Web Analytics**.
2. Add the site hostname `trendscout.pages.dev` and copy the generated token.
3. In **Workers & Pages → TrendScout → Settings → Variables and Secrets**, add `CLOUDFLARE_WEB_ANALYTICS_TOKEN` as an environment variable for production builds.
4. Trigger a new Pages deployment. The build script can inject the Cloudflare beacon when this variable is present; without the token, no analytics script is added.

The site owner must create the Web Analytics property and supply its token. Do not commit the token to GitHub. Analytics data appears only after deployment and visitor activity; it is not retroactive.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
trendscout/
├── config/topics.json
├── data/snapshots/
├── reports/
├── tests/
├── trendscout/
│   ├── __init__.py
│   ├── __main__.py
│   └── core.py
└── .github/workflows/daily-scan.yml
```

## Roadmap

- [ ] Add GitHub Trending HTML as a second discovery source
- [ ] Add Hacker News launch signals
- [ ] Add category-specific score weights
- [x] Publish a responsive static dashboard
- [ ] Add repository health signals (recent commits, issue response, releases)

## Data and privacy

TrendScout only reads public GitHub repository metadata. It does not clone projects, execute their code, or collect private user data. Set `GITHUB_TOKEN` only through a secure environment variable or GitHub Actions secret; never commit tokens.

## License

MIT. See [LICENSE](LICENSE).
