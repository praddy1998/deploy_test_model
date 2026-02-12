"""Deterministic scoring engine for risk classification."""

from __future__ import annotations

from typing import Any


def _evaluate_price_rules(
    price: float, rules: list[dict[str, Any]]
) -> tuple[float, list[str]]:
    """Evaluate price rules and return contribution + reasons."""
    contribution = 0.0
    reasons: list[str] = []
    for rule in rules:
        # Support old format (condition) and new format (if_price_gte, if_price_lt, add)
        if "condition" in rule:
            # Old format: {"condition": "price >= 80", "contribution": 0.35, "reason": "high_price"}
            condition = rule["condition"]
            parts = condition.split()
            if len(parts) != 3:
                continue
            operator = parts[1]
            threshold = float(parts[2])
            matched = False
            if operator == ">" and price > threshold:
                matched = True
            elif operator == ">=" and price >= threshold:
                matched = True
            elif operator == "<" and price < threshold:
                matched = True
            elif operator == "<=" and price <= threshold:
                matched = True
            elif operator == "==" and price == threshold:
                matched = True
            if matched:
                contribution += rule["contribution"]
                reasons.append(rule["reason"])
                break  # Only first matching rule applies
        else:
            # New format: {"if_price_gte": 80, "add": 0.4, "reason": "high_price"}
            matched = False
            if "if_price_gte" in rule and price >= rule["if_price_gte"]:
                matched = True
            elif "if_price_gt" in rule and price > rule["if_price_gt"]:
                matched = True
            elif "if_price_lt" in rule and price < rule["if_price_lt"]:
                matched = True
            elif "if_price_lte" in rule and price <= rule["if_price_lte"]:
                matched = True
            if matched:
                contribution += rule["add"]
                reasons.append(rule["reason"])
                break  # Only first matching rule applies
    return contribution, reasons


def _evaluate_units_rules(
    units: int, rules: list[dict[str, Any]]
) -> tuple[float, list[str]]:
    """Evaluate units rules and return contribution + reasons."""
    contribution = 0.0
    reasons: list[str] = []
    for rule in rules:
        # Support old format (condition) and new format (if_units_gte, if_units_lt, add)
        if "condition" in rule:
            # Old format
            condition = rule["condition"]
            parts = condition.split()
            if len(parts) != 3:
                continue
            operator = parts[1]
            threshold = int(parts[2])
            matched = False
            if operator == ">" and units > threshold:
                matched = True
            elif operator == ">=" and units >= threshold:
                matched = True
            elif operator == "<" and units < threshold:
                matched = True
            elif operator == "<=" and units <= threshold:
                matched = True
            elif operator == "==" and units == threshold:
                matched = True
            if matched:
                contribution += rule["contribution"]
                reasons.append(rule["reason"])
                break  # Only first matching rule applies
        else:
            # New format: {"if_units_gte": 500, "add": 0.4, "reason": "high_units"}
            matched = False
            if "if_units_gte" in rule and units >= rule["if_units_gte"]:
                matched = True
            elif "if_units_gt" in rule and units > rule["if_units_gt"]:
                matched = True
            elif "if_units_lt" in rule and units < rule["if_units_lt"]:
                matched = True
            elif "if_units_lte" in rule and units <= rule["if_units_lte"]:
                matched = True
            if matched:
                contribution += rule["add"]
                reasons.append(rule["reason"])
                break  # Only first matching rule applies
    return contribution, reasons


def _evaluate_text_rules(
    text: str, rules: list[dict[str, Any]]
) -> tuple[float, list[str]]:
    """Evaluate text keyword rules. All matching rules contribute."""
    contribution = 0.0
    reasons: list[str] = []
    text_lower = text.lower()
    for rule in rules:
        # Support old format (keyword) and new format (keywords_any)
        if "keyword" in rule:
            # Old format: {"keyword": "chargeback", "contribution": 0.25, "reason": "negative_signal_text"}
            if rule["keyword"].lower() in text_lower:
                contribution += rule["contribution"]
                reasons.append(rule["reason"])
        elif "keywords_any" in rule:
            # New format: {"keywords_any": ["chargeback", "refund"], "add": 0.35, "reason": "..."}
            for keyword in rule["keywords_any"]:
                if keyword.lower() in text_lower:
                    contribution += rule["add"]
                    reasons.append(rule["reason"])
                    break  # Only count this rule once even if multiple keywords match
    return contribution, reasons


def score_input(
    text: str,
    price: float,
    units: int,
    channel: str,
    config: dict[str, Any],
) -> tuple[float, str, list[str]]:
    """
    Score a single input against the model config.

    Returns: (score, label, reasons)
    """
    base_score: float = config["base_score"]
    channel_weights: dict[str, float] = config["channel_weights"]
    price_rules: list[dict[str, Any]] = config["price_rules"]
    units_rules: list[dict[str, Any]] = config["units_rules"]
    text_rules: list[dict[str, Any]] = config["text_rules"]
    # Support both "risk_thresholds" and "thresholds"
    thresholds = config.get("risk_thresholds") or config.get("thresholds")

    reasons: list[str] = []

    # Channel weight
    channel_contrib = channel_weights.get(channel.lower(), 0.0)
    if channel_contrib != 0.0:
        reasons.append(f"channel_{channel.lower()}")

    # Price rules
    price_contrib, price_reasons = _evaluate_price_rules(price, price_rules)
    reasons.extend(price_reasons)

    # Units rules
    units_contrib, units_reasons = _evaluate_units_rules(units, units_rules)
    reasons.extend(units_reasons)

    # Text rules
    text_contrib, text_reasons = _evaluate_text_rules(text, text_rules)
    reasons.extend(text_reasons)

    # Compute final score
    score = base_score + channel_contrib + price_contrib + units_contrib + text_contrib

    # Clamp to [0.0, 1.0]
    score = max(0.0, min(1.0, score))

    # Round to avoid floating point drift
    score = round(score, 6)

    # Label assignment
    low_risk_max = thresholds["low_risk_max"]
    medium_risk_max = thresholds["medium_risk_max"]

    if score <= low_risk_max:
        label = "low_risk"
    elif score <= medium_risk_max:
        label = "medium_risk"
    else:
        label = "high_risk"

    return score, label, reasons
