---
name: jira
description: Interact with Jira Cloud REST API v3. Requires JIRA_URL, JIRA_USERNAME, and JIRA_PERSONAL_TOKEN environment variables.
argument-hint: "<action> [args] — e.g. 'get issue FOO-123', 'search JQL=\"project=FOO\"', 'create issue in FOO'"
allowed-tools:
  - Bash
---

Load and apply the `jira` skill from this plugin (skills/jira/SKILL.md) to fulfill the
user's request. Use the Python API client at `skills/jira/scripts/jira-api.py` for all
Jira REST API calls. The script reads `JIRA_URL`, `JIRA_USERNAME`, and `JIRA_PERSONAL_TOKEN`
from environment variables internally — never use shell variable expansion in commands.

Follow all guidance in the skill, including:
- Use `scripts/jira-api.py` for every API call (no inline curl)
- ADF format for rich-text fields (description, comments)
- `--jql` flag for search queries (auto-encodes)
- Pagination with `--start-at` and `--max-results`

If environment variables are missing, report which ones are unset and direct the user
to `references/authentication.md` for setup instructions.
