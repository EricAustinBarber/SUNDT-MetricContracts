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
  "visual_usage": ["Executive Health / 16D"],
  "source_lineage": ["prod.example.metric_source"],
  "agent_guidance": "Use for KPI cards, trends, or comparisons by project/group."
}
```

The agent-facing contract should expose numeric measures for charting and retain text/display measures as presentation metadata.
