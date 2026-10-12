# Production gates

Production promotion requires all applicable gates below.

| Gate | Required evidence | Owner |
|---|---|---|
| Contract completeness | Validator passes; required fields populated | Analyst |
| DAX integrity | Exact DAX extracted from the semantic model | Power BI analyst |
| Lineage | Source paths and Alation object IDs reconciled or exceptioned | Data Governance |
| Visual impact | Report pages, visuals, fields, and aggregations recorded | Power BI analyst |
| Business meaning | Definitions and glossary terms reviewed | Business steward |
| Relationship safety | Joins, cardinality, filters, and grain documented | BI/data engineering |
| Access control | Power BI, Alation, and agent permissions validated | Platform/security |
| Agent readiness | JSON/MCP response tests pass and include citations/status | Agent/API owner |
| Steward approval | Contract state is `steward_approved` | Steward |
| Publication verification | Alation read-back and endpoint smoke test pass | Release owner |

Do not mark the contract `published` based only on a merged pull request. Publication must be verified in the target system.
