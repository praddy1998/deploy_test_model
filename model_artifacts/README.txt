Mock Model Artifacts (Candidate Starter Pack)

This folder provides two deterministic 'model artifacts' (JSON) to simulate an ML model registry + rollout/rollback.

Files:
- model_manifest.json  : indicates which version is active
- model_v1.json        : baseline rules (v1.0.0)
- model_v2.json        : stricter rules (v2.0.0)

Expected service behavior:
- On startup, the API loads model_manifest.json, then loads the active model file.
- GET /model returns the loaded version + sha256 checksum of the active model file.
- OPTIONAL: POST /model/reload reloads model_manifest.json and swaps the active model without restart.
- Rollback is done by changing active_model_version back to 1.0.0 (or any available version).

Deterministic scoring suggestion:
score = clamp(
    base_score
  + channel_weight(channel)
  + price_rule_contrib(price)
  + units_rule_contrib(units)
  + text_rule_contrib(text),
  0, 1
)

Label suggestion:
if score <= low_risk_max  -> low_risk
elif score <= medium_risk_max -> medium_risk
else -> high_risk
