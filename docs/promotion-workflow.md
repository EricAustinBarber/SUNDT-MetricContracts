# Contract promotion workflow

## State flow

```text
draft → submitted → validated → steward_approved → published → retired
```

## Step 1: Analyst preparation

The analyst creates or refreshes the contract from the Power BI semantic model and report layout. The contract must preserve exact DAX and identify the model, report, source lineage, visual usage, relationships, ownership, and known limitations.

## Step 2: Local validation

Run:

```powershell
python tools/validate_all_contracts.py
```

The validator checks semantic versioning, required product fields, stable metric IDs, exact DAX presence, grain, aggregation, lineage state, usage counts, ownership, and review state.

## Step 3: Pull request review

The pull request must include:

- contract version and change type
- Power BI report and semantic-model IDs
- metric count and changed metric count
- source-lineage changes
- downstream visual impact
- glossary and relationship changes
- known limitations
- validation output

Required reviewers are a Power BI peer and the assigned data steward. Data Governance reviews schema or workflow changes.

## Step 4: Approval and merge

The contract may be merged only when validation passes and required reviewers approve. Merging is approval of the contract source; it is not proof of Alation publication.

## Step 5: Controlled publication

An authorized publication job or operator:

1. Reads the merged contract.
2. Verifies the target Alation product and asset IDs.
3. Publishes the approved version using an API service identity.
4. Reads the product and asset metadata back from Alation.
5. Records the publication response and contract version.
6. Runs MCP/API smoke tests.

If the target product cannot be read with the API token, publication stops. Do not use browser sign-in as a workaround for an API-only process.

For the current Group Health implementation, run the repository publication
adapter in dry-run mode first, then repeat with `--apply` only after steward
approval. See `docs/alation-publication-adapter.md`. The adapter updates and
verifies only the contract pointer on explicitly identified Power BI assets;
Data Product Service publication remains a separate gated step.

## Step 6: Runtime release

The MCP/API layer may expose a contract only after publication read-back succeeds. Responses must identify the contract version and governance state.
