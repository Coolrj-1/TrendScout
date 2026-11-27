import tempfile
import unittest
from datetime import date
from pathlib import Path
from trendscout.core import collect, score_repositories, render_markdown

class TrendScoutTests(unittest.TestCase):
    def setUp(self):
        self.repo = {"full_name": "demo/project", "html_url": "https://github.com/demo/project",
                     "description": "Demo", "stargazers_count": 120, "forks_count": 10,
                     "language": "Python", "created_at": "2026-11-01T00:00:00Z",
                     "pushed_at": "2026-11-26T00:00:00Z", "topics": ["ai"]}

    def test_collect_deduplicates_repositories(self):
        result = collect({"topics": ["AI agent", "MCP"], "per_query": 10},
                         today=date(2026, 11, 27), search_fn=lambda query, count: [self.repo])
        self.assertEqual(len(result["repositories"]), 1)
        self.assertEqual(result["repositories"][0]["full_name"], "demo/project")

    def test_growth_uses_week_old_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            old = {"repositories": [{"full_name": "demo/project", "stars": 100}]}
            (folder / "2026-11-20.json").write_text(__import__("json").dumps(old))
            snapshot = {"date": "2026-11-27", "repositories": [{
                "full_name": "demo/project", "stars": 120, "created_at": "2026-11-01T00:00:00Z",
                "category": "AI agent", "html_url": "https://github.com/demo/project", "language": "Python"}]}
            ranked = score_repositories(snapshot, folder)
            self.assertEqual(ranked[0]["stars_7d"], 20)
            self.assertEqual(ranked[0]["trend_status"], "rising")

    def test_missing_history_is_not_fabricated(self):
        with tempfile.TemporaryDirectory() as temp:
            ranked = score_repositories({"date": "2026-11-27",
                "repositories": [{"full_name": "demo/project", "stars": 5}]}, Path(temp))
            self.assertIsNone(ranked[0]["stars_7d"])
            self.assertEqual(ranked[0]["trend_status"], "new/untracked")

    def test_markdown_report(self):
        text = render_markdown({"date": "2026-11-27"}, [{
            "full_name": "demo/project", "html_url": "https://github.com/demo/project",
            "stars": 120, "stars_7d": 20, "category": "AI", "language": "Python"}])
        self.assertIn("demo/project", text)
        self.assertIn("+20", text)

if __name__ == "__main__":
    unittest.main()
