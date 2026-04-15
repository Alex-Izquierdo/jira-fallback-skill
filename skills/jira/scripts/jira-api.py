#!/usr/bin/env python3
"""Jira Cloud REST API client — no shell variable expansion needed.

Usage:
    python3 jira-api.py METHOD ENDPOINT [JSON_DATA]

Examples:
    python3 jira-api.py GET  /rest/api/3/myself
    python3 jira-api.py GET  /rest/api/3/issue/FOO-123
    python3 jira-api.py search 'project=FOO AND status=Open' --max-results 20
    python3 jira-api.py POST /rest/api/3/issue '{"fields": {"project": {"key": "FOO"}, ...}}'
    python3 jira-api.py PUT  /rest/api/3/issue/FOO-123 '{"fields": {"summary": "Updated"}}'

Environment variables (required):
    JIRA_URL              https://yourcompany.atlassian.net  (no trailing slash)
    JIRA_USERNAME         Atlassian account email
    JIRA_PERSONAL_TOKEN   Atlassian API token
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def die(msg):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(1)


def env(name):
    val = os.environ.get(name, "")
    if not val:
        die(f"Environment variable {name} is not set")
    return val


def build_url(base, endpoint, params=None):
    url = base.rstrip("/") + endpoint
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    return url


def handle_search():
    """JQL search using POST /rest/api/3/search/jql (replaces deprecated GET /rest/api/3/search).

    The new endpoint uses cursor-based pagination (nextPageToken) instead of startAt.
    """
    if len(sys.argv) < 3:
        die("Usage: jira-api.py search 'JQL query' [--max-results N] [--next-page TOKEN] [--fields f1,f2]")

    jql = sys.argv[2]
    max_results = 50
    next_page_token = None
    fields = None

    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--max-results" and i + 1 < len(sys.argv):
            max_results = int(sys.argv[i + 1])
            i += 2
        elif arg == "--next-page" and i + 1 < len(sys.argv):
            next_page_token = sys.argv[i + 1]
            i += 2
        elif arg == "--fields" and i + 1 < len(sys.argv):
            fields = [f.strip() for f in sys.argv[i + 1].split(",")]
            i += 2
        else:
            i += 1

    jira_url = env("JIRA_URL")
    username = env("JIRA_USERNAME")
    token = env("JIRA_PERSONAL_TOKEN")

    url = jira_url.rstrip("/") + "/rest/api/3/search/jql"
    payload = {"jql": jql, "maxResults": max_results}
    if next_page_token:
        payload["nextPageToken"] = next_page_token
    if fields:
        payload["fields"] = fields

    credentials = base64.b64encode(f"{username}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(json.dumps(data, indent=2))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(error_body)
        except json.JSONDecodeError:
            error_data = {"raw": error_body}
        print(json.dumps({"status": e.code, "error": error_data}, indent=2))
        sys.exit(1)
    except urllib.error.URLError as e:
        die(f"Connection error: {e.reason}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    # Check for the "search" subcommand shortcut
    if sys.argv[1].lower() == "search":
        return handle_search()

    method = sys.argv[1].upper()
    endpoint = sys.argv[2]
    body = None
    query_params = {}

    # Parse remaining args: either a JSON body or --flag value pairs
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--fields" and i + 1 < len(sys.argv):
            query_params["fields"] = sys.argv[i + 1]
            i += 2
        elif arg.startswith("{") or arg.startswith("["):
            body = arg.encode("utf-8")
            i += 1
        else:
            # Treat as JSON body
            body = arg.encode("utf-8")
            i += 1

    jira_url = env("JIRA_URL")
    username = env("JIRA_USERNAME")
    token = env("JIRA_PERSONAL_TOKEN")

    url = build_url(jira_url, endpoint, query_params if query_params else None)

    credentials = base64.b64encode(f"{username}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
            if raw:
                try:
                    data = json.loads(raw)
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    print(raw)
            else:
                print(json.dumps({"status": status, "message": "OK (no body)"}))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(error_body)
        except json.JSONDecodeError:
            error_data = {"raw": error_body}
        print(json.dumps({"status": e.code, "error": error_data}, indent=2))
        sys.exit(1)
    except urllib.error.URLError as e:
        die(f"Connection error: {e.reason}")


if __name__ == "__main__":
    main()
