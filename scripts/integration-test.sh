#!/usr/bin/env bash
# Integration test script for forex-mtl.
# Starts the full stack with docker-compose.it.yml, runs smoke tests, then tears down.
set -euo pipefail

COMPOSE_FILE="docker-compose.it.yml"
BASE_URL="http://localhost:9090"
TOKEN="10dc303535874aeccc86a8251e6992f5"

echo "==> Building and starting services..."
docker compose -f "$COMPOSE_FILE" up --build -d

echo "==> Waiting for forex-proxy to become healthy..."
for i in $(seq 1 24); do
  STATUS=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null \
    | python3 -c "import sys,json; [print(s['Health']) for s in json.load(sys.stdin) if s['Service']=='forex-proxy']" 2>/dev/null || true)
  if [[ "$STATUS" == "healthy" ]]; then
    echo "forex-proxy is healthy"
    break
  fi
  echo "  attempt $i/24 — waiting 5s..."
  sleep 5
done

PROXY_TOKEN="10dc303535874aeccc86a8251e699999"
FAIL=0

run_test() {
  local desc="$1"
  local url="$2"
  local expected_status="$3"
  local actual_status
  actual_status=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Proxy-Token: $PROXY_TOKEN" "$url")
  if [[ "$actual_status" == "$expected_status" ]]; then
    echo "  PASS: $desc (HTTP $actual_status)"
  else
    echo "  FAIL: $desc — expected HTTP $expected_status, got $actual_status"
    FAIL=1
  fi
}

echo ""
echo "==> Running integration tests..."

# Auth endpoints (public — no token needed)
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@paidy.com","password":"forex2025"}')
SESSION_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null || true)

if [[ -n "$SESSION_TOKEN" ]]; then
  echo "  PASS: POST /auth/login returns token"
else
  echo "  FAIL: POST /auth/login — no token in response: $LOGIN_RESPONSE"
  FAIL=1
fi

VALIDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/auth/validate" \
  -H "Authorization: Bearer $SESSION_TOKEN")
if [[ "$VALIDATE_STATUS" == "200" ]]; then
  echo "  PASS: GET /auth/validate with valid token returns 200"
else
  echo "  FAIL: GET /auth/validate — expected 200, got $VALIDATE_STATUS"
  FAIL=1
fi

BAD_LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"user@paidy.com","password":"wrongpassword"}')
if [[ "$BAD_LOGIN_STATUS" == "401" ]]; then
  echo "  PASS: POST /auth/login with wrong password returns 401"
else
  echo "  FAIL: POST /auth/login bad creds — expected 401, got $BAD_LOGIN_STATUS"
  FAIL=1
fi

# Rates endpoints (X-Proxy-Token required)
run_test "USD to JPY returns 200"               "$BASE_URL/rates?from=USD&to=JPY" "200"
run_test "EUR to GBP returns 200"               "$BASE_URL/rates?from=EUR&to=GBP" "200"
run_test "invalid currency returns 400"         "$BASE_URL/rates?from=XYZ&to=JPY" "400"
run_test "missing from param returns 400"       "$BASE_URL/rates?to=JPY"          "400"
run_test "missing to param returns 400"         "$BASE_URL/rates?from=USD"         "400"
run_test "same currency (USD->USD) returns 400" "$BASE_URL/rates?from=USD&to=USD" "400"
# Verify /rates without token returns 401
UNAUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/rates?from=USD&to=JPY")
if [[ "$UNAUTH_STATUS" == "401" ]]; then
  echo "  PASS: /rates without X-Proxy-Token returns 401"
else
  echo "  FAIL: /rates without token — expected 401, got $UNAUTH_STATUS"
  FAIL=1
fi

echo ""
echo "==> Response body for USD/JPY:"
curl -s -H "X-Proxy-Token: $PROXY_TOKEN" "$BASE_URL/rates?from=USD&to=JPY" | python3 -m json.tool || true

echo ""
echo "==> Tearing down services..."
docker compose -f "$COMPOSE_FILE" down -v

if [[ "$FAIL" -eq 0 ]]; then
  echo ""
  echo "All integration tests passed."
  exit 0
else
  echo ""
  echo "One or more integration tests FAILED."
  exit 1
fi
