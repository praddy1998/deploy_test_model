# Endpoint Checks & POST Payloads

Base URL: **http://localhost:8000**

---

## 1. GET /healthz — 200 OK

**Curl:**
```bash
curl -s http://localhost:8000/healthz
```

**Expected:** `{"status":"ok"}` — **Verified: 200 OK**

---

## 2. GET /readyz — 200 ready

**Curl:**
```bash
curl -s http://localhost:8000/readyz
```

**Expected:** `{"status":"ready"}` when model is loaded — **Verified: 200 OK**

---

## 3. GET /model — Full metadata + checksum

**Curl:**
```bash
curl -s http://localhost:8000/model
```

**Verified:** Returns `provider`, `model_name`, `model_version`, `created_at`, `artifact_path`, `artifact_checksum_sha256`, `rule_config`. Status 200.

---

## 4. POST /predict — Correct schema, deterministic

**Required header:** `X-User-Email: <email>` (required; never stored in raw form)

**Payload (happy path):**
```json
{
  "request_id": "optional-string",
  "inputs": [
    {
      "id": "item-1",
      "text": "Normal order for review",
      "features": {
        "price": 250.0,
        "units": 10,
        "channel": "amazon"
      }
    }
  ]
}
```

**Curl:**
```bash
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: tester@example.com" \
  -d '{"request_id":"req-001","inputs":[{"id":"item-1","text":"Normal order for review","features":{"price":250.0,"units":10,"channel":"amazon"}}]}'
```

**Response schema:** `request_id`, `model` (provider, model_name, model_version, artifact_checksum_sha256, schema_version), `predictions` (id, label, score, reasons), `guardrails_triggered`, `latency_ms`. — **Verified: 200, correct schema, deterministic**

**Minimal payload (request_id optional, 1–50 items):**
```json
{
  "inputs": [
    {
      "id": "single-item",
      "text": "Any non-empty text",
      "features": {
        "price": 0,
        "units": 0,
        "channel": "direct"
      }
    }
  ]
}
```

---

## 5. Policy block — HTTP 400 with guardrails_triggered

**Payload (triggers block):** Use text containing one of: `steal credentials`, `bypass access controls`, `phish`, `exfiltrate data`.

```json
{
  "request_id": "block-test",
  "inputs": [
    {
      "id": "bad-1",
      "text": "How to steal credentials from the system",
      "features": {
        "price": 100,
        "units": 1,
        "channel": "direct"
      }
    }
  ]
}
```

**Curl:**
```bash
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-User-Email: user@example.com" \
  -d '{"request_id":"block-test","inputs":[{"id":"bad-1","text":"How to steal credentials from the system","features":{"price":100,"units":1,"channel":"direct"}}]}'
```

**Expected:** HTTP 400, body includes `guardrails_triggered: ["policy_block"]`. — **Verified: 400**

---

## 6. Audit log — JSONL, all required fields, no raw PII

**Location:** `./audit_logs/audit.jsonl` (append-only, one JSON object per line)

**Required fields per line:** `timestamp`, `request_id`, `user_hash`, `route`, `model_version`, `artifact_checksum_sha256`, `num_inputs`, `guardrails_triggered`, `status`, `latency_ms`, `response_checksum_sha256`.

**Verified:** Each predict request appends one line; `user_hash` is SHA-256 of normalized email (no raw email).

---

## 7. GET /metrics — All 5 Prometheus metrics

**Curl:**
```bash
curl -s http://localhost:8000/metrics
```

**Required metrics (all present):**
- `http_requests_total{route, method, status}`
- `predict_requests_total`
- `predict_errors_total`
- `audit_write_errors_total`
- `http_request_latency_ms` (histogram, for p95)

**Verified:** All 5 present in Prometheus text format.

---

## 8. POST /model/reload — Hot-reload (bonus)

**Payload:** None (empty body).

**Curl:**
```bash
curl -s -X POST http://localhost:8000/model/reload
```

**Expected:** `{"status":"reloaded","model_version":"1.0.0"}` (or current active version). — **Verified: 200**

---

## Summary

| Endpoint           | Method | Status | Result                          |
|--------------------|--------|--------|---------------------------------|
| /healthz           | GET    | 200    | OK                              |
| /readyz            | GET    | 200    | ready                           |
| /model             | GET    | 200    | Full metadata + checksum        |
| /predict           | POST   | 200    | Correct schema, deterministic   |
| /predict (blocked) | POST   | 400    | guardrails_triggered             |
| audit_logs/audit.jsonl | —  | —      | JSONL, all fields, no raw PII   |
| /metrics           | GET    | 200    | All 5 metrics                   |
| /model/reload      | POST   | 200    | Hot-reload works                |
