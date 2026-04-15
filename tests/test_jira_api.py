#!/usr/bin/env python3
"""Unit tests for jira-api.py — offline, no network calls."""

import base64
import importlib.util
import json
import os
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import jira-api.py as a module (filename has a hyphen)
SCRIPT_PATH = Path(__file__).resolve().parent.parent / "skills" / "jira" / "scripts" / "jira-api.py"
spec = importlib.util.spec_from_file_location("jira_api", SCRIPT_PATH)
jira_api = importlib.util.module_from_spec(spec)
sys.modules["jira_api"] = jira_api
spec.loader.exec_module(jira_api)


class TestBuildUrl(unittest.TestCase):
    def test_simple_endpoint(self):
        url = jira_api.build_url("https://example.atlassian.net", "/rest/api/3/myself")
        self.assertEqual(url, "https://example.atlassian.net/rest/api/3/myself")

    def test_trailing_slash_stripped(self):
        url = jira_api.build_url("https://example.atlassian.net/", "/rest/api/3/myself")
        self.assertEqual(url, "https://example.atlassian.net/rest/api/3/myself")

    def test_with_query_params(self):
        url = jira_api.build_url("https://ex.atlassian.net", "/rest/api/3/issue/FOO-1", {"fields": "summary,status"})
        self.assertEqual(url, "https://ex.atlassian.net/rest/api/3/issue/FOO-1?fields=summary%2Cstatus")

    def test_no_params(self):
        url = jira_api.build_url("https://ex.atlassian.net", "/rest/api/3/project", None)
        self.assertEqual(url, "https://ex.atlassian.net/rest/api/3/project")

    def test_existing_query_string_uses_ampersand(self):
        url = jira_api.build_url("https://ex.atlassian.net", "/rest/api/3/board?type=scrum", {"maxResults": "5"})
        self.assertEqual(url, "https://ex.atlassian.net/rest/api/3/board?type=scrum&maxResults=5")


class TestEnv(unittest.TestCase):
    @patch.dict(os.environ, {"JIRA_URL": "https://test.atlassian.net"})
    def test_returns_value_when_set(self):
        self.assertEqual(jira_api.env("JIRA_URL"), "https://test.atlassian.net")

    @patch.dict(os.environ, {}, clear=True)
    def test_exits_when_missing(self):
        with self.assertRaises(SystemExit):
            jira_api.env("JIRA_URL")

    @patch.dict(os.environ, {"JIRA_URL": ""})
    def test_exits_when_empty(self):
        with self.assertRaises(SystemExit):
            jira_api.env("JIRA_URL")


class TestMainArgParsing(unittest.TestCase):
    """Test that main() constructs correct requests for various argument patterns."""

    ENV = {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USERNAME": "user@example.com",
        "JIRA_PERSONAL_TOKEN": "tok123",
    }

    def _run_main(self, argv):
        """Run main() with given argv, intercepting the urllib.request.Request and urlopen."""
        captured = {}

        def fake_urlopen(req):
            captured["req"] = req
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = b'{"ok": true}'
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch.dict(os.environ, self.ENV), \
             patch.object(sys, "argv", ["jira-api.py"] + argv), \
             patch("jira_api.urllib.request.urlopen", side_effect=fake_urlopen):
            jira_api.main()

        return captured["req"]

    def test_get_request(self):
        req = self._run_main(["GET", "/rest/api/3/myself"])
        self.assertEqual(req.method, "GET")
        self.assertEqual(req.full_url, "https://test.atlassian.net/rest/api/3/myself")
        self.assertIsNone(req.data)

    def test_get_with_fields(self):
        req = self._run_main(["GET", "/rest/api/3/issue/FOO-1", "--fields", "summary,status"])
        self.assertIn("fields=summary%2Cstatus", req.full_url)
        self.assertEqual(req.method, "GET")

    def test_post_with_json_body(self):
        body = '{"fields": {"summary": "test"}}'
        req = self._run_main(["POST", "/rest/api/3/issue", body])
        self.assertEqual(req.method, "POST")
        self.assertEqual(json.loads(req.data), {"fields": {"summary": "test"}})
        self.assertEqual(req.get_header("Content-type"), "application/json")

    def test_put_with_json_body(self):
        body = '{"fields": {"summary": "updated"}}'
        req = self._run_main(["PUT", "/rest/api/3/issue/FOO-1", body])
        self.assertEqual(req.method, "PUT")
        self.assertEqual(json.loads(req.data), {"fields": {"summary": "updated"}})

    def test_delete_no_body(self):
        req = self._run_main(["DELETE", "/rest/api/3/issue/FOO-1"])
        self.assertEqual(req.method, "DELETE")
        self.assertIsNone(req.data)

    def test_auth_header(self):
        req = self._run_main(["GET", "/rest/api/3/myself"])
        expected = base64.b64encode(b"user@example.com:tok123").decode()
        self.assertEqual(req.get_header("Authorization"), f"Basic {expected}")

    def test_accept_header(self):
        req = self._run_main(["GET", "/rest/api/3/myself"])
        self.assertEqual(req.get_header("Accept"), "application/json")

    def test_method_case_insensitive(self):
        req = self._run_main(["get", "/rest/api/3/myself"])
        self.assertEqual(req.method, "GET")

    def test_missing_args_exits(self):
        with patch.object(sys, "argv", ["jira-api.py", "GET"]):
            with self.assertRaises(SystemExit):
                jira_api.main()


