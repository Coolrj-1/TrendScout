from __future__ import annotations

import json
from html.parser import HTMLParser
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


def _get(url: str, user_agent: str = "TrendScout/0.2") -> bytes:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/json,text/html"})
    with urlopen(request, timeout=12) as response:
        return response.read()


def hacker_news_signals(limit: int = 20) -> list[dict]:
    """Return recent HN stories that link to GitHub repositories; never affect GitHub star ranking."""
    url = "https://hn.algolia.com/api/v1/search_by_date?query=github.com&tags=story&hitsPerPage=" + str(limit)
    try:
        payload = json.loads(_get(url).decode("utf-8"))
    except Exception:
        return []
    signals = []
    for hit in payload.get("hits", []):
        link = hit.get("url") or ""
        parsed = urlparse(link)
        parts = [p for p in parsed.path.split("/") if p]
        if parsed.hostname not in {"github.com", "www.github.com"} or len(parts) < 2:
            continue
        signals.append({
            "title": hit.get("title") or "GitHub project discussion",
            "repository": "/".join(parts[:2]),
            "url": link,
            "discussion_url": "https://news.ycombinator.com/item?id=" + str(hit.get("objectID", "")),
            "points": int(hit.get("points") or 0),
            "comments": int(hit.get("num_comments") or 0),
            "created_at": hit.get("created_at"),
            "source": "Hacker News",
        })
    return signals


class _TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._repo = None
        self._description = False
        self._text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "Box-row" in attrs.get("class", ""):
            self._repo = None
            self._text = []
        if self._repo is None and tag == "h2":
            self._description = True
        if self._description and tag == "a":
            href = attrs.get("href", "")
            if href.count("/") == 2 and href.startswith("/"):
                self._repo = href.strip("/")
        if self._repo and tag == "p":
            self._description = False
            self._text = []

    def handle_data(self, data):
        if self._repo and not self._description:
            self._text.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "article" and self._repo:
            self.items.append({"repository": self._repo,
                               "url": "https://github.com/" + self._repo,
                               "description": " ".join(x for x in self._text if x),
                               "source": "GitHub Trending"})


def github_trending_signals() -> list[dict]:
    """Fetch GitHub's public daily trending page as a secondary discovery signal."""
    try:
        parser = _TrendingParser()
        parser.feed(_get("https://github.com/trending?since=daily").decode("utf-8", "replace"))
        seen = set()
        result = []
        for item in parser.items:
            if item["repository"] not in seen:
                seen.add(item["repository"])
                result.append(item)
        return result
    except Exception:
        return []
