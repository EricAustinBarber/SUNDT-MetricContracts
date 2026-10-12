---
name: powerbi-alation-agent-contract
description: Design, validate, and govern an API/MCP-ready data contract between Power BI semantic models and Alation data products, including DAX metrics, lineage, report usage, glossary context, joins, security, and delivery evidence.
metadata:
  short-description: Govern Power BI metrics through Alation for agent use
---

# Power BI–Alation agent contract

Use this skill when a Power BI report or semantic model must become governed, machine-readable context for Alation data products, agent APIs, MCP tools, analytics assistants, or downstream charting.

## Outcome

Produce an auditable contract and formal design that connects:

```text
Power BI source logic → semantic model → report visuals → Alation assets → data product → agent/API/MCP consumption
```

The Power BI model remains the authoritative source for DAX semantics. Alation provides catalog governance, ownership, certification, glossary context, lineage references, and the data-product boundary. The agent/API layer exposes only approved contract content.

## Scope and safety boundaries

- Use API-token access for Alation. Do not use browser sign-in when the workflow specifies API-only access.
- Keep PBIX/PBIT files, Power Query, report layouts, and production Databricks tables/views unedited unless the user explicitly requests otherwise.
- Treat a data-product URL slug as a locator, not proof of the internal product ID.
- Resolve live asset IDs before preparing writes.
- Stage and validate contract payloads before any Alation mutation.
- Do not submit catalog or data-product changes merely because steward approval is assumed; publication still requires an explicit implementation request and a supported API route.
- Never invent upstream lineage, glossary mappings, joins, ownership, or quality status. Mark unresolved items explicitly.

## Required companion evidence

Use the existing `powerbi-metric-contract` skill or equivalent extraction process first. Prefer these artifacts:

- `agent-contract/metric_contract.json`
- `agent-contract/metric_contract.md`
- `lineage/measure_dependencies.csv`
- `lineage/report_visual_inventory.csv`
- `lineage/report_visual_source_lineage.csv`
- `lineage/prod_source_to_metric_lineage.csv`
- `lineage/live_datasource_1895_field_reconciliation.csv`
- `alation/live_powerbi_asset_inventory.csv`

If a live-connected PBIX is available, use its report layout for visual usage and the live Alation datasource for catalog identity. Do not infer DAX from the report layout.

## Standard workflow

### 1. Establish the outcome

Define the user and governance outcome before selecting MCP or API technology. For the Group Health pattern, the outcome is:

> Agents and governed users can discover, explain, chart, and trace approved Group Health metrics without losing Power BI definitions, Alation governance, or source lineage.

Capture the outcome, users, business owner, steward, success measures, constraints, and decision deadline.

### 2. Inventory and reconcile assets

Identify and record:

- Power BI report ID, name, external ID, owner, and parent datasource
- Power BI semantic-model/datasource ID, name, external ID, table and measure counts
- PBIX/PBIT aliases and embedded report/model IDs
- Report pages, visuals, chart/KPI fields, and aggregations
- Alation datasource/report/column object IDs
- Source paths and production Alation table IDs
- Unresolved or conflicting mappings

Use stable IDs and preserve naming aliases. A naming mismatch is a reconciliation issue, not a reason to create duplicate assets.

### 3. Generate the metric contract

Each metric must carry, when available:

- stable name and display name
- model table and object name
- exact DAX expression
- expression language = `DAX`
- metric role: base value, score, weighted score, display, status, color, arrow, HTML, or trend
- value type and format string
- grain and safe aggregation rule
- direct and transitive dependencies
- source lineage and Alation object references
- report pages and visual usage
- glossary terms and business definition
- owner, steward, certification status, contract version, and effective date

Preserve DAX exactly. Keep explanatory language in a separate description field. Treat text-returning display measures and `_Color`, `_Arrow`, and `_HTML` measures as presentation logic rather than primary numeric metrics.

### 4. Map the contract to Alation

