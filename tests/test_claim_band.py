"""The certainty band keeps a proof, a measurement, and a borrowed formula apart."""

import unittest

from core.claim_band import CHIRAL_FLOOR, ClaimKind, judge


class TestClaimBand(unittest.TestCase):
    def test_formal_arithmetic_may_be_certain(self):
        decision = judge(ClaimKind.FORMAL, 1.0)
        self.assertTrue(decision.stands)
        self.assertEqual(decision.allowed, 1.0)

    def test_empirical_inside_the_band_stands(self):
        decision = judge(ClaimKind.EMPIRICAL, 0.8)
        self.assertTrue(decision.stands)
        self.assertGreaterEqual(decision.allowed, CHIRAL_FLOOR)
        self.assertLess(decision.allowed, 0.9)

    def test_empirical_overconfidence_is_refused(self):
        decision = judge(ClaimKind.EMPIRICAL, 0.9)
        self.assertFalse(decision.stands)
        self.assertIsNone(decision.allowed)

    def test_empirical_below_the_floor_does_not_stand(self):
        decision = judge(ClaimKind.EMPIRICAL, 0.5)
        self.assertFalse(decision.stands)

    def test_borrowed_math_is_not_a_measurement(self):
        decision = judge(ClaimKind.BORROWED_MATH, 1.0)
        self.assertFalse(decision.stands)
        self.assertIn("not a physical measurement", decision.reason)


if __name__ == "__main__":
    unittest.main()
