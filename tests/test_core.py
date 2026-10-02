"""Unit and property tests for the core runtime (Hamilgrangian, gate, ADCCL, topology).

Every Lean-verified identity of Res-Nova Hamilgrangian.lean that the translation
depends on is checked here numerically (H1, H2, H3, H6, H7, the two-channel
union algebra, and the QUMOND gate receipts of qumond_pm.py).
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "verification", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from sovereign_clipping_gate import (  # type: ignore
    COLLAPSE_TOLERANCE,
    MEASURED_TAU,
    GateLedger,
    SovereignClippingGate,
    band_ceiling_at_seven_tenths,
    cosine_similarity,
    derived_spin_ceiling,
    kappa_of_theta,
    theta_of_kappa,
    two_channel_union,
)
from dual_channel_action import (  # type: ignore
    DualChannelAction,
    f_dual,
    fisher_information,
    h_kinetic,
    l_corr,
    mu,
    odds_of,
    p_flux,
)
from anti_drift_controller import (  # type: ignore
    ADCCLController,
    CycleRecord,
    drift_coordinate,
    drift_coordinate_capped,
)
from topology_graph import (  # type: ignore
    AgentNode,
    TopologyGraph,
    far_field_monopole_ratio,
    ln_nu_derivative,
    nu_std,
)


class TestHamilgrangianIdentities(unittest.TestCase):
    """The Lean-verified identities of Res-Nova, checked numerically."""

    def test_h1_dual_channel_decomposition(self):
        """F_dual = H - L_corr for a grid of x (theorem H1)."""
        for x in [1e-6, 0.01, 0.1, 0.5, 1.0, 3.0, 10.0, 1e3]:
            with self.subTest(x=x):
                self.assertAlmostEqual(f_dual(x), h_kinetic(x) - l_corr(x), places=12)

    def test_h2_constitutive_flux_balance(self):
        """x - mu(x) = p_flux(x) and F'(x) = p_flux(x) (theorem H2)."""
        h = 1e-7
        for x in [0.01, 0.1, 0.5, 1.0, 3.0, 10.0]:
            with self.subTest(x=x):
                self.assertAlmostEqual(x - mu(x), p_flux(x), places=12)
                numerical = (f_dual(x + h) - f_dual(x - h)) / (2 * h)
                self.assertAlmostEqual(numerical, p_flux(x), places=5)

    def test_h3_mu_constitutive(self):
        """mu(x)(1 + x) = x (theorem H3) and mu in [0, 1)."""
        for x in [0.0, 1e-6, 0.1, 0.7, 1.0, 10.0, 1e3]:
            with self.subTest(x=x):
                self.assertAlmostEqual(mu(x) * (1.0 + x), x, places=12)
                self.assertTrue(0.0 <= mu(x) < 1.0)

    def test_h6_odds_inversion(self):
        """mu(p/(1-p)) = p for p in (0, 1) (theorem H6)."""
        for p in [1e-6, 0.1, 0.3, 0.5, 0.7, 0.9, 1 - 1e-6]:
            with self.subTest(p=p):
                self.assertAlmostEqual(mu(odds_of(p)), p, places=10)

    def test_h7_fisher_identity(self):
        """F'(x)^2 * I(mu(x)) = x^3 (theorem H7)."""
        for x in [0.1, 0.5, 1.0, 2.0, 10.0]:
            with self.subTest(x=x):
                lhs = p_flux(x) ** 2 * fisher_information(mu(x))
                self.assertAlmostEqual(lhs, x ** 3, places=9)

    def test_l_corr_properties(self):
        """L_corr is non-negative, increasing, and convex on x >= 0."""
        xs = [0.0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2]
        values = [l_corr(x) for x in xs]
        self.assertTrue(all(v >= 0.0 for v in values))
        self.assertTrue(all(b > a for a, b in zip(values, values[1:])))
        for a, b, c in zip(xs, xs[1:], xs[2:]):
            mid = l_corr((a + c) / 2)
            chord = (l_corr(a) + l_corr(c)) / 2
            self.assertLessEqual(mid, chord + 1e-12)

    def test_dual_channel_decision(self):
        """Clean proposals are admitted; violation-laden ones are rejected."""
        action = DualChannelAction()
        clean = action.evaluate(momentum=0.5, constraint_pressure=0.0)
        self.assertTrue(clean.accepted)
        dirty = action.evaluate(momentum=0.5, constraint_pressure=5.0)
        self.assertFalse(dirty.accepted)
        self.assertAlmostEqual(dirty.credibility, mu(0.5), places=12)

    def test_scale_free_credit_mode(self):
        """Scale-free credit mode evaluates pressure relative to momentum."""
        action_default = DualChannelAction()
        self.assertEqual(action_default.credit_mode, "classic")
        
        action_sf = DualChannelAction(credit_mode="scale_free")
        # For momentum=0.5, pressure=0.0: relative pressure is 0.0, net = 0.5 - L_corr(0) = 0.5
        clean = action_sf.evaluate(momentum=0.5, constraint_pressure=0.0)
        self.assertTrue(clean.accepted)
        self.assertAlmostEqual(clean.net_action, 0.5, places=12)

        # Small move (0.01) with proportional small pressure (0.001) -> w_rel = 0.1 -> L_corr(0.1) ~ 0.00466 -> net > 0
        small_clean = action_sf.evaluate(momentum=0.01, constraint_pressure=0.001)
        self.assertTrue(small_clean.accepted)

        # High relative pressure -> rejected
        dirty = action_sf.evaluate(momentum=0.01, constraint_pressure=0.05)
        self.assertFalse(dirty.accepted)

    def test_invalid_credit_mode(self):
        """Unknown credit modes are rejected."""
        action = DualChannelAction(credit_mode="invalid_mode")
        with self.assertRaises(ValueError):
            action.evaluate(momentum=0.5, constraint_pressure=0.0)

    def test_correction_force_is_constitutive(self):
        """The correction force is exactly p_flux (identity H2)."""
        action = DualChannelAction()
        for x in [0.0, 0.3, 1.0, 5.0]:
            self.assertEqual(action.correction_force(x), p_flux(x))


