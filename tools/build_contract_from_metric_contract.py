"""Convert the project metric_contract.json into the repository contract shape."""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path

def build(
    source: Path,
    output: Path,
    assets_manifest: Path | None = None,
    relationships_csv: Path | None = None,
    visual_inventory: Path | None = None,
) -> None:
    src = json.loads(source.read_text(encoding="utf-8"))
    product = src.get("data_product", {})
    manifest = json.loads(assets_manifest.read_text(encoding="utf-8")) if assets_manifest else {}
    reports = manifest.get("reports", [])
    semantic_models = manifest.get("semanticModels", [])
    source_model = next((item for item in semantic_models if item.get("role") == "report_parent_datasource"), {})
    reconciled_models = [item for item in semantic_models if item.get("role") == "reconciled_semantic_model"]
    visuals_by_measure: dict[str, list[dict[str, str]]] = {}
    if visual_inventory and visual_inventory.exists():
        with visual_inventory.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("report_id") != "1785":
                    continue
                for reference in row.get("field_references", "").split(" | "):
                    measure_name = reference.rsplit(".", 1)[-1]
                    measure_name = re.sub(
                        r"^(?:Sum|Min|Max|Count|DistinctCount|Average)\((.*)\)$",
                        r"\1",
                        measure_name,
                        flags=re.IGNORECASE,
                    )
                    if measure_name:
                        visuals_by_measure.setdefault(measure_name.upper(), []).append({
                            "page": row.get("page_name", ""),
                            "visualId": row.get("visual_id", ""),
                            "visualName": row.get("visual_name", ""),
                            "visualTitle": row.get("visual_title", ""),
                            "visualType": row.get("visual_type", ""),
                            "fieldReference": reference,
                        })
    metrics = []
    for item in src.get("metrics", []):
        name = item["name"]
        visual_usage = visuals_by_measure.get(name.upper(), item.get("visual_usage", []))
        metrics.append({
            "metricId": name,
            "displayName": item.get("display_name", name),
            "definition": f"Power BI measure {name} on {item['table']}.",
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
            "powerBiAssetRefs": {
                "daxSourceSemanticModel": source_model,
                "consumedByReports": reports,
                "reconciledSemanticModels": reconciled_models,
                "mappingBasis": "DAX extracted from the source semantic-model evidence; report and reconciled model references are explicit project identity mappings.",
            },
            "usage": {
                "referenceCount": len(visual_usage),
                "visuals": visual_usage,
            },
            "deploymentPath": {
                "report": reports,
                "sourceSemanticModel": source_model,
                "reconciledSemanticModels": reconciled_models,
                "measureName": name,
                "editDirections": [
                    "Open the mapped Power BI report and locate the listed page and visual.",
                    "Open the report's mapped semantic model/dataset and locate the model table and measure.",
                    "Edit the measure DAX in the semantic model; visuals consume the measure and do not own the DAX definition.",
                ],
            },
            "glossaryTerms": [],
            "review": {
                "status": "in_review",
                "notes": "Generated from the Power BI metric contract; steward review required.",
            },
        })
    assets = {"reports": [], "semanticModels": []}
    if manifest:
        assets["reports"] = reports
        assets["semanticModels"] = semantic_models

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
    parser.add_argument("--visual-inventory", type=Path, default=None)
    args = parser.parse_args()
    build(args.source, args.output, args.assets_manifest, args.relationships_csv, args.visual_inventory)

if __name__ == "__main__": main()
