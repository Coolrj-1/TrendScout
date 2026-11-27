from __future__ import annotations
import argparse
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from trendscout.external_sources import github_trending_signals, hacker_news_signals

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "topics.json"
SNAPSHOTS = ROOT / "data" / "snapshots"
REPORTS = ROOT / "reports"

def github_search(query: str, per_page: int = 30) -> list[dict]:
    params = urlencode({"q": query + " archived:false", "sort": "stars", "order": "desc", "per_page": per_page})
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "TrendScout/0.1", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/search/repositories?{params}", headers=headers)
    try:
        with urlopen(request, timeout=25) as response:
            return json.loads(response.read().decode("utf-8")).get("items", [])
    except HTTPError as exc:
        if exc.code == 403:
            raise RuntimeError("GitHub API rate limit or permission error. Set GITHUB_TOKEN and retry.") from exc
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc}") from exc

def normalize(repo: dict, category: str, captured_at: str) -> dict:
    return {
        "full_name": repo.get("full_name", ""), "html_url": repo.get("html_url", ""),
        "description": repo.get("description") or "", "stars": int(repo.get("stargazers_count") or 0),
        "forks": int(repo.get("forks_count") or 0), "language": repo.get("language") or "Unknown",
        "created_at": repo.get("created_at"), "pushed_at": repo.get("pushed_at"),
        "topics": repo.get("topics") or [], "category": category, "captured_at": captured_at,
        "homepage": repo.get("homepage") or "",
        "license": (repo.get("license") or {}).get("spdx_id") or "Not specified",
        "default_branch": repo.get("default_branch") or "main",
        "open_issues": int(repo.get("open_issues_count") or 0),
        "watchers": int(repo.get("watchers_count") or 0),
        "size_kb": int(repo.get("size") or 0),
        "visibility": repo.get("visibility") or "public",
        "archived": bool(repo.get("archived", False)),
        "has_wiki": bool(repo.get("has_wiki", False)),
        "has_pages": bool(repo.get("has_pages", False)),
        "owner_type": (repo.get("owner") or {}).get("type") or "Unknown",
        "archived": bool(repo.get("archived", False)),
    }

def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def collect(config: dict, today: date | None = None, search_fn=github_search) -> dict:
    today = today or datetime.now(timezone.utc).date()
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    unique: dict[str, dict] = {}
    topics = config.get("topics", [])
    per_query = max(1, min(int(config.get("per_query", 30)), 100))
    lookback_days = max(1, int(config.get("lookback_days", 30)))
    pushed_after = (today - timedelta(days=lookback_days)).isoformat()
    for index, query in enumerate(topics):
        dated_query = f"{query} pushed:>{pushed_after} archived:false"
        for raw in search_fn(dated_query, per_query):
            item = normalize(raw, query, captured_at)
            if not item["full_name"]:
                continue
            old = unique.get(item["full_name"])
            if old is None or item["stars"] > old["stars"]:
                unique[item["full_name"]] = item
        if index < len(topics) - 1:
            time.sleep(1.1)
    return {"date": today.isoformat(), "captured_at": captured_at,
            "repositories": sorted(unique.values(), key=lambda x: x["stars"], reverse=True)}

def find_comparison(repo_name: str, current_date: date, snapshots_dir: Path = SNAPSHOTS, target_days: int = 7):
    candidates = []
    for path in snapshots_dir.glob("*.json"):
        try:
            age = (current_date - date.fromisoformat(path.stem)).days
        except ValueError:
            continue
        if max(1, target_days - 1) <= age <= target_days + 1:
            candidates.append((abs(age - target_days), path))
    if not candidates:
        return None
    _, selected = min(candidates, key=lambda x: x[0])
    for repo in load_json(selected, {}).get("repositories", []):
        if repo.get("full_name") == repo_name:
            return int(repo.get("stars", 0))
    return None

def find_historical_comparison(repo_name: str, current_date: date, min_age: int, max_age: int, snapshots_dir: Path = SNAPSHOTS):
    candidates = []
    for path in snapshots_dir.glob('*.json'):
        try:
            age = (current_date - date.fromisoformat(path.stem)).days
        except ValueError:
            continue
        if min_age <= age <= max_age:
            candidates.append((abs(age - (min_age + max_age) / 2), path))
    if not candidates:
        return None
    _, selected = min(candidates, key=lambda x: x[0])
    for repo in load_json(selected, {}).get('repositories', []):
        if repo.get('full_name') == repo_name:
            return int(repo.get('stars', 0))
    return None

