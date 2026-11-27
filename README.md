# TrendScout

**A lightweight, open-source radar for rising GitHub projects.**

TrendScout collects public GitHub repository data across fast-moving developer topics, stores daily snapshots, compares current stars with older snapshots, and produces a ranked Markdown report plus JSON data.

## Why this project?

A November 27, 2026 scan of public trend trackers showed strong momentum around AI coding agents, agent skills and MCP integrations, computer-use agents, AI-assisted creator tools, and local/self-hosted AI tooling. TrendScout builds its own dated dataset instead of treating a trending list as timeless truth.

## Features

- Searches GitHub's public repository API by configurable topic queries
- Captures stars, forks, language, description, topics, creation date and URL
- Saves dated snapshots in `data/snapshots/`
- Estimates 7-day star growth when a snapshot from roughly a week earlier exists
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
- [ ] Add a small static dashboard
- [ ] Add repository health signals (recent commits, issue response, releases)

## Data and privacy

TrendScout only reads public GitHub repository metadata. It does not clone projects, execute their code, or collect private user data. Set `GITHUB_TOKEN` only through a secure environment variable or GitHub Actions secret; never commit tokens.

## License

MIT. See [LICENSE](LICENSE).
