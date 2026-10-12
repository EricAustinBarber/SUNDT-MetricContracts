# Formal design package

Use this reference when the project moves from discovery or QFD prioritization into architecture and implementation approval.

## 1. Architecture Decision Record

Document:

- Decision: MCP/API façade over an approved Alation data-product contract
- Power BI role: authoritative DAX and report-semantic source
- Alation role: catalog, governance, ownership, certification, glossary, lineage, and data-product boundary
- Agent-layer role: governed discovery, explanation, lineage, validation, and chart-context access
- Alternatives considered: direct Power BI access, direct warehouse access, Alation-only prose, unmanaged custom API
- Rejected alternatives and reasons
- Security and operational consequences
- Review date and decision owner

## 2. Outcome alignment

Use this structure:

| Goal | Outcome | Measure | Users | Owner | Deadline |
|---|---|---|---|---|---|
| Governed agent analytics | Agents can explain and chart approved metrics with traceable definitions | Contract coverage, citation coverage, reconciliation rate | Analysts, stewards, agents | Data Governance / BI | TBD |

Keep outcomes tool-independent. The MCP choice belongs in the capability-to-tool alignment, not the outcome statement.

## 3. Capability map

Minimum capabilities:

- Power BI semantic extraction
- Metric contract normalization
- Report and visual usage discovery
- Source and lineage reconciliation
- Glossary and business-language mapping
- Relationship and join documentation
- Alation product publication
- Agent/MCP contract exposure
- Access control and audit logging
- Version and change management
- Steward approval and exception handling
- Quality, freshness, and adoption monitoring

## 4. API/MCP design sections

For every tool define:

- name and purpose
- caller authorization
- required inputs
- input validation
- response schema
- source references
- freshness semantics
- errors and fallback
- audit fields
- rate and quota rules
- version/deprecation policy

Minimum response envelope:

```json
{
  "contractVersion": "0.1.0",
  "asOf": "<ISO timestamp>",
  "result": {},
  "sources": [],
  "governance": {
    "owner": "",
    "steward": "",
    "certificationStatus": "",
    "accessDecision": "allowed|blocked|review"
  },
  "limitations": []
}
```

## 5. Security design

Specify:

- service-principal or agent identity model
- token scope and rotation
- least-privilege Alation access
- Power BI and warehouse permission propagation
- row/column security behavior
- sensitive metric handling
- audit event fields
- blocked, uncertified, stale, or unresolved behavior
- human escalation path

## 6. Publication workflow

Publication requires:

1. Contract generation
2. Schema validation
3. Reconciliation checks
4. Steward review
5. Version approval
6. API publication
7. Read-back verification
8. MCP/API smoke tests
9. Evidence capture

Separate `staged`, `approved`, `published`, and `retired` states. A local JSON file is not proof of publication.

## 7. Pilot acceptance criteria

For Group Health, use the current evidence baseline:

- 316 measures
- 192 report visuals
- 194 chart/KPI field-reference rows
- 194 live datasource field matches
- 18 production source paths represented in source-lineage evidence
- reports 1785 and 1787 identified
- semantic models/datasources 1355 and 1895 identified

Acceptance criteria should require exact DAX preservation, stable asset IDs, explicit unresolved mappings, governance fields, and read-back verification after publication.

## 8. Release roadmap

### Release 0: Design and contract validation

- approve architecture
- resolve API access
- validate contract schema
- confirm steward review package

### Release 1: Group Health read-only pilot

- publish or register approved contract
- expose metric lookup and lineage tools
- test analyst and agent questions
- capture audit evidence

### Release 2: Governance automation

- scheduled Power BI extraction
- version diffing
- change impact analysis
- ownership/certification checks
- publication workflow automation

### Release 3: Scale-out

- additional Power BI models and reports
- shared glossary and join patterns
- agent usage analytics
- trust and quality scoring