def repository_health(repo: dict, current_date: date) -> dict:
    score, reasons = 100, []
    if repo.get('archived'):
        score -= 45; reasons.append('Archived repository')
    if not repo.get('license') or repo.get('license') in {'Not specified', 'NOASSERTION'}:
        score -= 15; reasons.append('No recognized license')
    try:
        age = (current_date - date.fromisoformat((repo.get('pushed_at') or '')[:10])).days
    except ValueError:
        age = None
    if age is None:
        score -= 15; reasons.append('Last activity date unavailable')
    elif age > 365:
        score -= 35; reasons.append('No push in over a year')
    elif age > 180:
        score -= 20; reasons.append('No push in over six months')
    elif age > 90:
        score -= 10; reasons.append('No push in over three months')
    score = max(0, min(100, score))
    label = 'Strong signals' if score >= 80 else 'Some caution' if score >= 55 else 'Needs review'
    return {'health_score': score, 'health_label': label, 'health_notes': reasons, 'health_method': 'Metadata heuristic: archive status, recognized license and last-push recency'}

def collect_hacker_news(config: dict, limit: int = 5) -> list[dict]:
    queries = config.get('hackernews_queries', [])
    found = {}
    for query in queries[:5]:
        url = 'https://hn.algolia.com/api/v1/search?' + urlencode({'query': query, 'tags': 'story', 'hitsPerPage': limit})
        try:
            request = Request(url, headers={'User-Agent': 'TrendScout/0.2'})
            with urlopen(request, timeout=12) as response:
                hits = json.loads(response.read().decode('utf-8')).get('hits', [])
            for hit in hits:
                oid = str(hit.get('objectID') or '')
                if not oid: continue
                found[oid] = {'title': hit.get('title') or 'Untitled Hacker News story', 'url': hit.get('url') or 'https://news.ycombinator.com/item?id=' + oid, 'hn_url': 'https://news.ycombinator.com/item?id=' + oid, 'points': int(hit.get('points') or 0), 'comments': int(hit.get('num_comments') or 0), 'created_at': hit.get('created_at'), 'matched_query': query, 'source': 'Hacker News / Algolia'}
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            continue
    return sorted(found.values(), key=lambda x: (x['points'], x['comments']), reverse=True)[:limit * 3]
def repository_health(repo: dict, current_date: date) -> dict:
    """Transparent metadata-only maintenance heuristic; not a security audit."""
    score = 100
    reasons = []
    if repo.get("archived"):
        score -= 55
        reasons.append("Repository is archived")
    if (repo.get("license") or "Not specified") in {"Not specified", "NOASSERTION"}:
        score -= 15
        reasons.append("No recognized license reported")
    try:
        age = (current_date - date.fromisoformat(repo["pushed_at"][:10])).days
        if age > 365:
            score -= 30
            reasons.append("No push in over a year")
        elif age > 180:
            score -= 20
            reasons.append("No push in over six months")
        elif age > 90:
            score -= 10
            reasons.append("No push in over three months")
    except (KeyError, TypeError, ValueError):
        score -= 10
        reasons.append("Last-push date unavailable")
    stars = max(int(repo.get("stars") or 0), 1)
    if int(repo.get("open_issues") or 0) > 100 and int(repo.get("open_issues") or 0) / stars > 0.2:
        score -= 10
        reasons.append("Large open-issue count relative to stars")
    return {"health_score": max(0, min(100, score)), "health_reasons": reasons,
            "health_label": "Strong signals" if score >= 80 else "Mixed signals" if score >= 55 else "Needs review"}


