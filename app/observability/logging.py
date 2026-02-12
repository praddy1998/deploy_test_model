"""Structured JSON logging configuration with PII redaction."""

from __future__ import annotations

import logging
import sys

from pythonjsonlogger import json as json_logger

from app.guardrails.redaction import redact_pii


class RedactingFormatter(json_logger.JsonFormatter):
    """JSON formatter that redacts PII from log messages."""

    def format(self, record: logging.LogRecord) -> str:
        # Redact the message
        if isinstance(record.msg, str):
            record.msg = redact_pii(record.msg)
        # Redact args if they are strings
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_pii(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_pii(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structured JSON logging to stdout with redaction."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = RedactingFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
