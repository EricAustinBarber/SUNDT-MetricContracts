"""Build an agent-ready metric contract from the Group Health inventories."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "semantic-model-documentation"
OUT = ROOT / "agent-contract"


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def classify(name: str, expression: str, fmt: str) -> str:
    upper = name.upper()
    expr = expression.upper()
    if "HTML" in upper:
        return "html"
    if "_COLOR" in upper or upper.endswith(" COLOR"):
        return "color"
    if "_ARROW" in upper or upper.endswith(" ARROW"):
        return "arrow"
    if "TREND" in upper or "TRENDING" in upper:
        return "trend"
    if "NOT ACTIVE" in expr or "& \" /" in expression:
        return "display"
    if "TOTAL_SCORE" in upper or upper.endswith("_SCORE_MEASURE"):
        return "weighted_score" if "TOTAL" in upper else "score"
    if "%" in fmt or "PERCENT" in upper or "PERC" in upper or "RATE" in upper:
        return "base_value"
    return "base_value"


def referenced_names(expression: str) -> set[str]:
    return set(re.findall(r"\[([^\]]+)\]", expression or ""))


def main() -> None:
    measures = rows(ROOT / "inventories" / "measures.csv")
    visuals = rows(ROOT / "lineage" / "report_visual_inventory.csv")
    visual_lineage = rows(ROOT / "lineage" / "report_visual_source_lineage.csv")
    source_lineage = rows(ROOT / "lineage" / "prod_source_to_metric_lineage.csv")

    by_measure = {r["measure"].upper(): r for r in measures if r.get("measure")}
    usages = defaultdict(list)
    for row in visuals:
        if row.get("report_id") != "1785":
            continue
        for ref in row.get("field_references", "").split(" | "):
            name = ref.rsplit(".", 1)[-1]
            name = re.sub(r"^(?:Sum|Min|Max|Count|DistinctCount|Average)\((.*)\)$", r"\1", name, flags=re.I)
            usages[name.upper()].append({"page": row.get("page_name", ""), "visual": row.get("visual_title", ""), "type": row.get("visual_type", "")})

    sources_by_measure = defaultdict(set)
    for row in source_lineage:
        for name in row.get("measures", "").split(" | "):
            if name.strip():
                sources_by_measure[name.strip().upper()].add(row.get("prod_source_path", ""))

    graph = {name: referenced_names(row.get("expression", "")) for name, row in by_measure.items()}

    def expand(name: str, seen: set[str] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        if name in seen:
            return set()
        seen.add(name)
        result = set()
        for dep in graph.get(name, set()):
            result.add(dep)
            if dep.upper() in graph:
                result.update(expand(dep.upper(), seen))
        return result

    contract_metrics = []
    for key, row in sorted(by_measure.items()):
        name = row["measure"]
        expression = row.get("expression", "")
        fmt = row.get("format_string", "")
        role = classify(name, expression, fmt)
        used = usages.get(key, [])
        contract_metrics.append({
            "name": name,
            "display_name": name.replace("_", " "),
            "table": row.get("table", ""),
            "role": role,
            "value_type": "percentage" if "%" in fmt else "text" if role in {"display", "html"} else "numeric",
            "format_string": fmt,
            "grain": "project_or_report_context",
            "aggregation_rule": "do_not_sum" if "%" in fmt or "SCORE" in name.upper() else "model_defined",
            "dax_expression": expression,
            "direct_dependencies": sorted(referenced_names(expression)),
            "transitive_dependencies": sorted(expand(key)),
            "visual_usage": used,
            "source_lineage": sorted(sources_by_measure.get(key, set())),
            "certification_status": "documented_in_semantic_model",
        })

    contract = {
        "contract_version": "1.0",
        "data_product": {
            "name": "Group Health Executive Metrics",
            "report": "group-Group Health",
            "report_id": "1785",
            "semantic_model_aliases": [
                {"alation_id": "1355", "name": "swa-dataset-project-controls-management-deathstar-pilot"},
                {"alation_id": "1895", "name": "swa-dataset-project-controls-management-executive"},
            ],
            "status": "draft_for_agent_review",
        },
        "metrics": contract_metrics,
        "usage_guidance": [
            "Use numeric measures for charts; treat display, HTML, color, and arrow measures as presentation metadata.",
            "Do not sum percentage or score measures unless the model explicitly defines the aggregation.",
            "Preserve inactive states such as Not Active; do not convert them to zero without instruction.",
            "Use project, group, district, and date as the primary analytical dimensions.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metric_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    with (OUT / "metric_contract.md").open("w", encoding="utf-8") as handle:
        handle.write("# Group Health metric contract\n\n")
        handle.write("Generated from the Power BI semantic-model inventories. DAX expressions are preserved exactly.\n\n")
        for metric in contract_metrics:
            handle.write(f"## {metric['display_name']}\n\n")
            handle.write(f"- Role: `{metric['role']}`\n- Table: `{metric['table']}`\n- Format: `{metric['format_string']}`\n- Aggregation: `{metric['aggregation_rule']}`\n")
            if metric["visual_usage"]:
                handle.write(f"- Visual usage: {len(metric['visual_usage'])} report references\n")
            handle.write("\n### DAX\n\n```DAX\n" + metric["dax_expression"].rstrip() + "\n```\n\n")
            handle.write("### Dependencies\n\n" + ", ".join(f"`{x}`" for x in metric["transitive_dependencies"]) + "\n\n")
    print(f"wrote {len(contract_metrics)} metric records to {OUT}")


if __name__ == "__main__":
    main()