class TestCeilingsAndGate(unittest.TestCase):
    """The two-channel ceiling algebra and the sovereign clipping gate."""

    def test_two_channel_union_algebra(self):
        """1 - (1 - theta)^2 = theta(2 - theta), and kappa inverts exactly."""
        for theta in [0.0, 0.1, 0.3, 0.7, 0.7071067811865476, 0.9, 1.0]:
            with self.subTest(theta=theta):
                self.assertAlmostEqual(
                    two_channel_union(theta), 1.0 - (1.0 - theta) ** 2, places=14
                )
                self.assertAlmostEqual(theta_of_kappa(kappa_of_theta(theta)), theta,
                                       places=12)

    def test_catalogued_values(self):
        """Band ceiling 0.953939..., spin ceiling 0.956145..., measured 0.9539."""
        self.assertAlmostEqual(band_ceiling_at_seven_tenths(),
                               0.9539392014169457, places=15)
        self.assertAlmostEqual(derived_spin_ceiling(),
                               math.sqrt(math.sqrt(2.0) - 0.5), places=12)
        # The three catalogued numbers are all distinct; do not conflate them.
        self.assertNotAlmostEqual(MEASURED_TAU, band_ceiling_at_seven_tenths(),
                                   places=5)
        # The derived ceiling sits 2.2e-3 ABOVE the band ceiling (Finding 2 of
        # Res-Nova TWO_CHANNEL_CEILING_ANALYSIS.md: the 3.2x compression).
        self.assertAlmostEqual(derived_spin_ceiling() - band_ceiling_at_seven_tenths(),
                                0.002205956, places=6)

    def test_gate_pass_and_clip(self):
        """Inside the cone passes; outside is clipped onto the cone boundary."""
        gate = SovereignClippingGate([1.0, 0.0, 0.0])
        _, ok = gate.evaluate([1.0, 0.1, 0.0])
        self.assertEqual(ok.verdict, "PASS")
        clipped, decision = gate.evaluate([1.0, 0.4, 0.0])
        self.assertEqual(decision.verdict, "CLIP")
        self.assertAlmostEqual(
            cosine_similarity(clipped, gate.anchor), MEASURED_TAU, places=12
        )
        # The clip preserves the state's norm.
        self.assertAlmostEqual(math.sqrt(sum(c * c for c in clipped)),
                               math.sqrt(1.0 + 0.16), places=12)
        self.assertGreater(decision.dissipated_norm, 0.0)

    def test_gate_fails_closed(self):
        """Zero vectors and anti-parallel states are rejected, never admitted."""
        gate = SovereignClippingGate([1.0, 0.0, 0.0])
        _, zero = gate.evaluate([0.0, 0.0, 0.0])
        self.assertEqual(zero.verdict, "REJECT")
        _, anti = gate.evaluate([-1.0, 0.0, 0.0])
        self.assertEqual(anti.verdict, "REJECT")
        with self.assertRaises(ValueError):
            SovereignClippingGate([0.0, 0.0, 0.0])
        with self.assertRaises(ValueError):
            SovereignClippingGate([1.0, 0.0, 0.0], threshold=1.5)

    def test_gate_ledger(self):
        """The ledger counts cycles and collapse events monotonically."""
        gate = SovereignClippingGate([1.0, 0.0, 0.0])
        ledger = GateLedger()
        for state in ([1.0, 0.05, 0.0], [1.0, 0.5, 0.0], [0.1, 1.0, 0.0]):
            _, decision = gate.evaluate(state)
            ledger.append(decision, state)
        self.assertEqual(ledger.cycle, 3)
        self.assertEqual(ledger.collapse_events(), 2)
        summary = ledger.summary()
        self.assertEqual(summary["cycles"], 3.0)
        self.assertEqual(summary["count_CLIP"], 2.0)

    def test_gate_ledger_immutable(self):
        """GateLedger.entries returns an immutable tuple that cannot be mutated."""
        gate = SovereignClippingGate([1.0, 0.0, 0.0])
        ledger = GateLedger()
        _, decision = gate.evaluate([1.0, 0.05, 0.0])
        ledger.append(decision, [1.0, 0.05, 0.0])
        entries = ledger.entries
        self.assertIsInstance(entries, tuple)
        with self.assertRaises(AttributeError):
            entries.append(decision)
        with self.assertRaises(TypeError):
            entries[0] = decision

    def test_collapse_tolerance(self):
        """Collapse checks use a 1e-9 tolerance so gate-clipped states
        (cosine ≈ τ) are not spuriously counted as collapsed due to
        floating-point rounding."""
        gate = SovereignClippingGate([1.0, 0.0, 0.0])
        clipped, decision = gate.evaluate([1.0, 0.4, 0.0])
        self.assertEqual(decision.verdict, "CLIP")
        sim = cosine_similarity(clipped, gate.anchor)
        # The clipped similarity is within floating-point tolerance of τ.
        self.assertLess(abs(sim - MEASURED_TAU), COLLAPSE_TOLERANCE)
        # The controller's collapse_cycles should not count this as collapsed.
        ctrl = ADCCLController(anchor=[1.0, 0.0, 0.0])
        ctrl._state = clipped
        ctrl._ledger.append(CycleRecord(
            cycle=1, verdict="ACCEPTED+CLIP", similarity_in=0.5,
            similarity_out=sim, drift=0.1, energy=0.1,
            net_action=0.1, reason="test",
        ))
        self.assertEqual(ctrl.collapse_cycles(), 0)

    def test_drift_coordinate_45_degrees(self):
        """x = tan(alpha): x = 1 at exactly 45 degrees; caps when orthogonal."""
        self.assertAlmostEqual(drift_coordinate([1.0, 1.0, 0.0], [1.0, 0.0, 0.0]),
                               1.0, places=12)
        self.assertEqual(drift_coordinate_capped([0.0, 1.0, 0.0], [1.0, 0.0, 0.0]),
                         1e6)
        with self.assertRaises(ValueError):
            drift_coordinate([0.0, 1.0, 0.0], [1.0, 0.0, 0.0])


