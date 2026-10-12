"""Validate an Alation Data Product payload without requiring network access.

This performs contract-to-payload reconciliation plus the required structural
checks used by the Alation Data Product Specification. It intentionally does
not claim to replace a full JSON Schema validator; the official schema is also
loaded and parsed when supplied.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(contract: dict, payload: dict, schema_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    if schema_path:
        try:
            import yaml  # type: ignore

            yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Could not parse retrieved Alation schema: {exc}")

    product = payload.get("product")
    if not isinstance(product, dict):
        return ["payload.product must be an object"]
    if payload.get("schema") != "/dps/api/v1/specs/product/":
        errors.append("payload.schema must reference /dps/api/v1/specs/product/")
    if product.get("productId") != contract["product"]["productId"]:
        errors.append("payload productId does not match contract")
    if product.get("version") != contract["contractVersion"] or not SEMVER.match(str(product.get("version", ""))):
        errors.append("payload product.version does not match contract version or is not semver")
    if not isinstance(product.get("en"), dict):
        errors.append("payload.product.en is required")

    expected_metrics = {metric["metricId"]: metric for metric in contract.get("metrics", [])}
    actual_metrics = product.get("metadata", {}).get("metrics", {})
    if not isinstance(actual_metrics, dict):
        errors.append("payload.product.metadata.metrics must be an object")
        actual_metrics = {}
    if set(actual_metrics) != set(expected_metrics):
        errors.append(
            f"metric key mismatch: expected {len(expected_metrics)}, got {len(actual_metrics)}"
        )
    for metric_id, expected in expected_metrics.items():
        actual = actual_metrics.get(metric_id)
        if not isinstance(actual, dict):
            errors.append(f"missing metric payload: {metric_id}")
            continue
        for field in ("displayName", "description", "expression"):
            if not str(actual.get(field, "")).strip():
                errors.append(f"metric {metric_id} missing {field}")
        if actual.get("expression") != expected.get("daxExpression"):
            errors.append(f"metric {metric_id} DAX expression does not match contract")
        if actual.get("x-expressionLanguage") != "DAX":
            errors.append(f"metric {metric_id} must declare x-expressionLanguage=DAX")

    record_sets = product.get("recordSets", {})
    if not isinstance(record_sets, dict) or not record_sets:
        errors.append("payload.product.recordSets must contain the semantic model")
    else:
        for record_set_name, record_set in record_sets.items():
            if not record_set.get("name") or not record_set.get("displayName"):
                errors.append(f"record set {record_set_name} requires name and displayName")
            fields = record_set.get("schema", [])
            if len(fields) != len(expected_metrics):
                errors.append(
                    f"record set {record_set_name} field count {len(fields)} does not equal metric count {len(expected_metrics)}"
                )
            if not record_set.get("dataAccess"):
                errors.append(f"record set {record_set_name} requires dataAccess")

    powerbi_relationships = product.get("metadata", {}).get("x-powerBiRelationships", [])
    expected_relationships = contract.get("relationships", [])
    if len(powerbi_relationships) != len(expected_relationships):
        errors.append(
            f"Power BI relationship count mismatch: expected {len(expected_relationships)}, got {len(powerbi_relationships)}"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--schema", type=Path, default=None)
    args = parser.parse_args()
    errors = validate(load_json(args.contract), load_json(args.payload), args.schema)
    if errors:
        print("INVALID DATA PRODUCT PAYLOAD")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID DATA PRODUCT PAYLOAD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
