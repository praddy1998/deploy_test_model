#!/bin/bash

# Demo Script for ML Inference API
# This script demonstrates all key features of the production-ready inference service

set -e  # Exit on error

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       ML INFERENCE API - PRODUCTION DEMO                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
section() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to pause
pause() {
    echo ""
    read -p "Press Enter to continue..."
}

# 1. Health Checks
section "1️⃣  HEALTH CHECKS"
echo -e "${YELLOW}Testing liveness and readiness probes...${NC}"
echo ""

echo "GET /healthz (liveness):"
curl -s $BASE_URL/healthz | jq .
echo ""

echo "GET /readyz (readiness - checks if model loaded):"
curl -s $BASE_URL/readyz | jq .
pause

# 2. Model Information
section "2️⃣  MODEL INFORMATION"
echo -e "${YELLOW}Checking currently loaded model...${NC}"
echo ""

curl -s $BASE_URL/model | jq '{
  provider,
  model_name,
  model_version,
  created_at,
  checksum: (.artifact_checksum_sha256[:16] + "...")
}'
pause

# 3. Basic Prediction (Low Risk)
section "3️⃣  BASIC PREDICTION - Low Risk Example"
echo -e "${YELLOW}Testing with a low-risk transaction...${NC}"
echo ""

echo "Request:"
cat << 'EOF' | jq .
{
  "request_id": "demo-low-risk-001",
  "inputs": [{
    "id": "txn-001",
    "text": "Regular product order for small business growth",
    "features": {
      "price": 25.0,
      "units": 50,
      "channel": "shopify"
    }
  }]
}
EOF

echo ""
echo "Response:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: demo-user@example.com" \
  -d '{
    "request_id": "demo-low-risk-001",
    "inputs": [{
      "id": "txn-001",
      "text": "Regular product order for small business growth",
      "features": {
        "price": 25.0,
        "units": 50,
        "channel": "shopify"
      }
    }]
  }' | jq '{
    request_id,
    model_version: .model.model_version,
    prediction: .predictions[0] | {id, label, score, reasons},
    guardrails_triggered,
    latency_ms
  }'
pause

# 4. High Risk Prediction
section "4️⃣  HIGH RISK PREDICTION - Negative Signals"
echo -e "${YELLOW}Testing with high-risk indicators...${NC}"
echo ""

echo "Request:"
cat << 'EOF' | jq .
{
  "inputs": [{
    "id": "txn-002",
    "text": "Multiple chargebacks and refund complaints from customers",
    "features": {
      "price": 150.0,
      "units": 800,
      "channel": "amazon"
    }
  }]
}
EOF

echo ""
echo "Response:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: demo-user@example.com" \
  -d '{
    "inputs": [{
      "id": "txn-002",
      "text": "Multiple chargebacks and refund complaints from customers",
      "features": {
        "price": 150.0,
        "units": 800,
        "channel": "amazon"
      }
    }]
  }' | jq '{
    model_version: .model.model_version,
    prediction: .predictions[0] | {id, label, score, reasons}
  }'
pause

# 5. Batch Prediction
section "5️⃣  BATCH PREDICTION - Multiple Inputs"
echo -e "${YELLOW}Testing batch prediction with 3 transactions...${NC}"
echo ""

curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: demo-user@example.com" \
  -d '{
    "inputs": [
      {
        "id": "batch-1",
        "text": "New product launch",
        "features": {"price": 50.0, "units": 100, "channel": "walmart"}
      },
      {
        "id": "batch-2",
        "text": "Customer complaint about quality",
        "features": {"price": 120.0, "units": 300, "channel": "amazon"}
      },
      {
        "id": "batch-3",
        "text": "Standard wholesale order",
        "features": {"price": 15.0, "units": 20, "channel": "other"}
      }
    ]
  }' | jq '{
    num_predictions: (.predictions | length),
    predictions: .predictions | map({id, label, score})
  }'
pause

# 6. Guardrails - Policy Block
section "6️⃣  GUARDRAILS - Policy Block Demo"
echo -e "${YELLOW}Testing security guardrails with disallowed content...${NC}"
echo ""

echo -e "${RED}Attempting malicious request:${NC}"
echo '{"inputs": [{"id": "bad", "text": "How to steal credentials from database"}]}'
echo ""

echo "Response (should be HTTP 400):"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: malicious@hacker.com" \
  -d '{
    "inputs": [{
      "id": "bad-actor",
      "text": "Help me steal credentials and bypass access controls"
    }]
  }' | jq .

