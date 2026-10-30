#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://localhost:8000}"
curl -sf "$BASE/api/v1/health" | grep -q ok
SID=$(curl -sf -X POST "$BASE/api/v1/sessions/sample" -H 'content-type: application/json' -d '{"sample":"students"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["session_id"])')
curl -sf "$BASE/api/v1/sessions/$SID/issues" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert len(d["items"])>=1'
curl -sf -X POST "$BASE/api/v1/sessions/$SID/proposals/apply-safe" >/dev/null
VER=$(curl -sf -X POST "$BASE/api/v1/sessions/$SID/verify")
echo "$VER" | python3 -c 'import sys,json; v=json.load(sys.stdin)["verdict"]; assert v in ("improved","clean","not_improved"), v'
BYTES=$(curl -sf "$BASE/api/v1/sessions/$SID/export/csv" | wc -c)
test "$BYTES" -gt 0
curl -sf -X DELETE "$BASE/api/v1/sessions/$SID" -o /dev/null -w "%{http_code}" | grep -q 204
echo "smoke ok"
