"""Validate preservation and contract embedding in a merged Data Product."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-yaml", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--merged", type=Path, required=True)
    args = parser.parse_args()

    source = yaml.safe_load(args.source_yaml.read_text(encoding="utf-8"))["product"]
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    merged = json.loads(args.merged.read_text(encoding="utf-8"))["product"]
    errors = []
    source_metrics = source.get("metadata", {}).get("metrics", {})
    merged_metrics = merged.get("metadata", {}).get("metrics", {})
    contract_metrics = {metric["metricId"]: metric for metric in contract["metrics"]}

    for metric_id, metric in source_metrics.items():
        if merged_metrics.get(metric_id) != metric:
            errors.append(f"existing metric changed: {metric_id}")
    for metric_id, metric in contract_metrics.items():
        actual = merged_metrics.get(metric_id)
        if not actual:
            errors.append(f"missing Power BI metric: {metric_id}")
        elif actual.get("expression") != metric.get("daxExpression"):
            errors.append(f"DAX mismatch: {metric_id}")
    if len(merged_metrics) != len(source_metrics) + len(contract_metrics):
        errors.append("merged metric count is not source plus contract count")
    if len(merged.get("recordSets", {})) != len(source.get("recordSets", {})) + 1:
        errors.append("merged record set count is not source plus Power BI model")
    if len(merged.get("metadata", {}).get("relationships", [])) != len(source.get("metadata", {}).get("relationships", [])):
        errors.append("existing native relationships were not preserved")
    if len(merged.get("metadata", {}).get("x-powerBiRelationships", [])) != len(contract.get("relationships", [])):
        errors.append("Power BI relationships were not embedded")
    if merged.get("metadata", {}).get("x-contractVersion") != contract.get("contractVersion"):
        errors.append("contract version marker is missing or incorrect")

    if errors:
        print("INVALID MERGED DATA PRODUCT")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"VALID MERGED DATA PRODUCT: metrics={len(merged_metrics)} "
        f"recordSets={len(merged['recordSets'])} "
        f"nativeRelationships={len(merged['metadata'].get('relationships', []))} "
        f"powerBiRelationships={len(merged['metadata'].get('x-powerBiRelationships', []))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
