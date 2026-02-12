#!/bin/bash

# Model Rollback Demo Script
# Demonstrates switching between model versions v1.0.0 and v2.0.0

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       MODEL ROLLBACK DEMONSTRATION                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test payload - edge case where v1 and v2 differ
TEST_PAYLOAD='{
  "inputs": [{
    "id": "edge-case",
    "text": "refund chargeback issue problem",
    "features": {
      "price": 101.0,
      "units": 400,
      "channel": "amazon"
    }
  }]
}'

echo -e "${YELLOW}Test case:${NC} Transaction with price=$101 (threshold boundary)"
echo ""

# Current version
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}STEP 1: Check Current Model Version${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
CURRENT_VERSION=$(curl -s $BASE_URL/model | jq -r '.model_version')
echo "Current version: ${CURRENT_VERSION}"
echo ""

# Get prediction with current version
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}STEP 2: Prediction with Current Version${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
RESULT_BEFORE=$(curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: rollback-demo@example.com" \
  -d "$TEST_PAYLOAD")

echo "$RESULT_BEFORE" | jq '{
  model_version: .model.model_version,
  prediction: .predictions[0] | {
    label,
    score,
    reasons: (.reasons[:3])
  }
}'
echo ""
read -p "Press Enter to switch model version..."

# Switch version
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}STEP 3: Switch Model Version${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ "$CURRENT_VERSION" = "2.0.0" ]; then
    TARGET_VERSION="1.0.0"
    echo "Switching from v2.0.0 → v1.0.0"
else
    TARGET_VERSION="2.0.0"
    echo "Switching from v1.0.0 → v2.0.0"
fi

echo ""
echo "Updating manifest..."
jq --arg ver "$TARGET_VERSION" '.active_model_version = $ver' model_artifacts/model_manifest.json > /tmp/manifest.json
mv /tmp/manifest.json model_artifacts/model_manifest.json

echo "Triggering hot reload..."
curl -s -X POST $BASE_URL/model/reload | jq .
echo ""

NEW_VERSION=$(curl -s $BASE_URL/model | jq -r '.model_version')
echo -e "${GREEN}✓ Model reloaded: ${NEW_VERSION}${NC}"
echo ""
read -p "Press Enter to test with new version..."

# Get prediction with new version
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}STEP 4: Prediction with New Version${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
RESULT_AFTER=$(curl -s -X POST $BASE_URL/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: rollback-demo@example.com" \
  -d "$TEST_PAYLOAD")

echo "$RESULT_AFTER" | jq '{
  model_version: .model.model_version,
  prediction: .predictions[0] | {
    label,
    score,
    reasons: (.reasons[:3])
  }
}'
echo ""

# Compare
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}STEP 5: Comparison${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

LABEL_BEFORE=$(echo "$RESULT_BEFORE" | jq -r '.predictions[0].label')
SCORE_BEFORE=$(echo "$RESULT_BEFORE" | jq -r '.predictions[0].score')
LABEL_AFTER=$(echo "$RESULT_AFTER" | jq -r '.predictions[0].label')
SCORE_AFTER=$(echo "$RESULT_AFTER" | jq -r '.predictions[0].score')

printf "%-20s | %-12s | %-5s\n" "Version" "Label" "Score"
printf "%-20s | %-12s | %-5s\n" "--------------------" "------------" "-----"
printf "%-20s | %-12s | %.2f\n" "Before ($CURRENT_VERSION)" "$LABEL_BEFORE" "$SCORE_BEFORE"
printf "%-20s | %-12s | %.2f\n" "After ($NEW_VERSION)" "$LABEL_AFTER" "$SCORE_AFTER"
echo ""

# Check audit logs
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}STEP 6: Audit Trail${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Recent audit entries showing version changes:"
tail -2 audit_logs/audit.jsonl | jq '{
  timestamp: .timestamp[:19],
  model_version,
  label: .predictions[0].label,
  score: .predictions[0].score
}'
echo ""

echo -e "${GREEN}✅ Rollback demo complete!${NC}"
echo ""
echo "Key observations:"
echo "• v1.0.0: More conservative (condition: 'gte')"
echo "• v2.0.0: Stricter thresholds (if_price_gte)"  
echo "• Hot reload: Zero downtime"
echo "• Audit: Both versions tracked"
echo ""
