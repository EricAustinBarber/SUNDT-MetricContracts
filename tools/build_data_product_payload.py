"""Build an Alation Data Product Specification payload from a metric contract.

This is an offline build step. It does not call Alation. The output is ready
for a future authorized Data Product Service publication adapter.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "/dps/api/v1/specs/product/"


def metric_payload(metric: dict) -> dict:
    return {
        "displayName": metric["displayName"],
        "description": metric["definition"],
        "type": "number",
        "expression": metric["daxExpression"],
        "columns": metric.get("directDependencies", []),
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


def build(contract_path: Path, output_path: Path, repository_url: str) -> None:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    product = contract["product"]
    metrics = contract.get("metrics", [])
    semantic_models = contract.get("assets", {}).get("semanticModels", [])
    primary_model = next(
        (asset for asset in semantic_models if asset.get("role") == "reconciled_semantic_model"),
        semantic_models[0] if semantic_models else {},
    )

    model_schema = [
        {
            "name": metric["metricId"],
            "displayName": metric["displayName"],
            "description": metric["definition"],
            "type": "number",
            "x-expressionLanguage": metric.get("expressionLanguage", "DAX"),
        }
        for metric in metrics
    ]
    model_access = {"type": "other", "documentationUrl": repository_url}
    if primary_model.get("externalId"):
        model_access["x-alationDatasourceExternalId"] = primary_model["externalId"]

    payload = {
        "schema": SCHEMA,
        "product": {
            "productId": product["productId"],
            "version": contract["contractVersion"],
            "contactName": contract.get("review", {}).get("owner", ""),
            "en": {
                "name": product["name"],
                "shortDescription": product["description"],
                "description": product.get("businessContext", ""),
                "exampleQuestions": product.get("exampleQuestions", []),
            },
            "recordSets": {
                "powerbi_semantic_model": {
                    "name": primary_model.get("name", "powerbi_semantic_model"),
                    "displayName": "Group Health Power BI semantic model",
                    "description": "Power BI semantic model surface. Metrics retain exact DAX in metadata.metrics.",
                    "schema": model_schema,
                    "dataAccess": [model_access],
                }
            },
            "metadata": {
                "metrics": {metric["metricId"]: metric_payload(metric) for metric in metrics},
                "relationships": [],
                "x-powerBiRelationships": contract.get("relationships", []),
                "x-contractVersion": contract["contractVersion"],
                "x-contractStatus": contract["contractStatus"],
                "x-contractRepository": repository_url,
                "x-powerBiAssets": {
                    "reports": contract.get("assets", {}).get("reports", []),
                    "semanticModels": semantic_models,
                },
            },
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"generated={output_path} metrics={len(metrics)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repository-url", required=True)
    args = parser.parse_args()
    build(args.contract, args.output, args.repository_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
