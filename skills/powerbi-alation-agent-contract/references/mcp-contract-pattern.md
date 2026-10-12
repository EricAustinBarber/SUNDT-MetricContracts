# MCP/API contract pattern

## Design principle

The interface should return governed metric context, not just values. A metric answer without its definition, version, lineage, and certification status is not sufficient for governed agent use.

## Recommended resources

- `alation://data-products/{productId}`
- `alation://data-products/{productId}/metrics/{metricId}`
- `alation://data-products/{productId}/metrics/{metricId}/lineage`
- `alation://data-products/{productId}/metrics/{metricId}/visual-usage`
- `alation://data-products/{productId}/relationships`

## Recommended tools

### `search_metrics`

Input:

```json
{
  "query": "string",
  "productId": "string",
  "includeUncertified": false
}
```

Output should return metric IDs, names, descriptions, roles, certification status, and match reasons.

### `get_metric_definition`

Returns exact DAX, expression language, format, grain, aggregation rule, direct dependencies, source lineage, and contract version.

### `get_metric_lineage`

Returns report, visual, semantic model, model table/column, Power Query/source path, and Alation object references. Include unresolved edges explicitly.

### `get_metric_visual_usage`

Returns pages, visual IDs, visual types, titles, field references, aggregations, and downstream impact status.

### `get_join_context`

Returns model relationships, left/right tables, join expression, cardinality, nullable behavior, filters, and notes. Do not infer SQL joins from names alone.

### `validate_metric_request`

Checks metric existence, allowed aggregation, grain compatibility, certification, source freshness, and access before an agent generates a chart or query.

### `get_metric_quality_status`

Returns reconciliation status, source freshness, schema validity, known limitations, and last steward review.

## Error behavior

Use explicit states:

- `NOT_FOUND`
- `UNAUTHORIZED`
- `UNCERTIFIED`
- `STALE_CONTRACT`
- `UNRESOLVED_LINEAGE`
- `INVALID_AGGREGATION`
- `AMBIGUOUS_METRIC`
- `SOURCE_UNAVAILABLE`

Never silently substitute a similarly named metric.

## Versioning

Use semantic versions:

- Major: DAX meaning, grain, source, or output contract changes
- Minor: additive metric, glossary, lineage, or optional metadata changes
- Patch: description, owner, documentation, or non-semantic correction

Every response should identify the version used. Deprecated metrics should return their replacement or an explicit deprecation message.

