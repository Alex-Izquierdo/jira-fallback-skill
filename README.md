# jira-fallback

A Claude Code plugin that provides a skill for interacting with **Jira Cloud REST API v3**
via a Python helper script — a lightweight fallback for when the Jira MCP is unavailable.

**API reference:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/

---

## Features

- Get, create, update, and delete issues
- Search issues with JQL (uses `POST /rest/api/3/search/jql` with cursor-based pagination)
- List projects, boards, sprints, priorities, statuses, and issue types
- Add and list comments
- Transition issues through workflow states
- Single Python script — no external dependencies beyond `python3`

---

## Prerequisites

- Claude Code installed
- `python3` available in `$PATH`
- An Atlassian account with API token access

---

## Installation

### From the repository

```bash
# Clone the plugin
git clone https://github.com/alex/jira-fallback-skill ~/.claude/plugins/jira-fallback

# Enable in Claude Code
claude plugin enable ~/.claude/plugins/jira-fallback
```

### Test locally without installing

```bash
claude --plugin-dir /path/to/jira-fallback
```

---

## Configuration

Set the following environment variables before starting Claude Code:

```bash
export JIRA_URL="https://yourcompany.atlassian.net"   # No trailing slash
export JIRA_USERNAME="you@example.com"                 # Atlassian account email
export JIRA_PERSONAL_TOKEN="ATATT3x..."                # API token (see below)
```

Add them to `~/.bashrc`, `~/.zshrc`, or your preferred shell profile to persist across sessions.

### Generating an API token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Give it a descriptive label (e.g. `claude-jira-fallback`)
4. Copy the token — it is shown only once
5. Set it as `JIRA_PERSONAL_TOKEN`

### Permissions

The plugin ships with a `.claude/settings.json` that pre-approves the specific
script that needs to run:

```json
{
  "permissions": {
    "allow": ["Bash(python3 */skills/jira/scripts/jira-api.py *)"]
  }
}
```

This scopes the permission to only the Jira API script — no other Python
commands are auto-approved.

---

## Usage

The skill is **not auto-triggered**. Invoke it explicitly:

**Via slash command:**
```
/jira-fallback:jira get issue FOO-123
/jira-fallback:jira search JQL="project=FOO AND status=Open"
/jira-fallback:jira create issue in project FOO
```

**Via prompt instruction:**
```
Use the jira skill to find all open bugs in project FOO assigned to me.
Use jira-fallback to create a bug report for the login issue.
```

---

## Running the tests

### Unit tests (offline)

```bash
python3 -m pytest tests/test_jira_api.py -v
```

26 tests covering URL building, argument parsing, search subcommand, auth
headers, and error handling — no network calls required.

### Smoke tests (live)

Read-only operations against a live Jira instance:

```bash
# Required
export JIRA_URL="https://yourcompany.atlassian.net"
export JIRA_USERNAME="you@example.com"
export JIRA_PERSONAL_TOKEN="ATATT3x..."

# Optional: set a known issue key to test single-issue fetching
export JIRA_TEST_ISSUE="FOO-1"

# Run
./tests/smoke-tests.sh
```

| # | Test | Method |
|---|---|---|
| 1 | Get current user | `GET /rest/api/3/myself` |
| 2 | List projects | `GET /rest/api/3/project/search` |
| 3 | List issue types | `GET /rest/api/3/issuetype` |
| 4 | List priorities | `GET /rest/api/3/priority` |
| 5 | Search issues (JQL) | `POST /rest/api/3/search/jql` |
| 6 | Get issue by key (optional) | `GET /rest/api/3/issue/{key}` |
| 7 | List statuses | `GET /rest/api/3/status` |
| 8 | List boards (Agile) | `GET /rest/agile/1.0/board` |
| 9 | jira-api.py GET | `scripts/jira-api.py GET` |
| 10 | jira-api.py search | `scripts/jira-api.py search` |

---

## Project structure

```
jira-fallback/
├── .claude-plugin/
│   └── plugin.json                     # Plugin manifest
├── .claude/
│   └── settings.json                   # Auto-approved permissions
├── skills/
│   └── jira/
│       ├── SKILL.md                    # Skill definition
│       ├── scripts/
│       │   └── jira-api.py            # Python API client
│       └── references/
│           ├── authentication.md       # Token setup, auth details
│           ├── api-operations.md       # Curl examples for all operations
│           └── jql-reference.md        # JQL syntax and query examples
├── commands/
│   └── jira.md                         # /jira-fallback:jira slash command
├── tests/
│   ├── test_jira_api.py               # Unit tests (offline, 26 tests)
│   └── smoke-tests.sh                 # Live smoke tests (10 tests)
└── README.md
```

---

## License

MIT
