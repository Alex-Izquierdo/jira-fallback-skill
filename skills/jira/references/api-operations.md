# Jira REST API v3 — curl Operations Reference

All examples assume:

```bash
export JIRA_URL="https://mycompany.atlassian.net"
export JIRA_USERNAME="you@example.com"
export JIRA_PERSONAL_TOKEN="sometoken..."
```

Pipe output through `| python3 -m json.tool` or `| jq .` for readable JSON.

**Official docs:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/

---

## Current User

### Get current user (myself)

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/myself" \
  | python3 -m json.tool
```

Returns: `accountId`, `displayName`, `emailAddress`, timezone, locale.

---

## Issues

### Get issue by key

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/FOO-123" \
  | python3 -m json.tool
```

**Select specific fields** (reduces payload size):

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/FOO-123?fields=summary,status,assignee,priority" \
  | python3 -m json.tool
```

---

### Create issue

Jira v3 uses **Atlassian Document Format (ADF)** for rich-text fields (`description`, `comment`).

```bash
curl -s -X POST \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "fields": {
      "project": {"key": "FOO"},
      "summary": "Something is broken",
      "issuetype": {"name": "Bug"},
      "priority": {"name": "Medium"},
      "description": {
        "type": "doc",
        "version": 1,
        "content": [
          {
            "type": "paragraph",
            "content": [
              {"type": "text", "text": "Steps to reproduce: ..."}
            ]
          }
        ]
      }
    }
  }' \
  "$JIRA_URL/rest/api/3/issue" \
  | python3 -m json.tool
```

Returns: `{"id": "10234", "key": "FOO-124", "self": "..."}`.

**To get valid `issuetype` names for a project:**

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/createmeta?projectKeys=FOO&expand=projects.issuetypes.fields" \
  | python3 -m json.tool
```

---

### Update issue

Only include the fields you want to change:

```bash
curl -s -X PUT \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "fields": {
      "summary": "Updated summary",
      "priority": {"name": "High"}
    }
  }' \
  "$JIRA_URL/rest/api/3/issue/FOO-123" \
  | python3 -m json.tool
```

Returns HTTP 204 on success (no body).

---

### Delete issue

```bash
curl -s -X DELETE \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  "$JIRA_URL/rest/api/3/issue/FOO-123"
```

Returns HTTP 204 on success. Add `?deleteSubtasks=true` to also delete subtasks.

---

### Get available transitions

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/FOO-123/transitions" \
  | python3 -m json.tool
```

Returns an array of transitions, each with an `id` and `name` (e.g., "In Progress", "Done").

---

### Transition issue (change status)

```bash
# First get the transition ID from the previous call, then:
curl -s -X POST \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"transition": {"id": "31"}}' \
  "$JIRA_URL/rest/api/3/issue/FOO-123/transitions" \
  | python3 -m json.tool
```

Returns HTTP 204 on success.

---

### Assign issue

```bash
# Assign to a specific user (use their accountId)
curl -s -X PUT \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"accountId": "5b10ac8d82e05b22cc7d4ef5"}' \
  "$JIRA_URL/rest/api/3/issue/FOO-123/assignee"

# Unassign
curl -s -X PUT \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"accountId": null}' \
  "$JIRA_URL/rest/api/3/issue/FOO-123/assignee"
```

---

## Comments

### List comments on an issue

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/FOO-123/comment" \
  | python3 -m json.tool
```

---

### Add a comment

```bash
curl -s -X POST \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "body": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {"type": "text", "text": "This is a comment."}
          ]
        }
      ]
    }
  }' \
  "$JIRA_URL/rest/api/3/issue/FOO-123/comment" \
  | python3 -m json.tool
```

---

## Search

### Search with JQL (new API)

**Important:** The old `GET /rest/api/3/search` endpoint is deprecated and returns HTTP 410.
Use `POST /rest/api/3/search/jql` instead. The `jira-api.py` script provides a `search`
subcommand that handles this automatically.

**Using the script (recommended):**

```bash
python3 jira-api.py search 'project=FOO AND status=Open AND assignee=currentUser()' --max-results 50 --fields summary,status,assignee,priority
```

**Using curl directly:**

```bash
curl -s -X POST \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jql": "project=FOO AND status=Open AND assignee=currentUser()",
    "maxResults": 50,
    "startAt": 0,
    "fields": ["summary", "status", "assignee", "priority"]
  }' \
  "$JIRA_URL/rest/api/3/search/jql" \
  | python3 -m json.tool
```

**Pagination:**

```bash
python3 jira-api.py search 'project=FOO' --start-at 50 --max-results 50
```

Response includes `total`, `startAt`, `maxResults` for pagination control.

---

## Projects

### List all projects

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/project" \
  | python3 -m json.tool
```

### Get a specific project

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/project/FOO" \
  | python3 -m json.tool
```

---

## Boards and Sprints (Agile API)

These endpoints use `/rest/agile/1.0/` — not `/rest/api/3/`.

### List all boards

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/agile/1.0/board" \
  | python3 -m json.tool
```

Filter by project key: `?projectKeyOrId=FOO`

### List sprints for a board

```bash
BOARD_ID=12
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/agile/1.0/board/${BOARD_ID}/sprint" \
  | python3 -m json.tool
```

Filter by state: `?state=active` or `?state=future` or `?state=closed`

### Get issues in a sprint

```bash
SPRINT_ID=42
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/agile/1.0/sprint/${SPRINT_ID}/issue?fields=summary,status,assignee" \
  | python3 -m json.tool
```

---

## Metadata

### List issue types

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issuetype" \
  | python3 -m json.tool
```

### List statuses

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/status" \
  | python3 -m json.tool
```

### List priorities

```bash
curl -s \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/priority" \
  | python3 -m json.tool
```

---

## Error Handling

All Jira API errors return JSON with `errorMessages` and/or `errors` fields:

```json
{
  "errorMessages": ["Issue does not exist or you do not have permission to see it."],
  "errors": {}
}
```

To capture HTTP status code alongside the body:

```bash
curl -s -o /tmp/jira_response.json -w "%{http_code}" \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/issue/FOO-999"
# Prints the HTTP code; body is in /tmp/jira_response.json
```