def score_repositories(snapshot: dict, snapshots_dir: Path = SNAPSHOTS) -> list[dict]:
    current_date = date.fromisoformat(snapshot["date"])
    ranked = []
    for repo in snapshot.get("repositories", []):
        previous = find_comparison(repo["full_name"], current_date, snapshots_dir, 7)
        previous_30d = find_comparison(repo["full_name"], current_date, snapshots_dir, 30)
        item = dict(repo)
        item.update(repository_health(item, current_date))
        previous_30d = find_historical_comparison(repo['full_name'], current_date, 27, 33, snapshots_dir)
        item['previous_stars_30d'] = previous_30d
        item['stars_30d'] = item['stars'] - previous_30d if previous_30d is not None else None
        if previous is None:
            item.update({"previous_stars_7d": None, "stars_7d": None, "growth_rate_7d": None, "trend_score": None})
            item["trend_status"] = "new/untracked"
        else:
            delta = item["stars"] - previous
            rate = delta / max(previous, 1)
            try:
                age_days = max((current_date - date.fromisoformat(item["created_at"][:10])).days, 0)
            except (TypeError, ValueError):
                age_days = 30
            freshness = 1 / (1 + age_days / 30)
            score = max(delta, 0) * 0.7 + max(rate, 0) * 100 * 0.2 + freshness * 10
            item.update({"previous_stars_7d": previous, "stars_7d": delta,
                         "growth_rate_7d": round(rate, 4), "trend_score": round(score, 2)})
            item["trend_status"] = "rising" if delta > 0 else "flat/falling"
        item.update(repository_health(item, current_date))
        ranked.append(item)
    return sorted(ranked, key=lambda x: (x["trend_score"] is not None, x["trend_score"] or -1, x["stars"]), reverse=True)

def render_markdown(snapshot: dict, ranked: list[dict]) -> str:
    lines = ["# TrendScout — Daily GitHub Radar", "",
             f"> Snapshot: **{snapshot['date']}** · {len(ranked)} unique repositories", "",
             "Star growth is calculated only when a comparable snapshot from 6–8 days earlier exists. New/untracked means there is not enough stored history yet.",
             "", "| Rank | Repository | Stars | 7-day Δ | Category | Language |",
             "|---:|---|---:|---:|---|---|"]
    for index, repo in enumerate(ranked[:50], 1):
        delta = "—" if repo["stars_7d"] is None else f"{repo['stars_7d']:+,}"
        name = repo["full_name"].replace("|", r"\|")
        category = repo["category"].replace("|", r"\|")
        language = repo["language"].replace("|", r"\|")
        lines.append(f"| {index} | [{name}]({repo['html_url']}) | {repo['stars']:,} | {delta} | {category} | {language} |")
    lines += ["", "## Notes", "", "- Rankings are discovery signals, not endorsements or quality ratings.",
              "- Search results are limited by GitHub's API and the configured queries.",
              "- The first week builds history; growth comparisons become more useful after snapshots accumulate.", ""]
    return "\n".join(lines)

def run():
    config = load_json(CONFIG, {"topics": ["AI coding agent"], "per_query": 30})
    snapshot = collect(config)
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    snapshot_path = SNAPSHOTS / f"{snapshot['date']}.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ranked = score_repositories(snapshot)
    categories = sorted({repo["category"] for repo in ranked})
    dashboard_repositories = []
    for repo in ranked:
        dashboard_repositories.append({
            **repo,
            "url": repo.get("html_url", ""),
        })
    hacker_news = collect_hacker_news(config)
    dashboard_report = {
        "schema_version": 2,
        "generated_at": snapshot["captured_at"],
        "source": "GitHub public repository search and repository metadata API",
        "methodology": (
            "Projects are discovered using the configured topic searches and lookback window. "
            "Seven-day growth is shown only when a comparable snapshot from 6–8 days earlier exists. "
            "New/untracked projects do not have enough history for a growth claim. 30-day growth uses a comparable 29–31 day snapshot. Health is a metadata heuristic, not a security audit."
        ),
        "categories": categories,
        "repositories": dashboard_repositories,
        "hacker_news": hacker_news,
        "hacker_news_status": "available" if hacker_news else "no-results-or-temporarily-unavailable",
        "health_method": "Metadata heuristic only; not a security audit. Uses archive status, recognized license and last-push recency.",
    }
    (REPORTS / "latest.json").write_text(
        json.dumps(dashboard_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (REPORTS / "latest.md").write_text(render_markdown(snapshot, ranked), encoding="utf-8")
    print(f"Saved {len(snapshot['repositories'])} repositories to {snapshot_path}")
    print(f"Updated {REPORTS / 'latest.md'}")

def main():
    parser = argparse.ArgumentParser(description="Discover rising public GitHub repositories.")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit (default).")
    parser.parse_args()
    run()

if __name__ == "__main__":
    main()
