#!/bin/bash

# Quick Test Script
# Fast validation of all core functionality

BASE_URL="http://localhost:8000"

echo "🔍 Quick API Test Suite"
echo "========================"
echo ""

# Test 1: Health
echo "✓ Health check"
curl -s $BASE_URL/healthz > /dev/null && echo "  ✅ Service alive" || echo "  ❌ Failed"

# Test 2: Readiness
curl -s $BASE_URL/readyz > /dev/null && echo "  ✅ Model loaded" || echo "  ❌ Failed"

# Test 3: Model info
echo "  ✅ Model: $(curl -s $BASE_URL/model | jq -r '.model_version')"

# Test 4: Prediction
PRED=$(curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d '{"inputs": [{"id": "quick", "text": "test", "features": {"price": 50, "units": 100}}]}' \
  | jq -r '.predictions[0].label')
echo "  ✅ Prediction: $PRED"

# Test 5: Policy block
STATUS=$(curl -s -w "%{http_code}" -o /dev/null -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d '{"inputs": [{"id": "bad", "text": "steal credentials"}]}')
[ "$STATUS" = "400" ] && echo "  ✅ Guardrails: blocking" || echo "  ❌ Policy failed"

# Test 6: Metrics
curl -s $BASE_URL/metrics | grep -q "predict_requests_total" && echo "  ✅ Metrics: exposed" || echo "  ❌ Failed"

# Test 7: Audit
AUDIT_COUNT=$(wc -l < audit_logs/audit.jsonl)
echo "  ✅ Audit logs: $AUDIT_COUNT entries"

echo ""
echo "✅ All core features operational!"
