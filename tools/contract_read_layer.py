"""Read-only agent/MCP-style access to a versioned metric contract.

This local adapter mirrors the planned MCP resources and tools. It does not
query data and does not bypass Alation authorization; it returns governed
contract context for agent planning and validation.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "contracts" / "group-health-dashboard" / "0.1.0.json"


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def envelope(contract: dict[str, Any], payload: Any, status: str = "OK") -> dict[str, Any]:
    review = contract.get("review", {})
    certification = review.get("certificationStatus", "unreviewed")
    access_decision = "allowed" if contract.get("contractStatus") == "published" and certification == "approved" else "review"
    return {
        "status": status,
        "productId": contract["product"]["productId"],
        "contractVersion": contract["contractVersion"],
        "contractStatus": contract["contractStatus"],
        "asOf": datetime.now(timezone.utc).isoformat(),
        "result": payload,
        "sources": [
            {
                "type": "contract_repository",
                "productId": contract["product"]["productId"],
                "contractVersion": contract["contractVersion"],
            }
        ],
        "governance": {
            "owner": review.get("owner", ""),
            "steward": review.get("steward", ""),
            "certificationStatus": certification,
            "accessDecision": access_decision,
        },
        "limitations": review.get("knownLimitations", []),
    }


def find_metric(contract: dict[str, Any], metric_id: str) -> dict[str, Any] | None:
    exact = next((m for m in contract["metrics"] if m["metricId"] == metric_id), None)
    if exact:
        return exact
    folded = metric_id.casefold()
    return next((m for m in contract["metrics"] if m["displayName"].casefold() == folded), None)


def search_metrics(contract: dict[str, Any], query: str, include_uncertified: bool = False) -> dict[str, Any]:
    terms = [term for term in re.findall(r"[\w]+", query.casefold()) if term]
    results = []
    for metric in contract["metrics"]:
        if not include_uncertified and metric.get("review", {}).get("status") not in {"approved", "steward_approved"}:
            continue
        haystack = " ".join(
            [
                metric["metricId"],
                metric["displayName"],
                metric.get("definition", ""),
                metric.get("modelTable", ""),
                " ".join(metric.get("glossaryTerms", [])),
            ]
        ).casefold()
        matched = [term for term in terms if term in haystack]
        if terms and len(matched) != len(terms):
            continue
        results.append(
            {
                "metricId": metric["metricId"],
                "displayName": metric["displayName"],
                "definition": metric["definition"],
                "role": metric.get("role"),
                "reviewStatus": metric.get("review", {}).get("status"),
                "matchTerms": matched,
            }
        )
    return {"query": query, "count": len(results), "metrics": results}


def metric_definition(contract: dict[str, Any], metric_id: str) -> dict[str, Any]:
    metric = find_metric(contract, metric_id)
    if not metric:
        return {"status": "NOT_FOUND", "metricId": metric_id}
    return {
        "metricId": metric["metricId"],
        "displayName": metric["displayName"],
        "definition": metric["definition"],
        "expressionLanguage": metric["expressionLanguage"],
        "daxExpression": metric["daxExpression"],
        "formatString": metric.get("formatString", ""),
        "modelTable": metric["modelTable"],
        "role": metric.get("role"),
        "grain": metric["grain"],
        "aggregationRule": metric["aggregationRule"],
        "directDependencies": metric.get("directDependencies", []),
        "transitiveDependencies": metric.get("transitiveDependencies", []),
        "review": metric.get("review", {}),
    }


def metric_lineage(contract: dict[str, Any], metric_id: str) -> dict[str, Any]:
    metric = find_metric(contract, metric_id)
    if not metric:
        return {"status": "NOT_FOUND", "metricId": metric_id}
    return {
        "metricId": metric["metricId"],
        "modelTable": metric["modelTable"],
        "sourcePaths": metric.get("lineage", {}).get("sourcePaths", []),
        "alationObjectIds": metric.get("lineage", {}).get("alationObjectIds", []),
        "lineageStatus": metric.get("lineage", {}).get("status"),
        "directDependencies": metric.get("directDependencies", []),
        "transitiveDependencies": metric.get("transitiveDependencies", []),
        "reportAssets": contract.get("assets", {}),
    }


def metric_visual_usage(contract: dict[str, Any], metric_id: str) -> dict[str, Any]:
    metric = find_metric(contract, metric_id)
    if not metric:
        return {"status": "NOT_FOUND", "metricId": metric_id}
    return {
        "metricId": metric["metricId"],
        "referenceCount": metric.get("usage", {}).get("referenceCount", 0),
        "visuals": metric.get("usage", {}).get("visuals", []),
        "impactStatus": "consumed" if metric.get("usage", {}).get("referenceCount", 0) else "not_observed",
    }


def join_context(contract: dict[str, Any], table: str | None = None) -> dict[str, Any]:
    relationships = contract.get("relationships", [])
    if table:
        folded = table.casefold()
        relationships = [
            relationship
            for relationship in relationships
            if folded in relationship.get("fromTable", "").casefold()
            or folded in relationship.get("toTable", "").casefold()
        ]
    return {
        "count": len(relationships),
        "relationships": relationships,
        "note": "Power BI relationship evidence; cardinality is unresolved where blank and must not be inferred.",
    }


def validate_metric_request(
    contract: dict[str, Any],
    metric_id: str,
    aggregation: str | None,
    grain: str | None,
    include_uncertified: bool,
) -> dict[str, Any]:
    metric = find_metric(contract, metric_id)
    if not metric:
        return {"status": "NOT_FOUND", "metricId": metric_id}
    review_status = metric.get("review", {}).get("status", "")
    if not include_uncertified and review_status not in {"approved", "steward_approved"}:
        return {"status": "UNCERTIFIED", "metricId": metric["metricId"], "reviewStatus": review_status}
    if aggregation and aggregation.casefold() not in {metric.get("aggregationRule", "").casefold(), "model_defined"}:
        return {"status": "INVALID_AGGREGATION", "metricId": metric["metricId"], "allowed": metric.get("aggregationRule")}
    if grain and grain.casefold() != metric.get("grain", "").casefold():
        return {"status": "INVALID_GRAIN", "metricId": metric["metricId"], "allowed": metric.get("grain")}
    lineage_status = metric.get("lineage", {}).get("status")
    if lineage_status in {"unresolved", "model_only"}:
        return {"status": "UNRESOLVED_LINEAGE", "metricId": metric["metricId"], "lineageStatus": lineage_status}
    return {"status": "VALID", "metricId": metric["metricId"], "reviewStatus": review_status}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search_metrics")
    search.add_argument("query")
    search.add_argument("--include-uncertified", action="store_true")

    for name in ("get_metric_definition", "get_metric_lineage", "get_metric_visual_usage"):
        command = subparsers.add_parser(name)
        command.add_argument("metric_id")

    joins = subparsers.add_parser("get_join_context")
    joins.add_argument("--table")

    validate = subparsers.add_parser("validate_metric_request")
    validate.add_argument("metric_id")
    validate.add_argument("--aggregation")
    validate.add_argument("--grain")
    validate.add_argument("--include-uncertified", action="store_true")

    args = parser.parse_args()
    contract = load_contract(args.contract)
    if args.command == "search_metrics":
        data = search_metrics(contract, args.query, args.include_uncertified)
        result = envelope(contract, data)
    elif args.command == "get_metric_definition":
        data = metric_definition(contract, args.metric_id)
        result = envelope(contract, data, data.get("status", "OK"))
    elif args.command == "get_metric_lineage":
        data = metric_lineage(contract, args.metric_id)
        result = envelope(contract, data, data.get("status", "OK"))
    elif args.command == "get_metric_visual_usage":
        data = metric_visual_usage(contract, args.metric_id)
        result = envelope(contract, data, data.get("status", "OK"))
    elif args.command == "get_join_context":
        result = envelope(contract, join_context(contract, args.table))
    else:
        data = validate_metric_request(contract, args.metric_id, args.aggregation, args.grain, args.include_uncertified)
        result = envelope(contract, data, data.get("status", "OK"))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
