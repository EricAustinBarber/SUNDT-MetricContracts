# Power BI Data Contract Repository

This repository is the pre-production contract boundary for Power BI semantic models and reports.

Power BI analysts use it to submit a versioned contract before a model or report is promoted to production. Data Governance and BI stewards use the same contract to verify metric definitions, lineage, report usage, ownership, and agent/API readiness.

## Outcome

Every production Power BI model should have a reviewable contract that answers:

- What does each metric mean?
- What exact DAX creates it?
- What are its grain and aggregation rules?
- Which tables, columns, and source paths feed it?
- Which reports and visuals consume it?
- Which glossary terms and joins apply?
- Who owns and certifies it?
- Can an agent safely use it to answer or chart a question?

## Repository layout

```text
contracts/       Submitted semantic-model contracts
schemas/         Machine-readable contract schemas
templates/       Analyst starter templates
examples/        Sanitized examples
docs/            Workflow, governance, and design guidance
tools/           Local validation utilities
```

## Analyst workflow

1. Copy `templates/powerbi-alation-contract.template.json` into `contracts/<product-id>/<version>.json`.
2. Extract the Power BI semantic model and report layout.
3. Complete the metric, lineage, visual-usage, relationship, ownership, and quality sections.
4. Run the validator:

   ```powershell
   python tools/validate_contract.py contracts/<product-id>/<version>.json
   ```

5. Open a pull request using the review checklist.
6. Resolve validation and steward review findings.
7. Promote the approved version to Alation and the agent/API registry through the controlled publication workflow.

## Contract states

`draft` → `submitted` → `validated` → `steward_approved` → `published` → `retired`

The repository is not the production catalog. A merged contract means the definition is approved for publication; it does not prove that Alation or the MCP/API endpoint has been updated.

## Design principles

- Preserve exact DAX. Do not replace DAX with a paraphrase.
- Keep presentation-only measures separate from primary numeric metrics.
- Never invent unresolved lineage or glossary mappings.
- Treat report usage as impact-analysis evidence.
- Use semantic versioning for contract changes.
- Keep Power BI files and production tables unedited by the contract process.
- Do not store tokens, passwords, exported sensitive data, or production extracts in Git.
