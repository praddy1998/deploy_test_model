"""Prometheus metrics definitions."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# HTTP-level metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["route", "method", "status"],
)

http_request_latency_ms = Histogram(
    "http_request_latency_ms",
    "HTTP request latency in milliseconds",
    ["route"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)

# Application-level metrics
predict_requests_total = Counter(
    "predict_requests_total",
    "Total prediction requests",
)

predict_errors_total = Counter(
    "predict_errors_total",
    "Total prediction errors",
)

audit_write_errors_total = Counter(
    "audit_write_errors_total",
    "Total audit log write failures",
)
