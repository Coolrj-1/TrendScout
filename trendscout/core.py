from __future__ import annotations
import argparse
import json
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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
    }

def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def collect(config: dict, today: date | None = None, search_fn=github_search) -> dict:
    today = today or datetime.now(timezone.utc).date()
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    unique: dict[str, dict] = {}
    topics = config.get("topics", [])
    per_query = max(1, min(int(config.get("per_query", 30)), 100))
    for index, query in enumerate(topics):
        for raw in search_fn(query, per_query):
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

def find_comparison(repo_name: str, current_date: date, snapshots_dir: Path = SNAPSHOTS):
    candidates = []
    for path in snapshots_dir.glob("*.json"):
        try:
            age = (current_date - date.fromisoformat(path.stem)).days
        except ValueError:
            continue
        if 6 <= age <= 8:
            candidates.append((abs(age - 7), path))
    if not candidates:
        return None
    _, selected = min(candidates, key=lambda x: x[0])
    for repo in load_json(selected, {}).get("repositories", []):
        if repo.get("full_name") == repo_name:
            return int(repo.get("stars", 0))
    return None

def score_repositories(snapshot: dict, snapshots_dir: Path = SNAPSHOTS) -> list[dict]:
    current_date = date.fromisoformat(snapshot["date"])
    ranked = []
    for repo in snapshot.get("repositories", []):
        previous = find_comparison(repo["full_name"], current_date, snapshots_dir)
        item = dict(repo)
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
    (REPORTS / "latest.json").write_text(json.dumps({"snapshot": snapshot, "ranked": ranked}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
