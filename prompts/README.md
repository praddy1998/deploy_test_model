# LLM Usage Transparency

This project was built with the assistance of an LLM (Claude) in VS Code.

## Prompts Used

The primary prompt was a high-level instruction to implement the full take-home task specification, including:
- Model artifact loading and version management
- FastAPI service with all required endpoints
- Guardrails (policy block, PII redaction, identity hashing)
- Audit logging (append-only JSONL)
- Observability (structured logging, Prometheus metrics)
- Containerization (Dockerfile, docker-compose)
- CI/CD (GitHub Actions)
- Test suite (18 tests covering all required scenarios)

## Validation Steps

1. **Determinism verified**: Same input produces identical output across multiple runs
2. **All tests pass**: `pytest tests/ -v` runs 18 tests with 100% pass rate
3. **Linting clean**: `ruff check .` reports zero errors
4. **Docker build verified**: `docker compose up --build` starts the service successfully
5. **Manual endpoint testing**: All API endpoints tested via curl
6. **Audit log inspection**: Verified JSONL format, field completeness, and PII redaction
7. **Metrics verified**: Prometheus text format with all required counters/histograms
8. **Checksum validation**: SHA-256 checksums computed and verified against CHECKSUMS.json
9. **Model version rollback**: Tested switching between v1.0.0 and v2.0.0 via hot reload
