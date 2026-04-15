# JQL (Jira Query Language) Reference

JQL is used with the `/rest/api/3/search?jql=<query>` endpoint. Always URL-encode the query
before passing it as a query parameter.

```bash
# URL-encoding helper
python3 -c "import urllib.parse; print(urllib.parse.quote('project=FOO AND status=Open'))"
```

**Full JQL documentation:** https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/

---

## Syntax

```
field operator value [AND|OR|NOT field operator value ...]
```

- Fields and operators are case-insensitive.
- String values with spaces must be quoted: `summary ~ "login bug"`.
- Keywords: `AND`, `OR`, `NOT`, `EMPTY`, `NULL`, `ORDER BY`.

---

## Common Fields

| Field | Description | Example value |
|---|---|---|
| `project` | Project key or name | `FOO`, `"My Project"` |
| `issuetype` | Issue type | `Bug`, `Story`, `Epic`, `Task` |
| `status` | Workflow status | `Open`, `"In Progress"`, `Done` |
| `assignee` | Assignee account or function | `currentUser()`, `"john.doe@co.com"`, `EMPTY` |
| `reporter` | Reporter | `currentUser()` |
| `priority` | Priority name | `High`, `Medium`, `Low` |
| `summary` | Issue summary (title) | `~ "keyword"` |
| `description` | Issue description | `~ "keyword"` |
| `labels` | Labels | `backend`, `EMPTY` |
| `fixVersion` | Fix version | `"2.0"`, `EMPTY` |
| `sprint` | Sprint name or id | `"Sprint 5"`, `openSprints()` |
| `created` | Creation date | `>= -7d`, `= "2024-01-01"` |
| `updated` | Last updated | `>= -1d` |
| `dueDate` | Due date | `<= "2024-12-31"`, `EMPTY` |
| `resolutionDate` | When resolved | `>= -30d` |
| `resolution` | Resolution | `Fixed`, `Unresolved`, `EMPTY` |
| `component` | Component name | `"Auth"` |
| `comment` | Comment text | `~ "review needed"` |
| `votes` | Number of votes | `> 0` |
| `watchers` | Number of watchers | `> 0` |
| `parent` | Parent issue key | `FOO-100` |

---

## Operators

| Operator | Meaning | Example |
|---|---|---|
| `=` | Equals | `status = Open` |
| `!=` | Not equals | `status != Done` |
| `>` | Greater than | `priority > Medium` |
| `<` | Less than | `dueDate < "2024-12-31"` |
| `>=` | Greater or equal | `created >= -7d` |
| `<=` | Less or equal | `updated <= "2024-01-01"` |
| `~` | Contains (text search) | `summary ~ "login"` |
| `!~` | Does not contain | `summary !~ "deprecated"` |
| `in` | In list | `status in (Open, "In Progress")` |
| `not in` | Not in list | `issuetype not in (Epic, Subtask)` |
| `is EMPTY` | Has no value | `assignee is EMPTY` |
| `is not EMPTY` | Has a value | `fixVersion is not EMPTY` |

---

## Functions

| Function | Returns |
|---|---|
| `currentUser()` | Logged-in user's accountId |
| `membersOf("group")` | Users in a Jira group |
| `openSprints()` | Active sprints |
| `closedSprints()` | Closed sprints |
| `futureSprints()` | Future sprints |
| `startOfDay()` | Midnight today |
| `endOfDay()` | 23:59:59 today |
| `startOfWeek()` | Start of current week |
| `startOfMonth()` | First day of current month |
| `now()` | Current datetime |

---

## Common Query Examples

```jql
# My open issues
assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC

# Bugs in project FOO, unresolved
project = FOO AND issuetype = Bug AND resolution = Unresolved

# Issues updated in the last 24 hours
updated >= -24h ORDER BY updated DESC

# High or critical priority issues due this week
priority in (High, Critical) AND dueDate <= endOfWeek()

# Issues in the current sprint
sprint in openSprints() AND project = FOO

# Issues created this month by me
project = FOO AND reporter = currentUser() AND created >= startOfMonth()

# Unassigned open issues in a project
project = FOO AND assignee is EMPTY AND status != Done

# Issues with a specific label
labels = backend AND status != Done

# Epic and its children
parent = FOO-10

# Full-text search in summary and description
summary ~ "authentication" OR description ~ "authentication"

# Recently resolved (last 7 days)
resolution = Fixed AND resolutionDate >= -7d

# Overdue issues
dueDate < now() AND resolution = Unresolved
```

---

## ORDER BY

Append `ORDER BY field [ASC|DESC]` to sort results:

```jql
project = FOO ORDER BY created DESC
project = FOO ORDER BY priority DESC, updated ASC
```

Sortable fields: `created`, `updated`, `dueDate`, `priority`, `status`, `summary`, `assignee`.

---

## Using JQL with the Script

The `search` subcommand handles encoding automatically — pass the JQL as a plain string:

```bash
python3 jira-api.py search 'project = FOO AND status in ("In Progress", "Open") ORDER BY updated DESC' --max-results 20 --fields summary,status,assignee
```

When using curl directly, use `POST /rest/api/3/search/jql` with JQL in the JSON body
(no URL encoding needed):

```bash
curl -s -X POST \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jql": "project = FOO AND status in (\"In Progress\", \"Open\") ORDER BY updated DESC", "maxResults": 20, "fields": ["summary", "status", "assignee"]}' \
  "$JIRA_URL/rest/api/3/search/jql" \
  | python3 -m json.tool
```
