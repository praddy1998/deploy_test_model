# Mock ML Inference API

A production-ready HTTP microservice that serves deterministic risk classifications from versioned model artifacts. Built with FastAPI, containerized with Docker, and fully observable with structured logging and Prometheus metrics.

## Quick Start

```bash
docker compose up --build
```

The service starts at **http://localhost:8000**.

## Architecture

```
Client  →  FastAPI (port 8000)
             ├── Middleware (latency tracking, PII redaction)
             ├── Guardrails (policy block, secret scan)
             ├── Scoring Engine (deterministic rules)
             ├── Model Loader (manifest + artifact + checksum)
             ├── Audit Logger (append-only JSONL)
             └── Metrics Collector (Prometheus)
```

### Project Structure

```
app/
  main.py              # FastAPI app, lifespan, middleware
  config.py            # Settings
  models/
    loader.py          # Artifact loading, checksum validation
    scorer.py          # Deterministic scoring engine
    schemas.py         # Pydantic request/response models
  guardrails/
    policy.py          # Policy-block keyword detection
    redaction.py       # PII / secret redaction
    identity.py        # Email hashing
  observability/
    audit.py           # Append-only JSONL audit writer
    metrics.py         # Prometheus counters and histograms
    logging.py         # Structured JSON logging
  routes/
    predict.py         # POST /predict
    model.py           # GET /model, POST /model/reload
    health.py          # GET /healthz, GET /readyz
    metrics.py         # GET /metrics
model_artifacts/       # Versioned model JSON files
tests/                 # pytest test suite (16 tests)
```

## API Endpoints

### POST /predict

Score inputs against the active model.

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: user@example.com" \
  -d '{
    "request_id": "req-001",
    "inputs": [{
      "id": "item-1",
      "text": "Order for review",
      "features": {"price": 250.0, "units": 10, "channel": "amazon"}
    }]
  }'
```

### GET /model

Returns metadata about the currently loaded model, including version, checksum, and rule configuration.

### GET /healthz

Liveness probe. Always returns 200.

### GET /readyz

Readiness probe. Returns 200 if a valid model is loaded, 503 otherwise.

### GET /metrics

Prometheus-format metrics including:
- `http_requests_total{route, method, status}`
- `predict_requests_total`
- `predict_errors_total`
- `audit_write_errors_total`
- `http_request_latency_ms` (histogram for p95)

### POST /model/reload

Hot-reload the model manifest and switch to the active model version without restarting the service.

## Model Versioning and Rollback

The service loads model artifacts from `model_artifacts/`:

| File | Purpose |
|------|---------|
| `model_manifest.json` | Specifies active version, available versions, and paths |
| `model_v1.json` | Version 1.0.0 - Baseline conservative rules |
| `model_v2.json` | Version 2.0.0 - Stricter rules, higher text sensitivity |
| `CHECKSUMS.json` | SHA-256 checksums for artifact integrity validation |

### Model Manifest Format

```json
{
  "active_model_version": "2.0.0",
  "available_versions": ["1.0.0", "2.0.0"],
  "paths": {
    "1.0.0": "model_v1.json",
    "2.0.0": "model_v2.json"
  }
}
```

### Version Differences

| Parameter | v1.0.0 | v2.0.0 |
|-----------|--------|--------|
| base_score | 0.10 | 0.12 |
| high_price add | 0.35 | 0.40 |
| high_units add | 0.35 | 0.40 |
| negative_text add | 0.25 | 0.35 |
| low_risk_max | 0.33 | 0.30 |
| medium_risk_max | 0.66 | 0.60 |

**To rollback**: Change `active_model_version` in `model_manifest.json`, then call `POST /model/reload` or restart the service.

## Security

- **Policy Block**: Inputs containing disallowed phrases (e.g., "steal credentials", "exfiltrate data") are rejected with HTTP 400
- **PII Redaction**: Email addresses and token-like strings are redacted from all logs and audit records
- **Identity Hashing**: User emails are SHA-256 hashed before storage; raw emails are never persisted

## Audit Logging

Every `/predict` request appends a JSON record to `audit_logs/audit.jsonl` (append-only, gitignored) containing:
- timestamp, request_id, user_hash, route, model_version
- artifact checksum, input count, guardrails triggered
- status (success/blocked/error), latency, response checksum

## Development

### Run Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

### Lint

```bash
ruff check .
```

### Run Locally (without Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## CI/CD

GitHub Actions pipeline runs on pull requests:
1. **Lint** - `ruff check .`
2. **Test** - `pytest tests/ -v`
3. **Docker Build** - `docker compose build`

## Design Decisions

- **FastAPI + Pydantic**: Strict request validation, auto-generated OpenAPI docs, async support
- **Deterministic scoring**: All rules evaluated in fixed order with `round()` to prevent floating-point drift
- **Append-only audit**: JSONL format for easy streaming/parsing; write failures counted in metrics
- **Prometheus metrics**: Native text exposition; histogram for latency p95 approximation
- **No external dependencies at runtime**: All model artifacts are local JSON files
