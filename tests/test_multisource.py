"""Several filters on one claim stay in register or stay out of the stack."""

import unittest

from core.claim_band import ClaimKind
from core.multisource import SourceReading, stack


class TestMultisource(unittest.TestCase):
    def test_aligned_layers_stack(self):
        result = stack(
            "a0-sparc",
            [
                SourceReading("lean", "a0-sparc", ClaimKind.FORMAL, 1.0),
                SourceReading(
                    "sparc",
                    "a0-sparc",
                    ClaimKind.EMPIRICAL,
                    0.8,
                    citation="PARAMETER_LEDGER.json",
                ),
            ],
        )
        self.assertTrue(result.stands)
        self.assertEqual(len(result.included), 2)

    def test_wrong_object_is_left_out(self):
        result = stack(
            "a0-sparc",
            [
                SourceReading(
                    "other", "cassini", ClaimKind.EMPIRICAL, 0.8, citation="cassini.md"
                ),
            ],
        )
        self.assertFalse(result.stands)
        self.assertEqual(result.layers[0].reason, "pointed at a different object")

    def test_empirical_without_a_citation_is_left_out(self):
        result = stack(
            "event-2019",
            [
                SourceReading("web", "event-2019", ClaimKind.EMPIRICAL, 0.8),
            ],
        )
        self.assertFalse(result.stands)

    def test_overconfident_measurement_is_left_out(self):
        result = stack(
            "event-2019",
            [
                SourceReading(
                    "web",
                    "event-2019",
                    ClaimKind.EMPIRICAL,
                    0.95,
                    citation="https://example.test",
                ),
            ],
        )
        self.assertFalse(result.stands)

    def test_borrowed_formula_does_not_enter_the_stack(self):
        result = stack(
            "routing",
            [
                SourceReading("qumond", "routing", ClaimKind.BORROWED_MATH, 1.0),
                SourceReading("proof", "routing", ClaimKind.FORMAL, 1.0),
            ],
        )
        self.assertEqual(len(result.included), 1)
        self.assertEqual(result.included[0].reading.source_id, "proof")


if __name__ == "__main__":
    unittest.main()
