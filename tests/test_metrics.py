"""Test 8: Prometheus metrics increment correctly."""


def test_metrics_endpoint_returns_prometheus_format(client):
    """GET /metrics returns valid Prometheus text format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "# HELP" in content or "# TYPE" in content


def test_predict_request_increments_metrics(
    client, predict_payload, predict_headers
):
    """Test 8: predict_requests_total increments after a predict call."""
    # Make a prediction
    client.post("/predict", json=predict_payload, headers=predict_headers)

    # Check metrics incremented
    resp_after = client.get("/metrics")
    text_after = resp_after.text

    assert "predict_requests_total" in text_after

    # The counter should be present and non-zero
    for line in text_after.split("\n"):
        if line.startswith("predict_requests_total") and not line.startswith("#"):
            value = float(line.split()[-1])
            assert value >= 1.0, "predict_requests_total should be >= 1"
            break


def test_http_requests_total_metric(client):
    """http_requests_total metric is present with labels."""
    client.get("/healthz")
    response = client.get("/metrics")
    assert "http_requests_total" in response.text


def test_metrics_contain_all_required_counters(client, predict_payload, predict_headers):
    """All five required metrics are exposed."""
    # Trigger some activity
    client.get("/healthz")
    client.post("/predict", json=predict_payload, headers=predict_headers)

    response = client.get("/metrics")
    text = response.text

    required_metrics = [
        "http_requests_total",
        "predict_requests_total",
        "predict_errors_total",
        "audit_write_errors_total",
        "http_request_latency_ms",
    ]
    for metric_name in required_metrics:
        assert metric_name in text, f"Missing required metric: {metric_name}"
