"""Merge the Power BI metric contract into an exported Alation Data Product.

This is an offline build step. Existing record sets, metrics, relationships,
delivery systems, and descriptions are preserved. Power BI metrics are added
to metadata.metrics and the semantic model is added as a record set.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml


def powerbi_metric(metric: dict) -> dict:
    return {
        "displayName": metric["displayName"],
        "description": metric["definition"],
        "expression": metric["daxExpression"],
        "type": "numeric",
        "columns": metric.get("directDependencies", []),
        "x-source": "powerbi-semantic-model",
        "x-expressionLanguage": metric.get("expressionLanguage", "DAX"),
        "x-powerBiTable": metric.get("modelTable", ""),
        "x-powerBiRole": metric.get("role", ""),
        "x-formatString": metric.get("formatString", ""),
        "x-grain": metric.get("grain", ""),
        "x-aggregationRule": metric.get("aggregationRule", ""),
        "x-transitiveDependencies": metric.get("transitiveDependencies", []),
        "x-sourceLineage": metric.get("lineage", {}).get("sourcePaths", []),
        "x-alationObjectIds": metric.get("lineage", {}).get("alationObjectIds", []),
        "x-lineageStatus": metric.get("lineage", {}).get("status", ""),
        "x-visualUsageCount": metric.get("usage", {}).get("referenceCount", 0),
        "x-visualUsage": metric.get("usage", {}).get("visuals", []),
        "x-glossaryTerms": metric.get("glossaryTerms", []),
        "x-reviewStatus": metric.get("review", {}).get("status", ""),
    }


def build(source_yaml: Path, contract_json: Path, output_json: Path, output_yaml: Path | None, version: str, repository_url: str) -> dict:
    exported = yaml.safe_load(source_yaml.read_text(encoding="utf-8"))
    contract = json.loads(contract_json.read_text(encoding="utf-8"))
    product = copy.deepcopy(exported["product"])
    metadata = product.setdefault("metadata", {})
    existing_metrics = metadata.setdefault("metrics", {})
    existing_metric_ids = set(existing_metrics)
    powerbi_metrics = {metric["metricId"]: powerbi_metric(metric) for metric in contract["metrics"]}
    collision_ids = sorted(existing_metric_ids & set(powerbi_metrics))
    if collision_ids:
        raise RuntimeError(f"Metric ID collisions require steward resolution: {collision_ids[:10]}")
    existing_metrics.update(powerbi_metrics)

    product["version"] = version
    product.setdefault("deliverySystems", {})["powerbi"] = {
        "type": "bi",
        "uri": "https://app.powerbi.com/groups/me/reports/a9e46f0b-86b8-4ff0-9481-3bb4f0dd9644",
    }
    product.setdefault("recordSets", {})["powerbi_semantic_model"] = {
        "name": "swa-dataset-project-controls-management-executive",
        "displayName": "Group Health Power BI semantic model",
        "description": "Power BI semantic model for the Group Health dashboard. Exact DAX is retained in metadata.metrics.",
        "schema": [
            {
                "name": metric["metricId"],
                "displayName": metric["displayName"],
                "description": metric["definition"],
                "type": "numeric",
                "x-expressionLanguage": "DAX",
            }
            for metric in contract["metrics"]
        ],
        "dataAccess": [
            {
                "type": "other",
                "documentationUrl": repository_url,
            }
        ],
    }
    metadata["x-contractVersion"] = contract["contractVersion"]
    metadata["x-contractStatus"] = contract["contractStatus"]
    metadata["x-contractRepository"] = repository_url
    metadata["x-powerBiRelationships"] = contract.get("relationships", [])
    metadata["x-powerBiAssets"] = contract.get("assets", {})
    metadata["x-powerBiMetricCount"] = len(powerbi_metrics)
    metadata["x-existingMetricCount"] = len(existing_metric_ids)
    metadata["x-mergePolicy"] = "preserve_existing_and_add_powerbi_contract"

    result = {"product": product}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if output_yaml:
        output_yaml.write_text(yaml.safe_dump(result, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"existing_metrics={len(existing_metric_ids)} added_powerbi_metrics={len(powerbi_metrics)} total_metrics={len(existing_metrics)}")
    print(f"existing_recordsets={len(exported['product'].get('recordSets', {}))} total_recordsets={len(product['recordSets'])}")
    print(f"existing_relationships={len(exported['product'].get('metadata', {}).get('relationships', []))} powerbi_relationships={len(contract.get('relationships', []))}")
    print(f"json={output_json}")
    if output_yaml:
        print(f"yaml={output_yaml}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-yaml", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-yaml", type=Path, default=None)
    parser.add_argument("--version", default="1.1.0")
    parser.add_argument("--repository-url", required=True)
    args = parser.parse_args()
    build(args.source_yaml, args.contract, args.output_json, args.output_yaml, args.version, args.repository_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
