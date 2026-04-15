#!/usr/bin/env bash
# jira-fallback smoke tests — READ-ONLY operations
# -------------------------------------------------------
# Usage: ./tests/smoke-tests.sh
#
# Required env vars:
#   JIRA_URL            https://yourcompany.atlassian.net
#   JIRA_USERNAME       your.email@example.com
#   JIRA_PERSONAL_TOKEN your-api-token
#
# Optional:
#   JIRA_TEST_ISSUE     A known issue key to fetch (e.g. FOO-1)
#                       If unset, the issue test is skipped.
#   JIRA_TEST_PROJECT   A known project key (e.g. FOO)
#                       If unset, the project test uses the first project found.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; SKIP=$((SKIP + 1)); }
header() { echo -e "\n--- $1 ---"; }

# -------------------------------------------------------
# Preflight checks
# -------------------------------------------------------
header "Preflight"

MISSING=()
[[ -z "${JIRA_URL:-}" ]]             && MISSING+=("JIRA_URL")
[[ -z "${JIRA_USERNAME:-}" ]]        && MISSING+=("JIRA_USERNAME")
[[ -z "${JIRA_PERSONAL_TOKEN:-}" ]]  && MISSING+=("JIRA_PERSONAL_TOKEN")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo -e "${RED}Missing required environment variables: ${MISSING[*]}${NC}"
  echo "Set them and re-run:  export JIRA_URL=... JIRA_USERNAME=... JIRA_PERSONAL_TOKEN=..."
  exit 1
fi

echo "JIRA_URL      = $JIRA_URL"
echo "JIRA_USERNAME = $JIRA_USERNAME"
echo "JIRA_PERSONAL_TOKEN = ${JIRA_PERSONAL_TOKEN:0:8}..."

# Helper: perform a GET and return body + status code
jira_get() {
  local endpoint="$1"
  curl -s -o /tmp/jira_smoke_body.json -w "%{http_code}" \
    -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
    -H "Accept: application/json" \
    "${JIRA_URL}${endpoint}"
}

# -------------------------------------------------------
# Test 1: Get current user (myself)
# -------------------------------------------------------
header "Test 1: Get current user"

STATUS=$(jira_get "/rest/api/3/myself")
if [[ "$STATUS" == "200" ]]; then
  DISPLAY=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(d.get('displayName','?'))" 2>/dev/null || echo "?")
  pass "GET /rest/api/3/myself → 200 (displayName: $DISPLAY)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "GET /rest/api/3/myself → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 2: List projects
# -------------------------------------------------------
header "Test 2: List projects"

STATUS=$(jira_get "/rest/api/3/project/search?maxResults=5")
if [[ "$STATUS" == "200" ]]; then
  COUNT=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(d.get('total', len(d.get('values',[]))))" 2>/dev/null || echo "?")
  pass "GET /rest/api/3/project/search?maxResults=5 → 200 ($COUNT projects found)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "GET /rest/api/3/project/search?maxResults=5 → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 3: List issue types
# -------------------------------------------------------
header "Test 3: List issue types"

STATUS=$(jira_get "/rest/api/3/issuetype")
if [[ "$STATUS" == "200" ]]; then
  COUNT=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(len(d))" 2>/dev/null || echo "?")
  pass "GET /rest/api/3/issuetype → 200 ($COUNT issue types)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "GET /rest/api/3/issuetype → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 4: List priorities
# -------------------------------------------------------
header "Test 4: List priorities"

STATUS=$(jira_get "/rest/api/3/priority")
if [[ "$STATUS" == "200" ]]; then
  COUNT=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(len(d))" 2>/dev/null || echo "?")
  pass "GET /rest/api/3/priority → 200 ($COUNT priorities)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "GET /rest/api/3/priority → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 5: Search issues with JQL (POST /rest/api/3/search/jql)
# -------------------------------------------------------
header "Test 5: Search issues (JQL)"

STATUS=$(curl -s -o /tmp/jira_smoke_body.json -w "%{http_code}" \
  -X POST \
  -u "$JIRA_USERNAME:$JIRA_PERSONAL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jql": "assignee = currentUser() ORDER BY created DESC", "maxResults": 5, "fields": ["summary", "status"]}' \
  "${JIRA_URL}/rest/api/3/search/jql")
