"""Build a reviewable provenance manifest for contract DAX expressions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


DEFAULT_SEMANTIC_DOCS = Path(__file__).resolve().parents[1].parent / "semantic-model-documentation"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).upper()


def raw_name_lines(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = re.search(r'"name"\s*:\s*"(.*)"', line)
        if match and match.group(1) not in result:
            result[match.group(1)] = number
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--semantic-docs", type=Path, default=DEFAULT_SEMANTIC_DOCS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    measures_path = args.semantic_docs / "inventories" / "measures.csv"
    raw_schema_path = args.semantic_docs / "raw" / "DataModelSchema.json"
    source_rows: dict[tuple[str, str], tuple[int, dict[str, str]]] = {}
    with measures_path.open(encoding="utf-8-sig", newline="") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            key = (normalize(row.get("table", "")), normalize(row.get("measure", "")))
            source_rows[key] = (row_number, row)

    raw_lines = raw_name_lines(raw_schema_path)
    output_rows: list[dict[str, object]] = []
    for metric in contract.get("metrics", []):
        table = str(metric.get("modelTable", ""))
        measure = str(metric.get("metricId", ""))
        key = (normalize(table), normalize(measure))
        source = source_rows.get(key)
        source_row_number = source[0] if source else ""
        source_row = source[1] if source else {}
        contract_dax = str(metric.get("daxExpression", ""))
        extracted_dax = str(source_row.get("expression", ""))
        output_rows.append(
            {
                "metric_id": measure,
                "model_table": table,
                "contract_dax_sha256": hashlib.sha256(contract_dax.encode("utf-8")).hexdigest(),
                "inventory_dax_sha256": hashlib.sha256(extracted_dax.strip().encode("utf-8")).hexdigest() if source else "",
                "dax_exact_match": normalize(contract_dax) == normalize(extracted_dax) if source else False,
                "measure_inventory": str(measures_path),
                "measure_inventory_row": source_row_number,
                "lineage_tag": source_row.get("lineage_tag", ""),
                "raw_model_schema": str(raw_schema_path),
                "raw_model_schema_name_line": raw_lines.get(measure, ""),
                "source_lineage": " | ".join(metric.get("lineage", {}).get("sourcePaths", [])),
                "evidence_status": "matched" if source and normalize(contract_dax) == normalize(extracted_dax) else "review_required",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)
    matched = sum(row["evidence_status"] == "matched" for row in output_rows)
    print(f"wrote={args.output} metrics={len(output_rows)} exact_matches={matched}")
    return 0 if matched == len(output_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
