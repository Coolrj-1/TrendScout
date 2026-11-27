import tempfile
import unittest
from datetime import date
from pathlib import Path
from trendscout.core import collect, normalize, score_repositories, render_markdown, repository_health, find_comparison

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

    def test_normalize_keeps_repository_metadata(self):
        raw = {**self.repo, "homepage": "https://example.com", "license": {"spdx_id": "MIT"},
               "default_branch": "main", "open_issues_count": 4, "watchers_count": 20,
               "size": 512, "visibility": "public", "archived": False, "has_wiki": True,
               "has_pages": False, "owner": {"type": "Organization"}}
        item = normalize(raw, "AI agent", "2026-11-27T00:00:00Z")
        self.assertEqual(item["license"], "MIT")
        self.assertEqual(item["open_issues"], 4)
        self.assertEqual(item["watchers"], 20)
        self.assertEqual(item["size_kb"], 512)
        self.assertEqual(item["owner_type"], "Organization")
        self.assertTrue(item["has_wiki"])

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


    def test_30_day_growth_and_health_signals(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            old = {"repositories": [{"full_name": "demo/project", "stars": 80}]}
            (folder / "2026-10-28.json").write_text(__import__("json").dumps(old))
            snapshot = {"date": "2026-11-27", "repositories": [{
                "full_name": "demo/project", "stars": 120, "created_at": "2026-11-01T00:00:00Z",
                "pushed_at": "2026-11-26T00:00:00Z", "license": "MIT", "open_issues": 2,
                "category": "AI", "html_url": "https://github.com/demo/project", "language": "Python"}]}
            ranked = score_repositories(snapshot, folder)
            self.assertEqual(ranked[0]["stars_30d"], 40)
            self.assertEqual(ranked[0]["health_score"], 100)
            self.assertEqual(ranked[0]["health_label"], "Strong signals")

    def test_archived_unlicensed_repo_gets_health_warnings(self):
        from trendscout.core import repository_health
        result = repository_health({"archived": True, "license": "Not specified",
                                    "pushed_at": "2024-01-01T00:00:00Z"}, date(2026, 11, 27))
        self.assertLess(result["health_score"], 40)
        self.assertGreaterEqual(len(result["health_reasons"]), 3)

    def test_markdown_report(self):
        text = render_markdown({"date": "2026-11-27"}, [{
            "full_name": "demo/project", "html_url": "https://github.com/demo/project",
            "stars": 120, "stars_7d": 20, "category": "AI", "language": "Python"}])
        self.assertIn("demo/project", text)
        self.assertIn("+20", text)


    def test_health_score_flags_archived_and_unlicensed_repositories(self):
        item = repository_health({'archived': True, 'license': 'Not specified', 'pushed_at': '2020-01-01T00:00:00Z'}, date(2026, 11, 27))
        self.assertEqual(item['health_score'], 0)
        self.assertEqual(item['health_label'], 'Needs review')
        self.assertIn('Archived repository', item['health_notes'])

    def test_30_day_comparison_uses_historical_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            old = {'repositories': [{'full_name': 'demo/project', 'stars': 80}]}
            (folder / '2026-10-28.json').write_text(__import__('json').dumps(old))
            self.assertEqual(find_comparison('demo/project', date(2026, 11, 27), folder, 30), 80)

if __name__ == "__main__":
    unittest.main()