class TestADCCL(unittest.TestCase):
    """The anti-drift control loop end to end."""

    def _controller(self):
        return ADCCLController(anchor=[1.0, 0.0, 0.0, 0.0])

    def test_clean_moves_are_accepted(self):
        """Small aligned moves pass both channels and the gate."""
        ctrl = self._controller()
        record = ctrl.step([0.05, 0.0, 0.0, 0.0])
        self.assertTrue(record.verdict.startswith("ACCEPTED"))
        self.assertGreaterEqual(record.similarity_out, MEASURED_TAU)
        self.assertEqual(ctrl.summary()["cycles"], 1.0)

    def test_violating_moves_are_rejected_and_corrected(self):
        """A small move cannot pay a heavy violation: rejected, then pulled home."""
        ctrl = self._controller()
        record = ctrl.step([0.05, 0.0, 0.0, 0.0])
        self.assertTrue(record.verdict.startswith("ACCEPTED"))
        record = ctrl.step([0.0, 0.5, 0.0, 0.0], constraint_pressure=10.0)
        self.assertEqual(record.verdict, "REJECTED")
        self.assertGreaterEqual(record.similarity_out, MEASURED_TAU)
        self.assertLessEqual(record.similarity_out, 1.0)

    def test_purchasability_seam_is_documented_by_test(self):
        """The dual channel is a soft regulator: quadratic momentum can buy a
        soft violation (hard invariants are vetoed by the consensus layer, not
        priced here; see ARCHITECTURE.md, Safety analysis)."""
        ctrl = self._controller()
        record = ctrl.step([0.0, 5.0, 0.0, 0.0], constraint_pressure=10.0)
        self.assertEqual(record.verdict, "ACCEPTED+CLIP")
        self.assertGreaterEqual(record.similarity_out, MEASURED_TAU)

    def test_energy_halt_fails_closed(self):
        """A tight halt energy HALTs the loop; further steps raise."""
        ctrl = ADCCLController(anchor=[1.0, 0.0, 0.0], halt_energy=1e-12)
        record = ctrl.step([0.0, 2.0, 0.0])
        # Any nonzero post-gate energy exceeds 1e-12: the loop must halt.
        self.assertIn(record.verdict, ("HALT", "REJECTED"))
        if record.verdict == "REJECTED":
            record = ctrl.step([0.0, 2.0, 0.0])
            self.assertEqual(record.verdict, "HALT")
        self.assertTrue(ctrl.halted)
        with self.assertRaises(RuntimeError):
            ctrl.step([0.0, 0.0, 0.0])

    def test_ledger_integrity(self):
        """Cycle numbers are monotonic and every verdict is recorded."""
        ctrl = self._controller()
        for move in ([0.05, 0.0, 0.0, 0.0], [0.0, 0.05, 0.0, 0.0],
                     [0.0, 0.0, 0.05, 0.0]):
            ctrl.step(move)
        numbers = [r.cycle for r in ctrl.ledger]
        self.assertEqual(numbers, [1, 2, 3])
        self.assertTrue(all(r.verdict in ("ACCEPTED", "ACCEPTED+CLIP", "REJECTED")
                            for r in ctrl.ledger))

    def test_controller_ledger_immutable(self):
        """The controller's ledger is a read-only tuple that cannot be mutated."""
        ctrl = self._controller()
        ctrl.step([0.05, 0.0, 0.0, 0.0])
        self.assertIsInstance(ctrl.ledger, tuple)
        with self.assertRaises(AttributeError):
            ctrl.ledger.append(None)
        with self.assertRaises(TypeError):
            ctrl.ledger[0] = None


