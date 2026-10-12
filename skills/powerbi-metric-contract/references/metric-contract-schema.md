# Metric contract schema

The contract has four layers:

1. `data_product`: report, semantic-model aliases, owners, and certification.
2. `metrics`: one record per model measure, including exact DAX and dependency graph.
3. `recordsets`: chartable dimensions and measures with grain and aggregation rules.
4. `usage_guidance`: rules the agent must follow when answering or charting.

Recommended metric object:

```json
{
  "name": "Total_Score_Measure",
  "display_name": "Total Health Score",
  "role": "weighted_score",
  "value_type": "percentage",
  "format_string": "0.00%;-0.00%;0.00%",
  "grain": "project",
  "aggregation_rule": "do_not_sum",
  "dax_expression": "<exact expression>",
  "dependencies": ["FIN_Score_Measure", "QDR_Score_Measure"],
  "visual_usage": [{
    "report_id": "1785",
    "report_name": "group-Group Health",
    "page": "Executive Health",
    "visual_id": "3718042087",
    "visual_title": "Health Score",
    "visual_type": "chart_or_kpi",
    "field_reference": "Project Grades.Total_Score_Measure"
  }],
  "deployment_path": {
    "source_semantic_model_alation_id": 1355,
    "consuming_report_alation_id": 1785,
    "reconciled_semantic_model_alation_id": 1895,
    "model_table": "Project Grades",
    "measure_name": "Total_Score_Measure",
    "edit_directions": [
      "Open the mapped report and locate the listed page and visual.",
      "Open the report semantic model and locate the table and measure.",
      "Edit the measure DAX in the semantic model; the visual consumes it."
    ]
  },
  "source_lineage": ["prod.example.metric_source"],
  "agent_guidance": "Use for KPI cards, trends, or comparisons by project/group."
}
```

The agent-facing contract should expose numeric measures for charting and retain text/display measures as presentation metadata.
