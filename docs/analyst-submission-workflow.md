# Analyst submission workflow

## Before development

Create the product folder and contract version before the semantic model is submitted to production:

```text
contracts/<product-id>/<major>.<minor>.<patch>.json
```

The analyst should identify the intended report, semantic model, owner, steward, business purpose, expected grain, and known source systems.

## During semantic-model development

Maintain the contract as metrics are created. Do not wait until the end of the project. For every metric:

1. Copy the exact DAX expression.
2. State the metric role.
3. State the valid grain and aggregation rule.
4. List direct and transitive dependencies.
5. Identify source paths and Alation objects.
6. Record report and visual usage.
7. Add glossary terms and a business definition.
8. Record owner, steward, and review status.

## Before production submission

Run the local validator and complete the pull-request checklist:

- Contract version is valid.
- All metric IDs are stable and unique.
- No DAX placeholders remain.
- All metrics specify grain and aggregation behavior.
- Presentation-only measures are labeled correctly.
- Source lineage is matched or explicitly unresolved.
- Report visual usage is reconciled or explicitly unresolved.
- Relationships and join assumptions are documented.
- Owner and steward are assigned.
- Known limitations are documented.
- No secrets, raw extracts, PBIX/PBIT files, or production data are committed.

## Review sequence

1. Analyst self-check
2. Power BI peer review
3. Data Governance / steward review
4. Alation/API publication review
5. Production promotion approval

## Change management

- Major version: changes metric meaning, grain, source, or aggregation behavior.
- Minor version: adds metrics or non-breaking metadata.
- Patch version: fixes descriptions, owners, links, or documentation.

Every major or minor change should include downstream report impact and agent/API impact.
