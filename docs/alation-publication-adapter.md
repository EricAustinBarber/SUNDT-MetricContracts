# Alation publication adapter

The publication adapter is the controlled bridge from a merged contract to
the existing Alation Power BI assets. It currently updates only the Alation
Description custom field on explicitly supplied asset IDs.

## Dry run

Run from the repository root:

```powershell
python tools/publish_alation_contract.py `
  --contract contracts/group-health-dashboard/0.1.0.json `
  --asset bi_report:1785:"group-Group Health" `
  --asset bi_datasource:1355:"swa-dataset-project-controls-management-deathstar-pilot" `
  --asset bi_datasource:1895:"swa-dataset-project-controls-management-executive"
```

The command validates the contract, reads the current descriptions, reports
what would change, and writes a CSV audit. It does not update Alation.

## Apply and verify

After steward approval and review of the dry-run audit, add `--apply`:

```powershell
python tools/publish_alation_contract.py ... --apply
```

The adapter writes the pointer, reads the description back, and reports
`UPDATED_VERIFIED` only when the contract pointer is present after the write.

## Boundary

The adapter does not publish to the Alation Data Product Service. That service
must be implemented as a separate, schema-driven adapter after the service
accepts the API token. A `401` response is a hard stop; browser sign-in and
Power BI file edits are not fallbacks.

The repository contract remains the source of truth. Alation descriptions are
navigation pointers and publication evidence, not a replacement for the
versioned contract.