Use the Alation Data Product specification as the target shape:

- `product.productId` and semantic version
- `product.en` for name, description, business context, and example questions
- `product.recordSets` for the semantic-model or governed tabular interface
- `product.metadata.metrics` for reusable metrics
- `product.metadata.relationships` for joins and relationship assumptions
- `dataAccess` for access/documentation references

The native metric expression field is generic. Preserve Power BI semantics with explicit extensions such as:

```json
{
  "expression": "<exact DAX>",
  "x-expressionLanguage": "DAX",
  "x-powerBiTable": "<model table>",
  "x-formatString": "<format>",
  "x-transitiveDependencies": [],
  "x-sourceLineage": [],
  "x-visualUsageCount": 0,
  "x-certificationStatus": "<status>"
}
```

Keep a review-friendly CSV alongside the structured JSON. JSON is the machine contract; CSV is the steward review surface.

### 5. Complete the formal MCP/API design

Design the agent interface as a governed façade over the approved contract. Do not expose raw Power BI internals or unrestricted warehouse queries as the primary interface.

Recommended read tools:

- `search_metrics`
- `get_metric_definition`
- `get_metric_lineage`
- `get_metric_visual_usage`
- `get_join_context`
- `get_data_product_contract`
- `validate_metric_request`
- `get_metric_quality_status`

Every response should include the contract version, definition, source lineage, Alation references, ownership/certification state, freshness or reconciliation timestamp, and known limitations.

Document authentication, authorization, rate limits, audit logging, error states, versioning, deprecation, and human escalation.

### 6. Define the operating workflow

The repeatable lifecycle is:

1. Extract Power BI semantic-model and report evidence.
2. Generate the versioned metric contract.
3. Reconcile reports, visuals, datasource fields, and source paths.
4. Validate schema, required fields, lineage, and ownership.
5. Produce a steward review package.
6. Obtain approval for the contract version.
7. Publish approved metadata to Alation through a supported API.
8. Expose only approved content through MCP/API.
9. Run recurring reconciliation and change detection.
10. Route material changes back through steward review.

### 7. Define evidence and release gates

Use functional, quality, business, and governance evidence. A pilot is not complete until:

- all extracted measures validate against the schema
- exact DAX is preserved
- report visual references reconcile or are explicitly unresolved
- source lineage is documented or marked unresolved
- priority glossary mappings are approved
- owners and certification states are present or exceptioned
- MCP/API responses include contract version, lineage, and governance status
- unauthorized or uncertified content is blocked or clearly flagged
- contract changes produce a reviewable diff

### 8. Resolve API blockers before publication

For an Alation data-product URL, first test:

- the supported integration endpoint
- the Data Product Service schema endpoint
- the product retrieval endpoint using the API token
- the internal product ID or external product ID

If the schema is readable but product retrieval returns `401`, record the issue as an API authorization/endpoint-scope blocker. Do not substitute browser sign-in or guess a write endpoint.

## Required design artifacts

For a formal design review, produce:

1. Architecture Decision Record
2. Outcome alignment table
3. Critical capability map
4. Capability-to-tool alignment matrix
5. Metric contract schema and example payload
6. MCP/API tool and response definitions
7. Security and authorization model
8. Steward review and publication workflow
9. Evidence and evaluation plan
10. Release roadmap and decision log

Use `references/formal-design-package.md` for the required sections and acceptance criteria. Use `references/mcp-contract-pattern.md` for the recommended tool/response design.

## Project output conventions

Place working outputs under the project’s documentation directory:

- `agent-contract/` for machine and human metric contracts
- `lineage/` for source, report, visual, and dependency evidence
- `alation/` for live asset inventories and staged product payloads
- `design/` for ADRs, API schemas, security model, workflow, and roadmap
- `qfd/` for prioritization matrices and value demonstrations

Report counts, unresolved mappings, API blockers, and whether changes were staged or published. Never imply publication when only a local staging artifact exists.
