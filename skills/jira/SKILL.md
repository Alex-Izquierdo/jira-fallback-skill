---
name: Jira REST API
description: >
  This skill provides a Python-based interface to the Jira Cloud REST API v3 for explicit
  invocation only. It is not triggered by general Jira questions or context — it applies
  exclusively when the /jira-fallback:jira slash command is run, or when the user explicitly
  instructs to use this skill by name. It executes issue CRUD, JQL search, transitions,
  comments, boards, and sprint operations against a Jira instance configured via environment
  variables.
version: 0.2.0
argument-hint: "<action> [args] — e.g. 'get issue FOO-123' or 'search JQL=\"project=FOO AND status=Open\"'"
allowed-tools:
  - Bash
---

# Jira REST API Skill

Interact with Jira Cloud via the official REST API v3 using a Python helper script. All
requests are made through `${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py`, which reads credentials from environment
variables — no shell variable expansion is needed in commands.

**Source of truth for all API details:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/

---

## Prerequisites

Three environment variables must be set before using any command:

| Variable | Description | Example |
|---|---|---|
| `JIRA_URL` | Base URL of the Jira instance | `https://mycompany.atlassian.net` |
| `JIRA_USERNAME` | Atlassian account email | `you@example.com` |
| `JIRA_PERSONAL_TOKEN` | Atlassian API token | `sometoken…` |

See `references/authentication.md` for how to generate a token and verify the setup.

---

## How to Run Commands

Use the Python script at `${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py` for all API calls:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py METHOD ENDPOINT [JSON_BODY]
```

The script handles authentication, JSON formatting, URL encoding, and error reporting
internally. Output is always pretty-printed JSON.

### GET requests

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py GET /rest/api/3/myself
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py GET /rest/api/3/issue/FOO-123
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py GET /rest/api/3/issue/FOO-123 --fields summary,status,assignee
```

### JQL search

Use the `search` subcommand — it uses `POST /rest/api/3/search/jql` (the current API) and
handles encoding automatically:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py search 'project=FOO AND status=Open' --max-results 20
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py search 'assignee=currentUser() AND resolution=Unresolved' --max-results 50
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py search 'parent = ANSTRAT-1899' --fields summary,issuetype,status
```

For pagination, use the `nextPageToken` from the response with `--next-page`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py search 'project=FOO' --max-results 20 --next-page 'TOKEN_FROM_PREVIOUS_RESPONSE'
```

**Note:** The old `GET /rest/api/3/search` endpoint is deprecated (returns 410). Always use the `search` subcommand instead.

### POST / PUT / DELETE

Pass the JSON body as the third argument:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py POST /rest/api/3/issue '{"fields": {"project": {"key": "FOO"}, "summary": "New bug", "issuetype": {"name": "Bug"}, "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Description here."}]}]}}}'

python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py PUT /rest/api/3/issue/FOO-123 '{"fields": {"summary": "Updated summary"}}'

python3 ${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py DELETE /rest/api/3/issue/FOO-123
```

---

## Supported Operations

### Issues

| Action | Method | Endpoint |
|---|---|---|
| Get issue | GET | `/rest/api/3/issue/{key}` |
| Create issue | POST | `/rest/api/3/issue` |
| Update issue | PUT | `/rest/api/3/issue/{key}` |
| Delete issue | DELETE | `/rest/api/3/issue/{key}` |
| Get transitions | GET | `/rest/api/3/issue/{key}/transitions` |
| Transition issue | POST | `/rest/api/3/issue/{key}/transitions` (requires ID from GET transitions) |
| Assign issue | PUT | `/rest/api/3/issue/{key}/assignee` |

### Comments

| Action | Method | Endpoint |
|---|---|---|
| List comments | GET | `/rest/api/3/issue/{key}/comment` |
| Add comment | POST | `/rest/api/3/issue/{key}/comment` |

### Search

| Action | Method | Endpoint |
|---|---|---|
| JQL search | `search` subcommand | `POST /rest/api/3/search/jql` (use `search 'JQL' --max-results N`) |

### Projects

| Action | Method | Endpoint |
|---|---|---|
| List projects | GET | `/rest/api/3/project` |
| Get project | GET | `/rest/api/3/project/{key}` |

### Agile (boards / sprints)

| Action | Method | Endpoint |
|---|---|---|
| List boards | GET | `/rest/agile/1.0/board` |
| List sprints | GET | `/rest/agile/1.0/board/{boardId}/sprint` |
| Get sprint issues | GET | `/rest/agile/1.0/sprint/{sprintId}/issue` |

### Metadata

| Action | Method | Endpoint |
|---|---|---|
| Get current user | GET | `/rest/api/3/myself` |
| List issue types | GET | `/rest/api/3/issuetype` |
| List statuses | GET | `/rest/api/3/status` |
| List priorities | GET | `/rest/api/3/priority` |
| Get create metadata | GET | `/rest/api/3/issue/createmeta` |

Full curl examples for every operation are in `references/api-operations.md`.

---

## Important Notes

- **ADF format**: Always wrap `description` and `comment` body text in Atlassian Document Format (ADF) — Jira REST API v3 rejects plain strings for rich-text fields. Use the ADF structure shown in the POST example above.
- **JQL search**: Always use the `search` subcommand for JQL queries — it uses the current `POST /rest/api/3/search/jql` API. The old `GET /rest/api/3/search` endpoint is deprecated and returns 410.
- **Pagination**: The new search API uses cursor-based pagination. Use `--max-results` to set page size (default 50). For the next page, pass the `nextPageToken` from the response via `--next-page`. Check `isLast` to know when to stop.
- **Cross-project hierarchy**: Issues can have parents in other projects. When creating an Epic under a Feature from another project, set `project` to the Epic's project and `parent.key` to the parent issue key.
- **HTTP errors**: On any `4xx` response, the script prints the full error JSON including `errorMessages` to help diagnose authentication, permission, or payload failures.

---

## JQL Reference

See `references/jql-reference.md` for JQL syntax, common fields, operators, and example queries.

---

## Additional Resources

- **`${CLAUDE_PLUGIN_ROOT}/skills/jira/scripts/jira-api.py`** — The Python API client used for all operations
- **`references/authentication.md`** — Token generation, env var setup, auth verification
- **`references/api-operations.md`** — Complete curl examples for every supported operation
- **`references/jql-reference.md`** — JQL syntax guide and query examples
- **Atlassian REST API v3 docs** — https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
