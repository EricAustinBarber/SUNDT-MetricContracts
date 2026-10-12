# Repository operating model

## Boundary decision

The reusable skill and the governed data contracts have separate homes.

| Boundary | System of record | Purpose |
|---|---|---|
| Power BI semantic model | Power BI artifact and workspace | Authoritative DAX, model relationships, report layouts, and visual definitions |
| Contract repository | Git repository | Versioned contract, review history, validation, ownership, and approval state |
| Published governance metadata | Alation | Catalog assets, glossary, lineage, stewardship, certification, and data-product representation |
| Agent runtime | MCP/API registry | Runtime projection of approved contract content |
| Secrets | Secret/configuration store | Tokens, service principals, and connection configuration |

## What belongs in this repository

- Contract JSON files
- Contract schema and templates
- Sanitized examples
- Validation and extraction tooling
- Evidence manifests and review notes
- Architecture and publication documentation

## What does not belong in this repository

- PBIX or PBIT files
- Raw data extracts
- Passwords, API tokens, or service-principal credentials
- Production query results containing sensitive data
- Unreviewed generated files presented as approved contracts

## Ownership

- Power BI analyst: maintains model definition, DAX, grain, aggregation, visuals, and technical lineage.
- BI peer reviewer: verifies model behavior and downstream report impact.
- Data steward: approves business meaning, glossary alignment, ownership, and certification.
- Data Governance: maintains schema, validation rules, review gates, and publication evidence.
- Platform/API owner: operates Alation publication and MCP/API exposure.

## Branch and release model

- `main`: approved contracts only.
- Feature branch: analyst changes for a model or contract version.
- Pull request: required validation and review evidence.
- Release tag: published contract version, such as `group-health-dashboard-v0.1.0`.

Configure branch protection and CODEOWNERS after the repository is moved to the Sundt-hosted Git service.
