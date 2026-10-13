# Group Health Power BI → Alation Project Resume Summary

## Objective

Create a governed, agent-ready metric contract documenting:

```text
Power BI report → page/visual → measure reference → semantic-model table → DAX → upstream source
```

The contract supports Alation catalog documentation, future Data Product publication, and MCP/API agent consumption.

## Repository

- GitHub: <https://github.com/EricAustinBarber/SUNDT-MetricContracts>
- Local: `C:\Users\eabarber\CodeX\Alation\DataProductsDudiligence\GroupHealth\dashboards\powerbi-data-contract-repo`
- Latest commit: `dfe8a33 Require Power BI metric deployment paths in skill`

## Current contract

Primary contract:

`contracts/group-health-dashboard/0.1.0.json`

It contains 316 Power BI measures with exact DAX, dependencies, model tables and columns, source lineage, Power BI asset references, report/page/visual references where available, edit directions, and review metadata.

## Power BI / Alation asset mapping

- Report `1785`: `group-Group Health`
- Datasource `1355`: `swa-dataset-project-controls-management-deathstar-pilot`
- Datasource `1895`: `swa-dataset-project-controls-management-executive`

Each metric identifies the DAX extraction model, consuming report, reconciled semantic model, model table, measure name, and visual deployment path when directly referenced.

The report inventory contains 192 visuals and 194 field references. Thirty-one measures currently have direct visual references; other measures may be indirect, unused, or referenced by other measures.

## DAX evidence

Evidence manifest:

`evidence/group-health-dax-evidence.csv`

It links each metric to the extracted `measures.csv` row, raw `DataModelSchema.json` location, Power BI lineage tag, source path, and DAX hashes.

Validation result:

```text
316 metrics
316 exact DAX matches
0 mismatches
```

## Existing Alation Data Product

The exported Data Product contains 21 native metrics. The staged merged candidate contains 337 total metrics: 316 Power BI metrics and 21 existing Data Product metrics.

Merged candidate:

`build/group-health-dashboard-data-product-update-1.1.0.json`

It also contains 63 recordsets, 7 native relationships, and 89 Power BI relationships.

## Alation status

Contract navigation pointers are verified on report `1785` and datasources `1355` and `1895`.

The standard Alation catalog API works for descriptions and navigation pointers. The Data Product Service API remains blocked: the normal Alation token works for catalog APIs and the product schema endpoint, but product, marketplace, and permission endpoints return HTTP 401. This is a Data Product Service authentication/session limitation, not a feature-toggle issue.

## Skill

Skill location:

`skills/powerbi-metric-contract`

The skill requires exact DAX, dependencies, source lineage, report/page/visual usage, stable visual IDs, dataset/report asset IDs, edit directions, and treatment of indirectly used or unreferenced measures.

## Validation commands

Run from the repository root:

```powershell
python tools\validate_contract.py contracts\group-health-dashboard\0.1.0.json
python tools\test_contract_read_layer.py
python skills\powerbi-metric-contract\scripts\build_metric_contract.py
```

## Recommended next phase

1. Review the 316-metric contract and evidence manifest.
2. Resolve remaining metric-to-visual gaps.
3. Add Alation object IDs for matched source tables and columns.
4. Add glossary terms, ownership, certification, and business definitions.
5. Continue using standard Alation catalog descriptions for discoverability.
6. Keep the Data Product payload staged until Data Product Service access is available.
7. Expose the approved contract through the MCP/API read layer for agents.
