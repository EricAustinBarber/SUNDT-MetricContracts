# Existing Data Product merge plan

The exported `dataproduct_export/group-health-dashboard.yaml` is an existing
curated Data Product, not an empty target. The export contains 62 Databricks
record sets, 21 existing metrics, 7 existing relationships, and a Databricks
delivery system.

The merge builder preserves those objects and adds the Power BI contract:

- 316 exact-DAX Power BI metrics under `product.metadata.metrics`.
- A `powerbi_semantic_model` record set with 316 metric fields.
- A Power BI delivery system pointing to the Group Health report.
- 89 Power BI relationships under `metadata.x-powerBiRelationships`.
- Power BI asset IDs and contract version under `x-*` metadata.

The existing export is never edited. Build a candidate update with:

```powershell
python tools/merge_contract_into_data_product.py `
  --source-yaml dataproduct_export/group-health-dashboard.yaml `
  --contract contracts/group-health-dashboard/0.1.0.json `
  --output-json build/group-health-dashboard-data-product-update-1.1.0.json `
  --output-yaml build/group-health-dashboard-data-product-update-1.1.0.yaml `
  --repository-url https://github.com/EricAustinBarber/SUNDT-MetricContracts/blob/main/contracts/group-health-dashboard/0.1.0.json
```

Version `1.1.0` represents an additive Data Product update. The embedded
Power BI contract remains identified separately as `x-contractVersion: 0.1.0`.
This candidate must be reviewed and validated before the guarded create/update
adapter submits it to Alation.

Validate preservation and embedding with:

```powershell
python tools/validate_merged_data_product.py `
  --source-yaml dataproduct_export/group-health-dashboard.yaml `
  --contract contracts/group-health-dashboard/0.1.0.json `
  --merged build/group-health-dashboard-data-product-update-1.1.0.json
```
