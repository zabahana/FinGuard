import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from finguard.web import JobManager, WebServer, sandbox_name


class LocalWebTests(unittest.TestCase):
    def setUp(self):
        self.manager = JobManager()
        self.server = WebServer(0, self.manager)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.client = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, body=None, headers=None):
        request = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(), headers=headers or {})
        try:
            response = self.client.open(request)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            return response.status, response.read()

    def test_no_arbitrary_file_access(self):
        for path in ("/.env", "/.local/openshell/tls-desktop/client/tls.key", "/../README.md", "/api/../../README.md"):
            self.assertEqual(self.request(path)[0], 404)

    def test_cross_origin_and_dns_rebinding_rejected(self):
        self.assertEqual(self.request("/api/state", headers={"Host": "attacker.example"})[0], 403)
        self.assertEqual(self.request("/api/state", headers={"Origin": "https://example.com"})[0], 403)
        self.assertEqual(self.request("/api/state", headers={"Sec-Fetch-Site": "cross-site"})[0], 403)

    def test_mutation_requires_token_and_exact_action_schema(self):
        self.assertEqual(self.request("/api/jobs", {"action": "train"})[0], 403)
        headers = {"Content-Type": "application/json", "X-FinGuard-Token": self.server.token}
        self.assertEqual(self.request("/api/jobs", {"action": "sh -c anything"}, headers)[0], 400)
        self.assertEqual(self.request("/api/jobs", {"action": "train", "command": "anything"}, headers)[0], 400)

    def test_single_job_exclusion(self):
        self.manager.job = {"status": "running"}
        headers = {"Content-Type": "application/json", "X-FinGuard-Token": self.server.token}
        self.assertEqual(self.request("/api/jobs", {"action": "train"}, headers)[0], 409)

    def test_state_and_assets(self):
        code, data = self.request("/api/state")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(data)["token"], self.server.token)
        self.assertEqual(self.request("/")[0], 200)
        self.assertEqual(self.request("/assets/components.svg")[0], 200)


class JobFailureTests(unittest.TestCase):
    def test_generated_sandbox_name_matches_runtime_constraint(self):
        name = sandbox_name()
        self.assertLessEqual(len(name), 19)
        self.assertRegex(name, r"^[a-z][a-z0-9-]+$")

    def test_failure_preserves_published_results_and_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp, patch("finguard.web.ROOT", Path(temp)):
            manager = JobManager()
            previous = {"training": {"sentinel": "previous valid report"}}
            manager.result = previous
            job = {"id": "test", "action": "train", "status": "running", "steps": [], "logs": [],
                   "started_at": "now", "finished_at": None, "sandbox": None, "error": None}
            with patch.object(manager, "command", side_effect=RuntimeError("training failed")):
                manager.run(job)
            self.assertEqual(job["status"], "failed")
            self.assertEqual(job["steps"][-1]["status"], "failed")
            self.assertEqual(manager.result, previous)
            restarted = JobManager()
            self.assertEqual(restarted.result, previous)
            self.assertTrue((Path(temp) / "artifacts/web/jobs/test/job.json").exists())


if __name__ == "__main__":
    unittest.main()
