# Demo Scripts

This directory contains shell scripts to demonstrate the ML Inference API functionality.

## Available Scripts

### 1. `demo.sh` - Complete Feature Demo
Comprehensive walkthrough of all production features:
- ✅ Health checks (liveness & readiness)
- ✅ Model information & checksums
- ✅ Predictions (low, medium, high risk)
- ✅ Batch processing
- ✅ Security guardrails (policy block)
- ✅ Deterministic scoring
- ✅ Audit logging
- ✅ Prometheus metrics
- ✅ Model versioning
- ✅ Hot reload
- ✅ Error handling

**Usage:**
```bash
./demo.sh
```

**Duration:** ~5-7 minutes with pauses  
**Prerequisites:** Service running on http://localhost:8000

---

### 2. `demo_rollback.sh` - Model Version Rollback
Demonstrates switching between model versions with zero downtime:
- Shows current model version
- Makes prediction with v1.0.0 or v2.0.0
- Switches to the other version via hot reload
- Makes same prediction with new version
- Compares results
- Shows audit trail

**Usage:**
```bash
./demo_rollback.sh
```

**Duration:** ~2 minutes  
**What it proves:** Hot reload, version differences, audit continuity

---

### 3. `quick_test.sh` - Fast Validation
Quick smoke test of all core functionality (no pauses):
- Health & readiness checks
- Model version check
- Single prediction test
- Policy block validation
- Metrics exposure
- Audit log count

**Usage:**
```bash
./quick_test.sh
```

**Duration:** ~5 seconds  
**Use case:** CI/CD validation, quick sanity check

---

## Example Session

```bash
# Start the service
docker compose up --build -d

# Wait for service to be ready
sleep 5

# Run quick validation
./quick_test.sh

# Full interactive demo
./demo.sh

# Model rollback demo
./demo_rollback.sh

# Check audit logs
tail -10 audit_logs/audit.jsonl | jq
```

## Key Demonstrations

### Guardrails in Action
```bash
# Blocked request (HTTP 400)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: test@example.com" \
  -d '{"inputs": [{"id": "bad", "text": "steal credentials"}]}'
```

### Determinism
```bash
# Same input always produces same output
for i in {1..3}; do
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -H "X-User-Email: test@example.com" \
    -d '{"inputs": [{"id": "det", "text": "test", "features": {"price": 75}}]}' \
    | jq '.predictions[0].score'
done
```

### Hot Reload
```bash
# Update manifest
jq '.active_model_version = "1.0.0"' model_artifacts/model_manifest.json > /tmp/m.json
mv /tmp/m.json model_artifacts/model_manifest.json

# Trigger reload (no downtime)
curl -X POST http://localhost:8000/model/reload
```

## Notes

- All scripts require `jq` for JSON parsing
- Service must be running on default port 8000
- Scripts use color output (ANSI escape codes)
- Interactive scripts pause between sections
- `demo.sh` is best for presentations
- `quick_test.sh` is best for CI/CD

## Troubleshooting

**Service not responding:**
```bash
docker compose ps
docker compose logs -f
```

**Permission denied:**
```bash
chmod +x *.sh
```

**jq not found:**
```bash
# macOS
brew install jq

# Ubuntu
apt-get install jq
```
