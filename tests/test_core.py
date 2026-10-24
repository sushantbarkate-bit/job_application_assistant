import tempfile
import unittest
from pathlib import Path

from job_assistant.matcher import score_job
from job_assistant.models import Job
from job_assistant.providers import DemoProvider, PortalSearchLinks
from job_assistant.storage import Store


class JobAssistantTests(unittest.TestCase):
    def test_demo_provider_returns_matching_sample_jobs_offline(self):
        jobs = DemoProvider().search(
            ["Angular Developer", "Frontend Developer", "Java Full Stack Developer"],
            ["Pune", "Remote"],
            50,
        )
        self.assertGreaterEqual(len(jobs), 3)
        self.assertTrue(all(job.source == "demo" for job in jobs))

    def test_matcher_returns_bounded_score_and_skills(self):
        job = Job(
            "test-1", "Angular Developer", "Example Co", "Pune",
            "Angular TypeScript REST APIs", "https://example.com/job/1"
        )
        result = score_job(job, {
            "skills": ["Angular", "TypeScript", "Java"],
            "target_titles": ["Angular Developer"],
            "target_locations": ["Pune"],
        })
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertIn("angular", result["matched_skills"])

    def test_store_add_update_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(str(Path(tmp) / "nested" / "jobs.sqlite3"))
            job = Job("test-2", "Frontend Developer", "Example Co", "Remote", "Angular", "https://example.com")
            store.add(job, 75, "matched", "test")
            self.assertEqual(store.rows()[0][0], "test-2")
            store.update_status("test-2", "approved_for_review", "manual review")
            self.assertEqual(store.rows()[0][6], "approved_for_review")
            store.db.close()

    def test_portal_links_are_generated(self):
        links = PortalSearchLinks.build(["Angular Developer"], ["Pune"])
        self.assertEqual(len(links), 2)
        self.assertTrue(all(item["url"].startswith("https://") for item in links))


if __name__ == "__main__":
    unittest.main()
