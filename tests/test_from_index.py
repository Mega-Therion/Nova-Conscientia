"""Index rows become stack layers without treating a workshop path as proof."""

import unittest

from core.from_index import stack_rows


class TestFromIndex(unittest.TestCase):
    def test_formal_row_stands_and_uncited_empirical_does_not(self):
        result = stack_rows(
            "a0-sparc",
            [
                {
                    "path": "lean/a0.md",
                    "claim_id": "a0-sparc",
                    "band": "formal",
                    "stated": 1.0,
                    "citation": "",
                },
                {
                    "path": "notes/a0.md",
                    "claim_id": "a0-sparc",
                    "band": "empirical",
                    "stated": 0.8,
                    "citation": "",
                },
                {
                    "path": "notes/other.md",
                    "claim_id": "cassini",
                    "band": "empirical",
                    "stated": 0.8,
                    "citation": "cassini.md",
                },
            ],
        )
        self.assertEqual(
            [layer.reading.source_id for layer in result.included], ["lean/a0.md"]
        )

    def test_cited_measurement_stands_inside_the_band(self):
        result = stack_rows(
            "event-2019",
            [
                {
                    "path": "sources/chronicle.md",
                    "claim_id": "event-2019",
                    "band": "empirical",
                    "stated": 0.8,
                    "citation": "https://example.test/chronicle",
                },
            ],
        )
        self.assertTrue(result.stands)


if __name__ == "__main__":
    unittest.main()
