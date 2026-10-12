# Supported Alation operating model

## Architecture

The repository is the versioned source of truth for the Power BI metric
contract. Standard Alation catalog APIs are the searchable documentation and
asset-navigation layer. The local MCP/API read layer exposes the governed
contract to agents.

The Alation Data Product Service is not part of the current publication path.
The tenant's Data Product schema endpoint is reachable, but product,
marketplace, and permission endpoints reject the available API token with
HTTP 401. Do not use browser authentication or edit Power BI files as a
workaround.

## Supported workflow

1. Extract or update the Power BI contract in
   `contracts/group-health-dashboard/<version>.json`.
2. Validate the contract:

   ```powershell
   python tools/validate_all_contracts.py
   ```

3. Review the exact DAX, source paths, Alation object IDs, relationships,
   visual usage, glossary terms, and review status in the contract.
4. Run the Alation publication adapter in dry-run mode:

   ```powershell
   python tools/publish_alation_contract.py `
     --contract contracts/group-health-dashboard/0.1.0.json `
     --asset bi_report:1785:"group-Group Health" `
     --asset bi_datasource:1355:"swa-dataset-project-controls-management-deathstar-pilot" `
     --asset bi_datasource:1895:"swa-dataset-project-controls-management-executive"
   ```

5. After review, add `--apply`. The adapter only appends a navigation pointer
   to the Description custom field on the explicitly supplied Alation assets;
   it does not modify Power BI files, semantic models, warehouse objects, or
   Data Product records.
6. Run the agent read-layer tests:

   ```powershell
   python tools/test_contract_read_layer.py
   ```

7. Serve the approved contract through the governed MCP/API interface.

## Current Group Health state

- Contract: `group-health-dashboard` version `0.1.0`
- Power BI metrics: 316
- Power BI relationships: 89
- Report asset: Alation BI report `1785`
- Semantic model assets: Alation BI datasources `1355` and `1895`
- Contract pointers: present on all three assets
- Data Product payload: validated and staged separately; not published through
  the unavailable Data Product Service API

## Governance boundary

Git pull-request review controls contract changes. Alation descriptions point
users and agents to the approved contract. The contract read layer must serve
only a validated contract version and must retain the publication/read audit.