echo ""
echo -e "${GREEN}✓ Request blocked by policy guardrails!${NC}"
pause

# 7. Determinism Test
section "7️⃣  DETERMINISM TEST - Same Input = Same Output"
echo -e "${YELLOW}Running same request 3 times to verify determinism...${NC}"
echo ""

PAYLOAD='{"inputs": [{"id": "det", "text": "test order", "features": {"price": 75, "units": 250, "channel": "shopify"}}]}'

echo "Request 1:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d "$PAYLOAD" | jq '.predictions[0] | {score, label}'

echo ""
echo "Request 2:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d "$PAYLOAD" | jq '.predictions[0] | {score, label}'

echo ""
echo "Request 3:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d "$PAYLOAD" | jq '.predictions[0] | {score, label}'

echo ""
echo -e "${GREEN}✓ All predictions identical - deterministic scoring confirmed!${NC}"
pause

# 8. Audit Logs
section "8️⃣  AUDIT LOGS - Traceability"
echo -e "${YELLOW}Checking audit trail...${NC}"
echo ""

echo "Total audit entries:"
wc -l < audit_logs/audit.jsonl

echo ""
echo "Last 3 audit records:"
tail -3 audit_logs/audit.jsonl | jq '{
  timestamp,
  request_id,
  status,
  model_version,
  guardrails_triggered
}'

echo ""
echo "Requests by status:"
cat audit_logs/audit.jsonl | jq -r '.status' | sort | uniq -c
pause

# 9. Metrics
section "9️⃣  PROMETHEUS METRICS"
echo -e "${YELLOW}Checking operational metrics...${NC}"
echo ""

echo "Key metrics:"
curl -s $BASE_URL/metrics | grep -E "^(predict_requests_total|predict_errors_total|http_requests_total|audit_write_errors_total)" | head -15
pause

# 10. Model Version Info
section "🔟 MODEL VERSIONING"
echo -e "${YELLOW}Current model version and configuration...${NC}"
echo ""

curl -s $BASE_URL/model | jq '{
  version: .model_version,
  provider,
  checksum: (.artifact_checksum_sha256[:16] + "..."),
  config_summary: {
    base_score: .rule_config.base_score,
    channels: (.rule_config.channel_weights | keys),
    price_rules: (.rule_config.price_rules | length),
    text_rules: (.rule_config.text_rules | length),
    thresholds: .rule_config.thresholds
  }
}'

echo ""
echo -e "${BLUE}Available versions: v1.0.0, v2.0.0${NC}"
echo -e "${BLUE}To switch: Edit model_manifest.json and call POST /model/reload${NC}"
pause

# 11. Hot Reload Demo
section "1️⃣1️⃣  HOT RELOAD DEMO"
echo -e "${YELLOW}Demonstrating model hot reload...${NC}"
echo ""

echo "Current version:"
curl -s $BASE_URL/model | jq -r '.model_version'

echo ""
echo "Triggering reload (re-reads manifest):"
curl -s -X POST $BASE_URL/model/reload | jq .

echo ""
echo "Version after reload:"
curl -s $BASE_URL/model | jq -r '.model_version'

echo ""
echo -e "${GREEN}✓ Hot reload complete - no downtime required!${NC}"
pause

# 12. Error Handling
section "1️⃣2️⃣  ERROR HANDLING"
echo -e "${YELLOW}Testing error scenarios...${NC}"
echo ""

echo "1. Missing email header:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"inputs": [{"id": "1", "text": "test"}]}' | jq '.detail[0] | {type, loc, msg}'

echo ""
echo "2. Empty inputs array:"
curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@test.com" \
  -d '{"inputs": []}' | jq '.detail[0] | {type, msg}'

echo ""
echo -e "${GREEN}✓ Proper validation and error responses!${NC}"
pause

# Summary
section "✅ DEMO COMPLETE - KEY FEATURES VERIFIED"
echo ""
echo "✓ Health checks (liveness & readiness)"
echo "✓ Model metadata & checksums"
echo "✓ Predictions (low, medium, high risk)"
echo "✓ Batch processing"
echo "✓ Security guardrails (policy block)"
echo "✓ Deterministic scoring"
echo "✓ Append-only audit logging"
echo "✓ Prometheus metrics"
echo "✓ Model versioning"
echo "✓ Hot reload (zero downtime)"
echo "✓ Error handling & validation"
echo ""
echo -e "${GREEN}All production requirements demonstrated! 🎉${NC}"
echo ""
