# Jira Authentication Reference

## Overview

Jira Cloud REST API v3 uses HTTP Basic Authentication with an **API token** — not your account
password. The credentials are passed with every request as a base64-encoded
`username:token` pair via the `Authorization` header.

`curl` handles this automatically with the `-u` flag.

---

## Required Environment Variables

Set the following in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) or in the terminal
before invoking the skill:

```bash
export JIRA_URL="https://mycompany.atlassian.net"   # No trailing slash
export JIRA_USERNAME="you@example.com"               # Atlassian account email
export JIRA_PERSONAL_TOKEN="sometoken"              # API token (see below)
```

---

## Generating an API Token

1. Log in to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Give it a label (e.g. `claude-jira-fallback`)
4. Copy the generated token immediately — it is shown only once
5. Set it as `JIRA_PERSONAL_TOKEN`

**Scopes**: API tokens inherit the permissions of the Atlassian account they belong to.
To limit exposure, create a dedicated service account with read-only access for read-only
operations.

---

## How Authentication Works in curl

```bash
# The -u flag sends: Authorization: Basic base64("username:token")
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/myself"
```

Internally, curl computes `Authorization: Basic $(printf '%s:%s' "$JIRA_USERNAME" "$JIRA_PERSONAL_TOKEN" | base64)`.

Both forms are equivalent. The `-u` flag is preferred for brevity and avoids shell history
issues with explicit base64 values.

---

## Verifying the Setup

Run this one-liner to confirm all three variables are set and credentials are valid:

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/myself" \
  | python3 -m json.tool
```

**Expected**: JSON object with `accountId`, `displayName`, `emailAddress`.

**Common errors:**

| HTTP Status | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong username or token | Re-check `JIRA_USERNAME` and `JIRA_PERSONAL_TOKEN` |
| `403 Forbidden` | Account lacks permission | Check Jira project/global permissions |
| `404 Not Found` | Wrong `JIRA_URL` | Verify the URL (no trailing slash, correct subdomain) |
| `curl: (6) Could not resolve host` | Typo in URL or no network | Check `JIRA_URL` spelling and connectivity |

---

## Security Notes

- Never hard-code the token in scripts or commit it to version control.
- Rotate the token via https://id.atlassian.com/manage-profile/security/api-tokens
  if it is exposed.
- Use a dedicated read-only account for automated or shared workflows.
