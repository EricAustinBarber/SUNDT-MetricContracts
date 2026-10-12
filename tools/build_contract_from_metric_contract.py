"""Convert the project metric_contract.json into the repository contract shape."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

def build(
    source: Path,
    output: Path,
    assets_manifest: Path | None = None,
    relationships_csv: Path | None = None,
) -> None:
    src = json.loads(source.read_text(encoding="utf-8"))
    product = src.get("data_product", {})
    metrics = []
    for item in src.get("metrics", []):
        metrics.append({
            "metricId": item["name"],
            "displayName": item.get("display_name", item["name"]),
            "definition": f"Power BI measure {item['name']} on {item['table']}.",
            "modelTable": item["table"],
            "role": item.get("role", "base_value"),
            "expressionLanguage": "DAX",
            "daxExpression": item.get("dax_expression", "").strip(),
            "formatString": item.get("format_string", ""),
            "grain": item.get("grain", "model_defined"),
            "aggregationRule": item.get("aggregation_rule", "model_defined"),
            "directDependencies": item.get("direct_dependencies", []),
            "transitiveDependencies": item.get("transitive_dependencies", []),
            "lineage": {
                "sourcePaths": item.get("source_lineage", []),
                "alationObjectIds": [],
                "status": "matched" if item.get("source_lineage") else "model_only",
            },
            "usage": {
                "referenceCount": len(item.get("visual_usage", [])),
                "visuals": [str(v.get("visual", v)) if isinstance(v, dict) else str(v) for v in item.get("visual_usage", [])],
            },
            "glossaryTerms": [],
            "review": {
                "status": "in_review",
                "notes": "Generated from the Power BI metric contract; steward review required.",
            },
        })
    assets = {"reports": [], "semanticModels": []}
    if assets_manifest:
        manifest = json.loads(assets_manifest.read_text(encoding="utf-8"))
        assets["reports"] = manifest.get("reports", [])
        assets["semanticModels"] = manifest.get("semanticModels", [])

    relationships = []
    if relationships_csv:
        with relationships_csv.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                relationships.append(
                    {
                        "name": row.get("name", ""),
                        "fromTable": row.get("from_table", ""),
                        "fromColumn": row.get("from_column", ""),
                        "toTable": row.get("to_table", ""),
                        "toColumn": row.get("to_column", ""),
                        "crossFilteringBehavior": row.get("cross_filtering_behavior", ""),
                        "cardinality": row.get("cardinality", ""),
                        "isActive": str(row.get("is_active", "")).lower() == "true",
                    }
                )

    payload = {
        "contractVersion": "0.1.0",
        "contractStatus": "submitted",
        "product": {
            "productId": product.get("product_id", "group-health-dashboard"),
            "name": product.get("name", "Group Health Dashboard"),
            "description": "Power BI semantic-model contract generated for Alation and agent/API review.",
            "businessContext": "Generated from the approved project semantic-model evidence.",
            "exampleQuestions": ["What does this metric mean?", "Which sources feed this metric?", "Which visuals consume this metric?"],
        },
        "assets": assets,
        "metrics": metrics,
        "relationships": relationships,
        "review": {
            "owner": "Power BI / Data Governance",
            "steward": "Assign steward",
            "certificationStatus": "in_review",
            "lastReviewed": None,
            "knownLimitations": ["Glossary and relationship mappings require steward review."],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"generated={output} metrics={len(metrics)}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--assets-manifest", type=Path, default=None)
    parser.add_argument("--relationships-csv", type=Path, default=None)
    args = parser.parse_args()
    build(args.source, args.output, args.assets_manifest, args.relationships_csv)

if __name__ == "__main__": main()