if [[ "$STATUS" == "200" ]]; then
  TOTAL=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(d.get('total','?'))" 2>/dev/null || echo "?")
  pass "POST /rest/api/3/search/jql → 200 (total: $TOTAL issues)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "POST /rest/api/3/search/jql → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 6: Get specific issue (optional)
# -------------------------------------------------------
header "Test 6: Get issue by key"

if [[ -n "${JIRA_TEST_ISSUE:-}" ]]; then
  STATUS=$(jira_get "/rest/api/3/issue/${JIRA_TEST_ISSUE}?fields=summary,status")
  if [[ "$STATUS" == "200" ]]; then
    SUMMARY=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(d['fields']['summary'])" 2>/dev/null || echo "?")
    pass "GET /rest/api/3/issue/$JIRA_TEST_ISSUE → 200 (summary: $SUMMARY)"
  else
    BODY=$(cat /tmp/jira_smoke_body.json)
    fail "GET /rest/api/3/issue/$JIRA_TEST_ISSUE → $STATUS\n  $BODY"
  fi
else
  skip "JIRA_TEST_ISSUE not set — skipping single issue fetch (set it to e.g. 'FOO-1')"
fi

# -------------------------------------------------------
# Test 7: List statuses
# -------------------------------------------------------
header "Test 7: List statuses"

STATUS=$(jira_get "/rest/api/3/status")
if [[ "$STATUS" == "200" ]]; then
  COUNT=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(len(d))" 2>/dev/null || echo "?")
  pass "GET /rest/api/3/status → 200 ($COUNT statuses)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "GET /rest/api/3/status → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 8: List boards (Agile API)
# -------------------------------------------------------
header "Test 8: List boards (Agile)"

STATUS=$(jira_get "/rest/agile/1.0/board?maxResults=5")
if [[ "$STATUS" == "200" ]]; then
  COUNT=$(python3 -c "import json,sys; d=json.load(open('/tmp/jira_smoke_body.json')); print(len(d.get('values',[])))" 2>/dev/null || echo "?")
  pass "GET /rest/agile/1.0/board → 200 ($COUNT boards)"
elif [[ "$STATUS" == "404" ]]; then
  skip "GET /rest/agile/1.0/board → 404 (Agile API may not be available on this instance)"
else
  BODY=$(cat /tmp/jira_smoke_body.json)
  fail "GET /rest/agile/1.0/board → $STATUS\n  $BODY"
fi

# -------------------------------------------------------
# Test 9: jira-api.py — GET /rest/api/3/myself
# -------------------------------------------------------
header "Test 9: jira-api.py script (GET myself)"

SCRIPT_DIR="$(cd "$(dirname "$0")/../skills/jira/scripts" && pwd)"
if OUTPUT=$(python3 "$SCRIPT_DIR/jira-api.py" GET /rest/api/3/myself 2>&1); then
  DISPLAY=$(echo "$OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('displayName','?'))" 2>/dev/null || echo "?")
  pass "jira-api.py GET /rest/api/3/myself → OK (displayName: $DISPLAY)"
else
  fail "jira-api.py GET /rest/api/3/myself → FAILED\n  $OUTPUT"
fi

# -------------------------------------------------------
# Test 10: jira-api.py — search subcommand
# -------------------------------------------------------
header "Test 10: jira-api.py script (search)"

if OUTPUT=$(python3 "$SCRIPT_DIR/jira-api.py" search 'assignee = currentUser() ORDER BY created DESC' --max-results 3 --fields summary 2>&1); then
  COUNT=$(echo "$OUTPUT" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('issues',[])))" 2>/dev/null || echo "?")
  pass "jira-api.py search → OK ($COUNT issues returned)"
else
  fail "jira-api.py search → FAILED\n  $OUTPUT"
fi

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
echo ""
echo "========================================"
echo -e "Results: ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  ${YELLOW}${SKIP} skipped${NC}"
echo "========================================"

rm -f /tmp/jira_smoke_body.json

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
