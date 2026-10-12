---
name: powerbi-metric-contract
description: Derive an agent-ready metric contract from Power BI semantic-model inventories, including exact DAX, KPI dependency chains, formats, grain, visual usage, and upstream lineage.
metadata:
  short-description: Build Power BI metric contracts with DAX lineage
---

# Power BI metric contract

Use this skill when a Power BI semantic model or report must be prepared for an Alation data product or agent that needs to explain, filter, compare, or chart metrics.

## Outcome

Produce two synchronized outputs:

- `metric_contract.json`: structured metadata suitable for an agent/data-product ingestion process.
- `metric_contract.md`: human-readable documentation showing each KPI, its exact DAX, dependencies, format, usage, and source lineage.

## Required evidence

Prefer extracted inventories over visual inspection alone:

- `inventories/measures.csv`
- `inventories/columns.csv`
- `inventories/tables.csv`
- `lineage/measure_dependencies.csv`
- `lineage/report_visual_inventory.csv`
- `lineage/report_visual_source_lineage.csv`
- `lineage/source_paths.csv` or `lineage/prod_source_to_metric_lineage.csv`

If the model is a live-connected PBIX, use the PBIX layout for report usage and the Alation datasource for field identity; do not infer missing DAX from the report layout.

## Required metric fields

Each metric record must include:

- stable metric name and display name
- semantic-model table and object name
- metric role: `base_value`, `score`, `weighted_score`, `display`, `status`, `color`, `arrow`, `html`, or `trend`
- exact DAX expression when available
- format string and value type
- business grain and safe aggregation rule
- direct and transitive dependencies
- report pages, visuals, and KPI cards using the metric
- upstream model/source lineage
- certification and confidence status

## Rules

- Preserve DAX exactly; add an explanatory interpretation separately.
- Distinguish numeric measures from display measures that return text such as `"1.75 / 2"` or `"Not Active"`.
- Never recommend summing percentages or scores unless the model explicitly defines that aggregation.
- Preserve weighting, toggles, inactive states, and denominator logic.
- Treat `_Color`, `_Arrow`, and `_HTML` measures as presentation logic, not primary chart metrics.
- Mark unresolved lineage explicitly; do not invent upstream sources.
- Keep Power BI files and production source objects unedited.

## Workflow

1. Load the inventories and normalize measure, table, column, and visual names.
2. Classify measures from names, expressions, format strings, and visual usage.
3. Build direct dependency edges from the dependency inventory and measure references.
4. Expand dependencies transitively with cycle detection.
5. Attach report pages and visuals from the report inventory.
6. Attach source paths from the source-lineage inventory.
7. Add agent guidance for charting, filtering, grain, and aggregation.
8. Write JSON and Markdown outputs and report unresolved items.

Use the bundled generator when available:

```powershell
python skills\powerbi-metric-contract\scripts\build_metric_contract.py
```

The generator is deterministic and may be rerun after a Power BI or Alation refresh.