class TestTopologyGraph(unittest.TestCase):
    """QUMOND attention, the carry-lookahead scan, and screening."""

    def test_nu_std_against_qumond_receipts(self):
        """nu_std matches qumond_pm.py's gate receipts (QUMOND_PM_GATES.json)."""
        # coarse.external: g_eN = 0.1 -> nu_e = 3.24229736410009.
        self.assertAlmostEqual(nu_std(0.1), 3.24229736410009, places=11)
        # L_e at y_e = 0.1 is -0.47503119150616474 (central-difference check).
        self.assertAlmostEqual(ln_nu_derivative(0.1), -0.47503119150616474,
                               delta=1e-4)
        # Predicted monopole ratio nu_e (1 + L_e/3) = 2.728899904071502.
        self.assertAlmostEqual(far_field_monopole_ratio(0.1), 2.728899904071502,
                               delta=1e-3)
        # Limits: nu -> 1 for strong coupling, amplification for weak coupling.
        self.assertAlmostEqual(nu_std(1e12), 1.0, places=6)
        self.assertGreater(nu_std(1e-3), 30.0)
        with self.assertRaises(ValueError):
            nu_std(0.0)

    def test_carry_lookahead_scan(self):
        """The scan produces exact exclusive prefixes for every roster size."""
        for n in (1, 2, 3, 5, 8, 13, 21):
            with self.subTest(n=n):
                agents = [AgentNode(f"a{i:03d}", [float(i), 0.0]) for i in range(n)]
                graph = TopologyGraph(agents)
                values = {f"a{i:03d}": float(i) for i in range(n)}
                scan = graph.carry_lookahead_scan(values)
                for i in range(n):
                    self.assertEqual(scan[f"a{i:03d}"], float(sum(range(i))))

    def test_scan_max_operation(self):
        """A non-additive associative operator routes correctly too."""
        agents = [AgentNode(f"a{i:03d}", [float(i), 0.0]) for i in range(4)]
        graph = TopologyGraph(agents)
        values = {f"a{i:03d}": float(i + 1) for i in range(4)}
        scan = graph.carry_lookahead_scan(
            values, op=lambda a, b: a if a >= b else b, identity=-1.0
        )
        expected = [-1.0, 1.0, 2.0, 3.0]
        got = [scan[f"a{i:03d}"] for i in range(4)]
        self.assertEqual(got, expected)

    def test_hierarchical_field(self):
        """The attended field pulls toward the swarm, amplified for weak coupling."""
        agents = [
            AgentNode("hub", [0.0, 0.0, 0.0], mass=1.0, context_scale=1.0),
            AgentNode("spoke", [3.0, 0.0, 0.0], mass=1.0, context_scale=1.0),
            AgentNode("bystander", [0.0, 5.0, 0.0], mass=1.0, context_scale=1.0),
        ]
        graph = TopologyGraph(agents)
        field = graph.field_on("hub")
        self.assertGreater(field[0], 0.0)
        self.assertGreater(field[1], 0.0)
        self.assertAlmostEqual(field[2], 0.0, places=12)
        # Weak-coupling amplification: a far, light agent is amplified by nu > 1.
        weak = graph.field_on("bystander")
        newton = 1.0 / 9.0  # hub's pull on bystander before amplification
        attended_norm = math.sqrt(sum(v * v for v in weak))
        self.assertGreater(attended_norm - newton, 0.0)

    def test_context_field_and_screening(self):
        """A strong context field screens weakly-coupled agents."""
        agents = [
            AgentNode("inner", [0.0, 0.0], mass=0.01, context_scale=1.0),
            AgentNode("outer", [10.0, 0.0], mass=0.01, context_scale=1.0),
        ]
        graph = TopologyGraph(agents)
        report = graph.sandbox_screening([5.0, 0.0])
        by_id = {r["agent_id"]: r for r in report}
        # The uniform context dominates both agents' weak internal coupling.
        self.assertTrue(all(r["screened"] for r in report))
        self.assertGreater(by_id["inner"]["far_field_amplification"], 1.0)
        attended = graph.apply_context_field("inner", [5.0, 0.0])
        self.assertGreater(attended[0], 5.0)  # nu(|g|/a0) > 1 amplifies the bias

    def test_fail_closed_configuration(self):
        """Degenerate rosters and nodes are refused."""
        with self.assertRaises(ValueError):
            TopologyGraph([])
        with self.assertRaises(ValueError):
            AgentNode("bad", [0.0, 0.0], mass=0.0)
        with self.assertRaises(ValueError):
            AgentNode("bad", [0.0, 0.0], context_scale=-1.0)


if __name__ == "__main__":
    unittest.main()
