"""Publish a reviewed Power BI contract pointer to Alation BI assets.

The default operation is a dry run.  This adapter deliberately publishes only
the contract pointer to existing Alation Power BI asset descriptions.  It does
not modify Power BI files, semantic models, tables, or Data Product records.

The Data Product Service is intentionally handled as a separate future adapter
because its endpoint currently returns 401 for the available API token.

Example:
    python tools/publish_alation_contract.py \
      --contract contracts/group-health-dashboard/0.1.0.json \
      --asset bi_report:1785:"group-Group Health" \
      --asset bi_datasource:1355:"swa-dataset-project-controls-management-deathstar-pilot" \
      --asset bi_datasource:1895:"swa-dataset-project-controls-management-executive"

Add ``--apply`` only after the dry-run output has been reviewed.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ALATION_ROOT = Path(r"C:\Users\eabarber\CodeX\Alation\alation")
DEFAULT_ENV = ALATION_ROOT / "alation_tools" / ".env"
DESCRIPTION_FIELD_ID = 4

sys.path.insert(0, str(ALATION_ROOT / "alation_tools" / "alation_tools"))
from api import AlationClient  # noqa: E402
from config import load_powerbi_curation_config  # noqa: E402


def parse_asset(value: str) -> dict[str, object]:
    """Parse ``otype:oid:name`` while allowing colons in the display name."""
    parts = value.split(":", 2)
    if len(parts) != 3 or not parts[0] or not parts[1] or not parts[2]:
        raise argparse.ArgumentTypeError(
            "asset must use otype:oid:name, for example bi_report:1785:group-Group Health"
        )
    try:
        oid = int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("asset oid must be an integer") from exc
    return {"otype": parts[0], "oid": oid, "name": parts[2]}


def load_contract(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Could not read contract {path}: {exc}") from exc


def validate_contract(path: Path) -> None:
    tools_dir = path.parents[2] / "tools"
    sys.path.insert(0, str(tools_dir))
    from validate_contract import validate  # noqa: PLC0415

    errors = validate(path)
    if errors:
        raise RuntimeError("Contract validation failed:\n- " + "\n- ".join(errors))


def strip_html(value: str) -> str:
    return html.unescape(value or "").replace("<p>", "").replace("</p>", " ").strip()


def pointer_html(contract: dict, repo_url: str) -> str:
    product = contract["product"]
    metrics = contract.get("metrics", [])
    status = contract.get("contractStatus", "unknown")
    version = contract.get("contractVersion", "unknown")
    return (
        f"<p><strong>Power BI data contract:</strong> {html.escape(product['productId'])} "
        f"v{html.escape(version)}. Contract state: {html.escape(status)}.</p>"
        f"<p>The contract covers {len(metrics)} metrics and preserves exact DAX, model dependencies, "
        "report usage, source paths, and agent/API governance fields.</p>"
        f"<p><strong>Contract repository:</strong> <a href=\"{html.escape(repo_url, quote=True)}\">"
        f"{html.escape(repo_url)}</a></p>"
    )


def get_description(client: AlationClient, otype: str, oid: int) -> str:
    payload = client.get(
        "/integration/v2/custom_field_value/",
        params={"field_id": DESCRIPTION_FIELD_ID, "otype": otype, "oid": str(oid)},
    )
    if not isinstance(payload, list):
        return ""
    values = [str(item.get("value", "")) for item in payload if isinstance(item, dict)]
    return next((value for value in values if value), "")


def write_description(client: AlationClient, cfg, target: dict, value: str) -> requests.Response:
    url = cfg.alation_url.rstrip("/") + "/integration/v2/custom_field_value/"
    return requests.put(
        url,
        headers=client.auth_headers(),
        json=[
            {
                "field_id": DESCRIPTION_FIELD_ID,
                "otype": target["otype"],
                "oid": target["oid"],
                "value": value,
            }
        ],
        timeout=60,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--asset", type=parse_asset, action="append", required=True)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument(
        "--repo-url",
        default="https://github.com/EricAustinBarber/SUNDT-MetricContracts/blob/main/contracts/group-health-dashboard/0.1.0.json",
    )
    parser.add_argument("--audit", type=Path, default=None)
    parser.add_argument("--apply", action="store_true", help="Write pointers and verify them")
    args = parser.parse_args()

    contract_path = args.contract.resolve()
    validate_contract(contract_path)
    contract = load_contract(contract_path)
    cfg = load_powerbi_curation_config(args.env_file)
    client = AlationClient(cfg)
    pointer = pointer_html(contract, args.repo_url)
    audit_path = args.audit or contract_path.parents[2] / "publication-audit" / "alation-contract-pointer.csv"
    rows: list[dict[str, object]] = []

    print(f"Contract valid: {contract_path}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY_RUN'}")
    for target in args.asset:
        row: dict[str, object] = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "contract": str(contract_path),
            "contract_version": contract.get("contractVersion", ""),
            "otype": target["otype"],
            "oid": target["oid"],
            "name": target["name"],
            "status": "",
            "detail": "",
        }
        try:
            existing = get_description(client, str(target["otype"]), int(target["oid"]))
            if f"{contract['product']['productId']} v{contract['contractVersion']}" in existing:
                row["status"] = "ALREADY_PRESENT"
                row["detail"] = "Contract pointer already exists."
            elif not args.apply:
                row["status"] = "DRY_RUN_READY"
                row["detail"] = f"Would append pointer; existing description length={len(strip_html(existing))}."
            else:
                response = write_description(client, cfg, target, existing + pointer)
                if response.status_code not in (200, 201):
                    row["status"] = "ERROR"
                    row["detail"] = f"HTTP {response.status_code}: {response.text[:500]}"
                else:
                    verified = get_description(client, str(target["otype"]), int(target["oid"]))
                    row["status"] = "UPDATED_VERIFIED" if pointer in verified else "UPDATED_NOT_VERIFIED"
                    row["detail"] = f"HTTP {response.status_code}; read-back length={len(verified)}."
        except Exception as exc:
            row["status"] = "ERROR"
            row["detail"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
        print(f"{target['otype']} {target['oid']} {row['status']}: {row['detail']}")

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Audit: {audit_path}")
    return 1 if any(row["status"] in {"ERROR", "UPDATED_NOT_VERIFIED"} for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
