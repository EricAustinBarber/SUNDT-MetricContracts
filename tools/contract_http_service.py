"""Local read-only HTTP adapter for the governed contract interface.

This is a development transport for the MCP/API contract. It is intentionally
bound to localhost by default and reads only the versioned contract. It does
not query Power BI, Alation, or production data.
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_read_layer import (  # noqa: E402
    DEFAULT_CONTRACT,
    envelope,
    find_metric,
    join_context,
    load_contract,
    metric_definition,
    metric_lineage,
    metric_visual_usage,
    search_metrics,
    validate_metric_request,
)


class ContractHandler(BaseHTTPRequestHandler):
    contract: dict = {}

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("request body exceeds 1 MB")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
        if path == ["health"]:
            self.send_json(envelope(self.contract, {"service": "contract_http_service", "readOnly": True}))
            return
        if len(path) < 3 or path[:2] != ["resources", "data-products"]:
            self.send_json({"status": "NOT_FOUND", "error": "resource not found"}, 404)
            return
        product_id = path[2]
        if product_id != self.contract["product"]["productId"]:
            self.send_json({"status": "NOT_FOUND", "productId": product_id}, 404)
            return
        if len(path) == 3:
            data = {
                "product": self.contract["product"],
                "assets": self.contract.get("assets", {}),
                "metricCount": len(self.contract.get("metrics", [])),
                "relationshipCount": len(self.contract.get("relationships", [])),
            }
        elif len(path) == 4 and path[3] == "relationships":
            data = join_context(self.contract)
        elif len(path) >= 5 and path[3] == "metrics":
            metric_id = path[4]
            if len(path) == 5:
                data = metric_definition(self.contract, metric_id)
            elif len(path) == 6 and path[5] == "lineage":
                data = metric_lineage(self.contract, metric_id)
            elif len(path) == 6 and path[5] == "visual-usage":
                data = metric_visual_usage(self.contract, metric_id)
            else:
                data = {"status": "NOT_FOUND", "path": parsed.path}
        else:
            data = {"status": "NOT_FOUND", "path": parsed.path}
        status = data.get("status", "OK")
        self.send_json(envelope(self.contract, data, status), 404 if status == "NOT_FOUND" else 200)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
        if len(path) != 2 or path[0] != "tools":
            self.send_json({"status": "NOT_FOUND", "error": "tool not found"}, 404)
            return
        try:
            request = self.read_json()
            tool = path[1]
            if tool == "search_metrics":
                data = search_metrics(self.contract, str(request.get("query", "")), bool(request.get("includeUncertified", False)))
            elif tool == "get_metric_definition":
                data = metric_definition(self.contract, str(request.get("metricId", "")))
            elif tool == "get_metric_lineage":
                data = metric_lineage(self.contract, str(request.get("metricId", "")))
            elif tool == "get_metric_visual_usage":
                data = metric_visual_usage(self.contract, str(request.get("metricId", "")))
            elif tool == "get_join_context":
                data = join_context(self.contract, request.get("table"))
            elif tool == "validate_metric_request":
                data = validate_metric_request(
                    self.contract,
                    str(request.get("metricId", "")),
                    request.get("aggregation"),
                    request.get("grain"),
                    bool(request.get("includeUncertified", False)),
                )
            else:
                self.send_json({"status": "NOT_FOUND", "tool": tool}, 404)
                return
            status = data.get("status", "OK")
            self.send_json(envelope(self.contract, data, status), 404 if status == "NOT_FOUND" else 200)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"status": "INVALID_REQUEST", "error": str(exc)}, 400)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    ContractHandler.contract = load_contract(args.contract)
    server = ThreadingHTTPServer((args.host, args.port), ContractHandler)
    print(f"contract service listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopping contract service")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
