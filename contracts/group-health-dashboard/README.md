# Group Health Dashboard contract

This is the first contract generated from the Group Health Power BI semantic-model evidence.

## Current state

- Contract version: `0.1.0`
- State: `submitted`
- Measures: 316
- Report visuals: 192
- Chart/KPI field references: 194
- Live datasource field reconciliation: 194 matched
- Steward approval: pending
- Alation publication: not performed

The JSON contract is generated from the project metric contract. Before publication, attach the approved report and semantic-model asset IDs, glossary mappings, relationship definitions, steward identity, and final certification state.

## DAX provenance evidence

The per-measure evidence manifest is [group-health-dax-evidence.csv](../../evidence/group-health-dax-evidence.csv).
It links every contract metric to:

- the extracted `semantic-model-documentation/inventories/measures.csv` row;
- the Power BI lineage tag captured during extraction;
- the raw `DataModelSchema.json` measure-name location;
- the production source path, when reconciled; and
- SHA-256 hashes proving the contract DAX and extracted inventory DAX match.

The current manifest reports an exact DAX match for all 316 metrics. The raw
Power BI evidence is retained in the sibling `semantic-model-documentation`
directory and was not modified by this contract project.

Each metric also carries a `powerBiAssetRefs` object in the JSON contract. For
this release, it records dataset `1355` as the DAX extraction source, report
`1785` as the consuming report, and dataset `1895` as the reconciled semantic
model identity. This preserves the distinction between where the expression
was extracted and which deployed report/dataset it serves.

Each metric also carries `deploymentPath`, including the report page, visual
ID, visual title/type, field reference, model table, measure name, and edit
directions when the measure is referenced by the extracted report layout. The
current report inventory contains 194 field references across 192 visuals; 31
of the 316 measures have direct visual references in this contract release.
Measures without a direct visual reference remain valid semantic-model
measures and may be consumed indirectly by other measures or report logic.
