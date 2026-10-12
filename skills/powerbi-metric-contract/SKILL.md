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
- deployment path from report to page/visual to measure to DAX
- certification and confidence status

## Deployment-path requirement

Every metric must make its edit and consumption path explicit:

`Power BI report → page → visual → field reference → semantic-model table → measure → DAX`

For each directly referenced visual, retain the report ID, report name, page
name, stable visual ID, visual name/title, visual type, and exact field
reference. Also identify the semantic-model dataset where the DAX was
extracted, the reconciled/deployed dataset when different, and the Alation
asset IDs when available.

The contract must state that the DAX is edited on the semantic-model measure;
the report visual consumes the measure and does not own the DAX definition.
Measures with no direct visual reference must remain in the contract and be
marked as indirect, unused, or unresolved rather than omitted.

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
5. Attach report pages and visuals from the report inventory, preserving stable
   visual IDs and field references.
6. Attach source paths from the source-lineage inventory.
7. Attach the source semantic-model asset, consuming report asset, reconciled
   dataset identity, and DAX edit directions.
8. Add agent guidance for charting, filtering, grain, and aggregation.
9. Write JSON and Markdown outputs and report unresolved items.

Use the bundled generator when available:

```powershell
python skills\powerbi-metric-contract\scripts\build_metric_contract.py
```

The generator is deterministic and may be rerun after a Power BI or Alation refresh.
