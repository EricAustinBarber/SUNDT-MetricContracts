"""Validate a Power BI-Alation contract without external dependencies."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

VERSION = re.compile(r"^\d+\.\d+\.\d+$")
ROLES = {"base_value", "score", "weighted_score", "display", "status", "color", "arrow", "html", "trend"}
STATUSES = {"draft", "submitted", "validated", "steward_approved", "published", "retired"}

def fail(errors, message):
    errors.append(message)

def validate(path: Path):
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Invalid JSON: {exc}"]
    for key in ("contractVersion", "contractStatus", "product", "assets", "metrics", "relationships", "review"):
        if key not in data: fail(errors, f"Missing top-level field: {key}")
    if data.get("contractVersion") and not VERSION.match(data["contractVersion"]): fail(errors, "contractVersion must use semantic versioning")
    if data.get("contractStatus") not in STATUSES: fail(errors, "contractStatus is invalid")
    product = data.get("product", {})
    for key in ("productId", "name", "description"):
        if not product.get(key): fail(errors, f"Missing product.{key}")
    assets = data.get("assets", {})
    for kind in ("reports", "semanticModels"):
        if not isinstance(assets.get(kind), list): fail(errors, f"assets.{kind} must be an array")
        for i, asset in enumerate(assets.get(kind, [])):
            if not asset.get("name") or asset.get("alationId") in (None, ""): fail(errors, f"{kind}[{i}] requires name and alationId")
    metric_ids = set()
    for i, metric in enumerate(data.get("metrics", [])):
        prefix = f"metrics[{i}]"
        for key in ("metricId", "displayName", "modelTable", "expressionLanguage", "daxExpression", "grain", "aggregationRule", "lineage", "usage", "review"):
            if key not in metric: fail(errors, f"{prefix} missing {key}")
        mid = metric.get("metricId")
        if mid in metric_ids: fail(errors, f"Duplicate metricId: {mid}")
        metric_ids.add(mid)
        if metric.get("expressionLanguage") != "DAX": fail(errors, f"{prefix}.expressionLanguage must be DAX")
        if metric.get("role") not in ROLES: fail(errors, f"{prefix}.role is invalid")
        if not str(metric.get("daxExpression", "")).strip() or "REPLACE WITH" in str(metric.get("daxExpression")):
            fail(errors, f"{prefix}.daxExpression is missing or still a placeholder")
        lineage = metric.get("lineage", {})
        if lineage.get("status") not in {"matched", "partial", "unresolved", "model_only"}:
            fail(errors, f"{prefix}.lineage.status is invalid")
        usage = metric.get("usage", {})
        if not isinstance(usage.get("referenceCount"), int) or usage.get("referenceCount") < 0:
            fail(errors, f"{prefix}.usage.referenceCount must be a non-negative integer")
    review = data.get("review", {})
    for key in ("owner", "steward", "certificationStatus"):
        if not review.get(key): fail(errors, f"Missing review.{key}")
    if review.get("certificationStatus") not in {"unreviewed", "in_review", "approved", "rejected", "exception"}:
        fail(errors, "review.certificationStatus is invalid")
    return errors

def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/validate_contract.py <contract.json>")
        return 2
    path = Path(sys.argv[1])
    errors = validate(path)
    if errors:
        print(f"INVALID: {path}")
        for error in errors: print(f"- {error}")
        return 1
    print(f"VALID: {path}")
    return 0

if __name__ == "__main__": sys.exit(main())
