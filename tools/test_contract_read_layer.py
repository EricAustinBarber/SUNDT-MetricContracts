"""Smoke tests for the local agent/MCP contract read layer."""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contract_read_layer import (
    DEFAULT_CONTRACT,
    find_metric,
    join_context,
    load_contract,
    metric_definition,
    metric_lineage,
    validate_metric_request,
)


class ContractReadLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(DEFAULT_CONTRACT)

    def test_contract_has_expected_metric_and_relationship_counts(self) -> None:
        self.assertEqual(len(self.contract["metrics"]), 316)
        self.assertEqual(len(self.contract["relationships"]), 89)

    def test_exact_dax_is_returned(self) -> None:
        metric = find_metric(self.contract, "FIN_Score_Trending")
        self.assertIsNotNone(metric)
        definition = metric_definition(self.contract, "FIN_Score_Trending")
        self.assertEqual(definition["daxExpression"], metric["daxExpression"])
        self.assertEqual(definition["expressionLanguage"], "DAX")

    def test_join_context_does_not_infer_cardinality(self) -> None:
        result = join_context(self.contract, "fact_project_billing_current_v")
        self.assertGreaterEqual(result["count"], 1)
        self.assertEqual(result["relationships"][0]["cardinality"], "")

    def test_model_only_lineage_is_explicit(self) -> None:
        result = metric_lineage(self.contract, "FIN_Score_Trending")
        self.assertEqual(result["lineageStatus"], "model_only")
        validation = validate_metric_request(
            self.contract,
            "FIN_Score_Trending",
            aggregation=None,
            grain=None,
            include_uncertified=True,
        )
        self.assertEqual(validation["status"], "UNRESOLVED_LINEAGE")

    def test_unknown_metric_is_not_substituted(self) -> None:
        result = metric_definition(self.contract, "does-not-exist")
        self.assertEqual(result["status"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
