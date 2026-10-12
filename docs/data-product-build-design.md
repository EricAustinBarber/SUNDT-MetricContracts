# Data Product build design

## Design decision

The metric contract is included during the Data Product build. The Git
repository is the versioned source of truth; the Alation Data Product is the
approved, discoverable runtime projection used by agents and governed users.

```text
Power BI semantic model + report layout
        ↓
metric_contract.json
        ↓ pull request, validation, steward approval
Power BI-Alation contract JSON
        ↓ offline schema-shaped build
Alation Data Product Specification payload
        ↓ API publication after authorization
Alation Data Product
        ↓ read-back and smoke tests
MCP/API metric discovery and chart planning
```

## Where each concern belongs

| Concern | Contract location | Data Product location |
|---|---|---|
| Exact DAX | `metrics[].daxExpression` | `product.metadata.metrics[id].expression` |
| DAX language | `metrics[].expressionLanguage` | `x-expressionLanguage` |
| Model table and role | `modelTable`, `role` | `x-powerBiTable`, `x-powerBiRole` |
| Grain and aggregation | `grain`, `aggregationRule` | `x-grain`, `x-aggregationRule` |
| Source lineage | `lineage.sourcePaths`, `alationObjectIds` | `x-sourceLineage`, `x-alationObjectIds` |
| Report consumption | `usage.referenceCount`, `usage.visuals` | `x-visualUsageCount`, `x-visualUsage` |
| Semantic model surface | `assets.semanticModels` | `product.recordSets` |
| Power BI joins | `relationships[]` | `metadata.x-powerBiRelationships` |
| Glossary and review state | `glossaryTerms`, `review` | `x-glossaryTerms`, `x-reviewStatus` |

The current model contains 316 metrics and 89 Power BI relationships. Native
Data Product relationship records remain empty until cardinality and
nullability are steward-validated. The raw Power BI joins are retained so
agents can see the actual model relationship evidence without fabricated SQL
join semantics.

## API authorization gate

The available API token currently passes normal catalog API calls and reads the
Data Product specification schemas, but receives `401 Session and Token
validation failed` for Data Product product and marketplace instances. This
means the Data Product Service is not accepting this credential as a valid
service session, even though the token identity is `server_admins` / `is_admin`.

The tenant's Data Product OpenAPI document is available at
`/dps/api/v1/openapi.json`. It documents the product routes under
`/api/v1/data-product/` and the permission routes under
`/api/v1/data-products/`. Its 401 response describes an invalid or unavailable
Alation session, so this is now an authentication/session integration issue,
not a missing product feature or missing standard catalog administrator role.

Authorization must be validated with these read-only checks:

1. `GET /dps/api/v1/specs/product/` returns the specification schema.
2. `GET /dps/api/v1/data-product/` returns a successful authorized response.
3. `GET /dps/api/v1/data-product/{productId}/` returns the target product.
4. `GET /dps/api/v1/data-products/permissions/`,
   `/user-permissions/`, and `/check-permissions/` are reachable with the
   same service identity.
5. The returned product ID is confirmed to be `group-health-dashboard`.
6. A publication service identity can read the product after publication.

Run the repository diagnostic with:

```powershell
python tools/check_data_product_access.py --product-id group-health-dashboard
```

Exit code `2` means the target product endpoint returned `401` or `403` and
the service identity needs a valid Data Product Service session or permission.
The diagnostic also checks the documented permission routes and never attempts
a Data Product write.

Testing alternate header formats does not replace a Data Product Service
session. If all supported headers return 401, the next technical question for
Alation support is which API-only session or OAuth flow is supported for the
Data Product Service. Do not change the contract or use browser authentication
as a workaround.

## Publication sequence after authorization

1. Run `tools/validate_all_contracts.py`.
2. Build `build/group-health-data-product-0.1.0.json`.
3. Run `tools/validate_data_product_payload.py` and validate the payload
   against the retrieved Alation schema. The repository validator reconciles
   every metric's exact DAX and every extracted relationship; a full JSON Schema
   package can be added to CI when dependency management is approved.
4. Resolve and read the target product.
5. Perform a dry-run diff against the existing product.
6. Publish only the approved version.
7. Read the product back and verify metric count, representative DAX, asset IDs,
   lineage fields, joins, and contract version.
8. Record the response in an immutable publication audit.
9. Enable the MCP/API read layer only for a successfully read-back version.

The guarded implementation is:

```powershell
python tools/publish_data_product.py `
  --payload build/group-health-data-product-0.1.0.json
```

This first reads the target product. A `200` produces an update plan, a `404`
produces a create plan, and a `401`/`403` stops with
`AUTHORIZATION_REQUIRED`. Add `--apply` only after the target read and dry-run
plan have been approved.

The current repository does steps 1 and 2 offline and has completed the
Power BI asset pointer integration. Step 3 requires a schema validator; steps
4–8 require Data Product Service authorization.