class TestSearchArgParsing(unittest.TestCase):
    """Test that the search subcommand constructs correct POST requests."""

    ENV = {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USERNAME": "user@example.com",
        "JIRA_PERSONAL_TOKEN": "tok123",
    }

    def _run_search(self, argv):
        captured = {}

        def fake_urlopen(req):
            captured["req"] = req
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = b'{"issues": [], "isLast": true}'
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch.dict(os.environ, self.ENV), \
             patch.object(sys, "argv", ["jira-api.py"] + argv), \
             patch("jira_api.urllib.request.urlopen", side_effect=fake_urlopen):
            jira_api.main()

        return captured["req"]

    def test_basic_search(self):
        req = self._run_search(["search", "project=FOO"])
        self.assertEqual(req.method, "POST")
        self.assertTrue(req.full_url.endswith("/rest/api/3/search/jql"))
        payload = json.loads(req.data)
        self.assertEqual(payload["jql"], "project=FOO")
        self.assertEqual(payload["maxResults"], 50)

    def test_search_with_max_results(self):
        req = self._run_search(["search", "project=FOO", "--max-results", "10"])
        payload = json.loads(req.data)
        self.assertEqual(payload["maxResults"], 10)

    def test_search_with_fields(self):
        req = self._run_search(["search", "status=Open", "--fields", "summary,status,assignee"])
        payload = json.loads(req.data)
        self.assertEqual(payload["fields"], ["summary", "status", "assignee"])

    def test_search_with_next_page(self):
        req = self._run_search(["search", "project=FOO", "--next-page", "TOKEN123"])
        payload = json.loads(req.data)
        self.assertEqual(payload["nextPageToken"], "TOKEN123")

    def test_search_no_startAt(self):
        req = self._run_search(["search", "project=FOO"])
        payload = json.loads(req.data)
        self.assertNotIn("startAt", payload)

    def test_search_all_flags(self):
        req = self._run_search([
            "search", "project=FOO AND status=Open",
            "--max-results", "25",
            "--fields", "summary,status",
            "--next-page", "abc",
        ])
        payload = json.loads(req.data)
        self.assertEqual(payload["jql"], "project=FOO AND status=Open")
        self.assertEqual(payload["maxResults"], 25)
        self.assertEqual(payload["fields"], ["summary", "status"])
        self.assertEqual(payload["nextPageToken"], "abc")

    def test_search_content_type(self):
        req = self._run_search(["search", "project=FOO"])
        self.assertEqual(req.get_header("Content-type"), "application/json")


class TestErrorHandling(unittest.TestCase):
    ENV = {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USERNAME": "user@example.com",
        "JIRA_PERSONAL_TOKEN": "tok123",
    }

    def test_http_error_exits_nonzero(self):
        import urllib.error

        def fake_urlopen(req):
            error_body = b'{"errorMessages": ["Not found"], "errors": {}}'
            raise urllib.error.HTTPError(
                url=req.full_url, code=404, msg="Not Found",
                hdrs={}, fp=BytesIO(error_body)
            )

        with patch.dict(os.environ, self.ENV), \
             patch.object(sys, "argv", ["jira-api.py", "GET", "/rest/api/3/issue/NOPE-999"]), \
             patch("jira_api.urllib.request.urlopen", side_effect=fake_urlopen), \
             self.assertRaises(SystemExit) as cm:
            jira_api.main()

        self.assertEqual(cm.exception.code, 1)

    def test_missing_env_var_exits(self):
        with patch.dict(os.environ, {"JIRA_URL": "", "JIRA_USERNAME": "", "JIRA_PERSONAL_TOKEN": ""}, clear=False), \
             patch.object(sys, "argv", ["jira-api.py", "GET", "/rest/api/3/myself"]), \
             self.assertRaises(SystemExit):
            jira_api.main()


if __name__ == "__main__":
    unittest.main()
