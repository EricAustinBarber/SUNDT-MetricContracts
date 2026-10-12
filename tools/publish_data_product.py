"""Create or update an Alation Data Product from a validated contract payload.

The default mode is read-only. The adapter will not create or update a product
unless the target can first be resolved and ``--apply`` is explicitly passed.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ALATION_ROOT = Path(r"C:\Users\eabarber\CodeX\Alation\alation")
DEFAULT_ENV = ALATION_ROOT / "alation_tools" / ".env"


def load_config(env_file: Path):
    import sys

    sys.path.insert(0, str(ALATION_ROOT / "alation_tools" / "alation_tools"))
    from config import load_powerbi_curation_config  # noqa: PLC0415

    return load_powerbi_curation_config(env_file)


def request(cfg, method: str, path: str, payload: dict | None = None) -> requests.Response:
    headers = {"TOKEN": cfg.alation_api_token, "Accept": "application/json", "Content-Type": "application/json"}
    url = cfg.alation_url.rstrip("/") + path
    return requests.request(method, url, headers=headers, json=payload, timeout=60)


def merge_product(existing: dict, candidate: dict) -> dict:
    """Preserve existing product metadata while replacing governed contract fields."""
    merged = dict(existing)
    merged.update(candidate)
    for key in ("en", "recordSets", "metadata"):
        if isinstance(existing.get(key), dict) and isinstance(candidate.get(key), dict):
            combined = dict(existing[key])
            combined.update(candidate[key])
            merged[key] = combined
    return merged


def verify_product(response_payload: dict, expected: dict) -> list[str]:
    errors: list[str] = []
    product = response_payload.get("product", response_payload)
    expected_product = expected.get("product", {})
    if product.get("productId") != expected_product.get("productId"):
        errors.append("productId mismatch")
    if product.get("version") != expected_product.get("version"):
        errors.append("version mismatch")
    actual_metrics = product.get("metadata", {}).get("metrics", {})
    expected_metrics = expected_product.get("metadata", {}).get("metrics", {})
    if set(actual_metrics) != set(expected_metrics):
        errors.append(f"metric ID mismatch: expected {len(expected_metrics)}, got {len(actual_metrics)}")
    for metric_id in list(expected_metrics)[:3]:
        if actual_metrics.get(metric_id, {}).get("expression") != expected_metrics[metric_id].get("expression"):
            errors.append(f"DAX mismatch for representative metric {metric_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--product-id", default="group-health-dashboard")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--audit", type=Path, default=None)
    parser.add_argument("--apply", action="store_true", help="Write only after target resolution succeeds")
    parser.add_argument("--update-method", choices=("PUT", "PATCH"), default="PUT")
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    expected_product = payload["product"]
    if expected_product.get("productId") != args.product_id:
        raise SystemExit("payload productId does not match --product-id")
    cfg = load_config(args.env_file)
    base_path = "/dps/api/v1/data-product/"
    target_path = base_path + args.product_id + "/"
    audit_path = args.audit or args.payload.parent / "publication-audit" / f"{args.product_id}-{expected_product.get('version', 'unknown')}.json"
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "productId": args.product_id,
        "version": expected_product.get("version"),
        "mode": "apply" if args.apply else "dry_run",
        "payload": str(args.payload.resolve()),
        "status": "",
        "detail": "",
        "targetReadStatus": None,
        "writeStatus": None,
        "readBackStatus": None,
    }

    target_response = request(cfg, "GET", target_path)
    result["targetReadStatus"] = target_response.status_code
    if target_response.status_code == 200:
        try:
            existing = target_response.json()
        except ValueError:
            result["status"] = "ERROR"
            result["detail"] = "Target returned non-JSON content."
            existing = {}
        operation = "update"
        operation_path = target_path
        operation_method = args.update_method
        outbound = dict(payload)
        outbound["product"] = merge_product(existing.get("product", existing), expected_product)
    elif target_response.status_code == 404:
        operation = "create"
        operation_path = base_path
        operation_method = "POST"
        outbound = payload
    elif target_response.status_code in (401, 403):
        result["status"] = "AUTHORIZATION_REQUIRED"
        result["detail"] = "Target Data Product is not readable; no create or update was attempted."
        print(f"{result['status']}: target read returned HTTP {target_response.status_code}")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"audit={audit_path}")
        return 2
    else:
        result["status"] = "TARGET_READ_ERROR"
        result["detail"] = f"Target read returned HTTP {target_response.status_code}: {target_response.text[:300]}"
        print(f"{result['status']}: {result['detail']}")
        return 1

    result["operation"] = operation
    result["operationPath"] = operation_path
    result["operationMethod"] = operation_method
    result["expectedMetricCount"] = len(expected_product.get("metadata", {}).get("metrics", {}))
    if not args.apply:
        result["status"] = "DRY_RUN_READY"
        result["detail"] = "Target resolved; no Data Product write was attempted."
    else:
        write_response = request(cfg, operation_method, operation_path, outbound)
        result["writeStatus"] = write_response.status_code
        if write_response.status_code not in (200, 201, 202, 204):
            result["status"] = "WRITE_ERROR"
            result["detail"] = f"Write returned HTTP {write_response.status_code}: {write_response.text[:500]}"
        else:
            read_back = request(cfg, "GET", target_path)
            result["readBackStatus"] = read_back.status_code
            if read_back.status_code != 200:
                result["status"] = "READ_BACK_ERROR"
                result["detail"] = f"Read-back returned HTTP {read_back.status_code}."
            else:
                errors = verify_product(read_back.json(), payload)
                result["status"] = "PUBLISHED_VERIFIED" if not errors else "PUBLISHED_NOT_VERIFIED"
                result["detail"] = "Read-back matched contract payload." if not errors else "; ".join(errors)

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"{result['status']}: {result['detail']}")
    print(f"audit={audit_path}")
    return 0 if result["status"] in {"DRY_RUN_READY", "PUBLISHED_VERIFIED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
