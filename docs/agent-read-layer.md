# Agent/MCP contract read layer

The repository now includes a dependency-free local adapter that mirrors the
planned MCP tools. It reads only the approved contract and never queries data
or changes Alation.

```powershell
python tools/contract_read_layer.py search_metrics "health score" --include-uncertified
python tools/contract_read_layer.py get_metric_definition "FIN_Score_Trending"
python tools/contract_read_layer.py get_metric_lineage "FIN_Score_Trending"
python tools/contract_read_layer.py get_metric_visual_usage "FIN_Score_Trending"
python tools/contract_read_layer.py get_join_context --table fact_project_billing_current_v
python tools/contract_read_layer.py validate_metric_request "FIN_Score_Trending" --include-uncertified
```

Every response includes the product ID, contract version, and contract state.
It also includes the standard `asOf`, `sources`, `governance`, and
`limitations` fields required by the agent interface design.
The adapter returns explicit statuses such as `NOT_FOUND`, `UNCERTIFIED`,
`INVALID_AGGREGATION`, and `UNRESOLVED_LINEAGE`; it never substitutes a
similarly named metric.

The current contract is `submitted` and metrics are `in_review`, so normal
search excludes them until approval. Use `--include-uncertified` only for
steward review and development diagnostics.

The future MCP service should map these operations to the following resources:

- `alation://data-products/group-health-dashboard`
- `alation://data-products/group-health-dashboard/metrics/{metricId}`
- `alation://data-products/group-health-dashboard/metrics/{metricId}/lineage`
- `alation://data-products/group-health-dashboard/metrics/{metricId}/visual-usage`
- `alation://data-products/group-health-dashboard/relationships`

The machine-readable interface definition is
`config/mcp-interface.group-health.json`.

## Local transport adapter

For development, the same interface is available as a localhost-only HTTP
service:

```powershell
python tools/contract_http_service.py
```

Resource examples:

```text
GET  http://127.0.0.1:8765/health
GET  http://127.0.0.1:8765/resources/data-products/group-health-dashboard
GET  http://127.0.0.1:8765/resources/data-products/group-health-dashboard/metrics/FIN_Score_Trending
POST http://127.0.0.1:8765/tools/get_metric_definition
```

The HTTP adapter is a development transport, not the production MCP service.
It has no data-query capability and should not be bound to a public interface.
