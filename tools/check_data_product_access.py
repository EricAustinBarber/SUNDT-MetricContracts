"""Run a read-only authorization diagnostic for Alation Data Products."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ALATION_ROOT = Path(r"C:\Users\eabarber\CodeX\Alation\alation")
DEFAULT_ENV = ALATION_ROOT / "alation_tools" / ".env"
sys.path.insert(0, str(ALATION_ROOT / "alation_tools" / "alation_tools"))
from config import load_powerbi_curation_config  # noqa: E402


def check(base: str, headers: dict[str, str], product_id: str) -> list[dict[str, object]]:
    paths = [
        ("product_schema", "/dps/api/v1/specs/product/"),
        ("products", "/dps/api/v1/data-product/"),
        ("target_product", f"/dps/api/v1/data-product/{product_id}/"),
        ("marketplaces", "/dps/api/v1/marketplace/"),
    ]
    results = []
    for name, path in paths:
        try:
            response = requests.get(base + path, headers=headers, timeout=30)
            results.append(
                {
                    "name": name,
                    "path": path,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "authorized": response.status_code not in (401, 403),
                    "body_preview": response.text[:160].replace("\n", " "),
                }
            )
        except requests.RequestException as exc:
            results.append({"name": name, "path": path, "status": None, "authorized": False, "error": str(exc)})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-id", default="group-health-dashboard")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    args = parser.parse_args()

    cfg = load_powerbi_curation_config(args.env_file)
    base = cfg.alation_url.rstrip("/")
    token = cfg.alation_api_token
    variants = {
        "TOKEN": {"TOKEN": token, "Accept": "application/json"},
        "Bearer": {"Authorization": f"Bearer {token}", "Accept": "application/json"},
        "X-Alation-Token": {"X-Alation-Token": token, "Accept": "application/json"},
    }
    report = {"product_id": args.product_id, "base_url": base, "variants": {}}
    for name, headers in variants.items():
        results = check(base, headers, args.product_id)
        report["variants"][name] = results
        statuses = ", ".join(f"{item['name']}={item['status']}" for item in results)
        print(f"{name}: {statuses}")

    token_results = report["variants"]["TOKEN"]
    product_result = next(item for item in token_results if item["name"] == "target_product")
    if product_result.get("status") in (401, 403):
        print("DECISION: Data Product Service authorization is not available to this token.")
        return 2
    if not product_result.get("authorized"):
        print("DECISION: target Data Product could not be read.")
        return 1
    print("DECISION: target Data Product endpoint is readable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
