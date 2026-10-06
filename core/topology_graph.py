"""Topology graph: hierarchical swarm attention and carry-lookahead gradient routing.

The QUMOND formulas below are borrowed mathematics. They route a swarm.
They are not a galaxy measurement and not a Res-Nova result.

Translation target (Res-Nova -> Nova Conscientia)
--------------------------------------------------
Res-Nova solves the QUMOND field equation on a grid with the Hockney-Eastwood
zero-padded FFT convolution (Res-Nova 02_galaxy_dynamics/qumond_pm.py, sha256
da80971a53273af9028120de4586a1eb2421ed1e8dd1fc7a0ceecff47d479a58):

    nu(y) = sqrt( (1 + sqrt(1 + 4/y^2)) / 2 )          (the mu_std pair)
    g_M    = nu(|g_N| / a0) g_N                        (MOND amplification)
    Phi_M  = FFT-isolated Poisson solve of -div g_M    (O(N log N))

Two structural facts of that solver become the swarm's routing substrate:

1. *Global field from local mass, in O(N log N).* The FFT convolution makes
   every grid point feel every other point without O(N^2) interaction.  The
   swarm translation is a Barnes-Hut-style hierarchy: agents are clustered into
   a binary tree over their semantic positions; far clusters act on an agent
   through their aggregated "center of mass" and near ones are opened.  This is
   the O(N log N) carry-lookahead: interaction credits are aggregated up the
   tree and delivered back down, level by level, exactly as carries propagate
   through a carry-lookahead adder in O(log N) levels.

2. *The interpolation function is attention.* nu(y) = mu_std(y) with y =
   |g|/a0 is exactly a soft attention gate: y << 1 (weak coupling relative to
   the context scale a0) gives nu ~ a0/|g| >> 1 (full amplification of weak
   signals -- the deep-MOND regime is "attend to everything weak"); y >> 1
   gives nu -> 1 (strong signals pass through unamplified -- the Newtonian
   regime).  a0 becomes the swarm's context scale: the strength below which
   agent-to-agent influence is amplified.

3. *External field effect and screening -> context bias and sandboxing.* In
   QUMOND an external field g_eN enters as g_tot = g_N + g_e (uniform), the
   internal dynamics are amplified by nu(|g_tot|/a0), and the far-field
   monopole ratio is nu_e (1 + L_e/3) with L_e = d ln nu / d ln y at y_e
   (qumond_pm.py gate 1b).  In the swarm: a shared context (the parent swarm,
   a global directive) acts as a uniform external field on every sandboxed
   agent; a sandbox whose internal interactions are weak relative to the
   context is *screened* -- dominated by the context, with effective
   amplification exactly the QUMOND far-field factor.

All numerology is grounded (PROVENANCE); nu_std is copied exactly from
qumond_pm.py and verified against that file's gate receipts in tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

PROVENANCE: Dict[str, str] = {
    "DEFAULT_CONTEXT_SCALE": (
        "a0 = 1.0 in normalized units: qumond_pm.py runs its gates in units "
        "G = a0 = M = 1 (Res-Nova 02_galaxy_dynamics/qumond_pm.py docstring, "
        "sha256 da80971a53273af9028120de4586a1eb2421ed1e8dd1fc7a0ceecff47d479a58)."
    ),
    "BARNES_HUT_OPENING_ANGLE": (
        "theta_open = 0.5: the standard Barnes-Hut opening criterion default. "
        "Engineering parameter of the hierarchy, not a Res-Nova constant."
    ),
}


def nu_std(y: float) -> float:
    """The mu_std interpolation pair nu(y) = sqrt((1 + sqrt(1 + 4/y^2)) / 2).

    Copied exactly from Res-Nova qumond_pm.py (nu_std).  This is the attention
    weight: for weak coupling y << 1 it amplifies as 1/sqrt(y); for strong
    coupling y >> 1 it saturates to 1.

    Args:
        y: coupling strength relative to the context scale, y > 0.

    Returns:
        nu(y) > 1 (>= sqrt(2)/sqrt... strictly > 1 for finite y; -> 1 as y -> inf).

    Raises:
        ValueError: if y <= 0 (fail closed; qumond_pm.py clamps at 1e-300, this
            module refuses non-positive coupling outright).
    """
    if y <= 0.0:
        raise ValueError(f"coupling y must be positive, got {y}")
    return math.sqrt(0.5 * (1.0 + math.sqrt(1.0 + 4.0 / (y * y))))


def ln_nu_derivative(y: float, h: float = 1e-6) -> float:
    """L_e = d ln nu / d ln y at y, by central differences on ln y.

    The exact QUMOND external-field logarithmic slope used in gate 1b of
    qumond_pm.py (L_e appears in the far-field monopole ratio nu_e (1 + L_e/3)).

    Args:
        y: evaluation point, y > 0.
        h: step in ln y for the central difference, h > 0.

    Returns:
        The logarithmic derivative L_e = d ln nu / d ln y.
    """
    if y <= 0.0:
        raise ValueError(f"coupling y must be positive, got {y}")
    if h <= 0.0:
        raise ValueError(f"step h must be positive, got {h}")
    y_lo, y_hi = y * math.exp(-h), y * math.exp(h)
    return (math.log(nu_std(y_hi)) - math.log(nu_std(y_lo))) / (2.0 * h)


def far_field_monopole_ratio(y_e: float) -> float:
    """QUMOND far-field monopole factor nu_e (1 + L_e/3) at external coupling y_e.

    Gate 1b of qumond_pm.py predicts the far-field potential ratio
    nu_e (1 + L_e/3); qumond_pm's own receipts show 3.2422 * (1 - 0.47503/3) =
    2.7289 against measured 2.7283 (QUMOND_PM_GATES.json, coarse.external).
    This is the sandbox amplification factor: how much a sandboxed sub-swarm's
    effective context field exceeds the naive external weight.
    """
    nu_e = nu_std(y_e)
    l_e = ln_nu_derivative(y_e)
    return nu_e * (1.0 + l_e / 3.0)


# ---------------------------------------------------------------------------
# Nodes and the hierarchy.
# ---------------------------------------------------------------------------


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    """Dot product; raises on mismatch (fail closed)."""
    if len(a) != len(b) or len(a) == 0:
        raise ValueError("vectors must be non-empty and of equal length")
    return sum(x * y for x, y in zip(a, b))


def _norm(a: Sequence[float]) -> float:
    """Euclidean norm."""
    return math.sqrt(_dot(a, a))


def _sub(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """Elementwise difference a - b."""
    if len(a) != len(b):
        raise ValueError("length mismatch")
    return [x - y for x, y in zip(a, b)]


def _scale(a: Sequence[float], s: float) -> List[float]:
    """Elementwise scaling."""
    return [s * x for x in a]


@dataclass
class AgentNode:
    """One agent in the swarm topology.

    Attributes:
        agent_id: stable identifier (used by routing and receipts).
        position: semantic position vector (embedding of the agent's current
            focus; this is the "space" over which attention operates).
        mass: interaction weight (workload / priority), mass > 0.
        context_scale: this agent's a0; coupling is computed relative to it.
    """

    agent_id: str
    position: Sequence[float]
    mass: float = 1.0
    context_scale: float = 1.0

    def __post_init__(self) -> None:
        """Validate the node; fail closed on degenerate configuration."""
        self.position = list(self.position)
        if not self.position:
            raise ValueError("position vector must be non-empty")
        if self.mass <= 0.0:
            raise ValueError(f"mass must be positive, got {self.mass}")
        if self.context_scale <= 0.0:
            raise ValueError(
                f"context_scale must be positive, got {self.context_scale}"
            )
        if not all(math.isfinite(p) for p in self.position):
            raise ValueError("position must be finite")


@dataclass
class _Cluster:
    """An internal node of the Barnes-Hut hierarchy (never exposed publicly).

    Attributes:
        center_of_mass: mass-weighted mean position of the subtree.
        total_mass: sum of masses in the subtree.
        size: characteristic radius (max distance of a member to the center).
        members: member agent ids (leaf clusters hold exactly one).
    """

    center_of_mass: List[float]
    total_mass: float
    size: float
    members: List[str]


class TopologyGraph:
    """Barnes-Hut hierarchy over the swarm with QUMOND attention routing.

    The graph supports:

    * ``field_on(agent)`` -- the O(N log N) hierarchical attention field on an
      agent: every other agent (or far cluster) contributes a Newtonian-like
      coupling m / d, amplified by nu(y) with y = coupling / a0.
    * ``carry_lookahead_scan(values)`` -- work-efficient prefix aggregation
      (Blelloch-style up-sweep/down-sweep) over a balanced binary tree of the
      agents, the exact structural analogue of carry-lookahead addition:
      gradient/credit signals are aggregated in O(log N) tree levels with O(N)
      work at each level -- used to route per-cycle gradient credit to the
      swarm in O(N log N) total across all levels.
    * ``apply_context_field(external)`` -- the external-field-effect translation:
      a uniform context field biases every agent's effective coupling, and
      ``sandbox_screening`` reports which agents are screened (context
      dominated), with the QUMOND far-field amplification factor.
    """

    def __init__(self, agents: Sequence[AgentNode], opening_angle: float = 0.5) -> None:
        """Build the hierarchy.

        Args:
            agents: the swarm's agents (>= 1).
            opening_angle: Barnes-Hut opening criterion theta_open in (0, 1].

        Raises:
            ValueError: on empty swarm or invalid opening angle.
        """
        if not agents:
            raise ValueError("the topology needs at least one agent")
        if not 0.0 < opening_angle <= 1.0:
            raise ValueError(f"opening_angle must lie in (0, 1], got {opening_angle}")
        self.agents: List[AgentNode] = list(agents)
        self.opening_angle = opening_angle
        self._by_id: Dict[str, AgentNode] = {a.agent_id: a for a in self.agents}
        if len(self._by_id) != len(self.agents):
            raise ValueError("agent ids must be unique")
        # Build a balanced binary hierarchy over the sorted agent list.
        # Sorting by id makes the tree deterministic given the roster.
        order = sorted(self.agents, key=lambda a: a.agent_id)
        self._root = self._build(order, 0, len(order))

    # -- construction -------------------------------------------------------

    def _build(self, order: List[AgentNode], lo: int, hi: int) -> _Cluster:
        """Recursively build the balanced hierarchy over ``order[lo:hi]``."""
        if hi - lo == 1:
            a = order[lo]
            return _Cluster(list(a.position), a.mass, 0.0, [a.agent_id])
        mid = (lo + hi) // 2
        left, right = self._build(order, lo, mid), self._build(order, mid, hi)
        total = left.total_mass + right.total_mass
        com = [
            (left.total_mass * cl + right.total_mass * cr) / total
            for cl, cr in zip(left.center_of_mass, right.center_of_mass)
        ]
        size = max(
            left.size + _norm(_sub(left.center_of_mass, com)),
            right.size + _norm(_sub(right.center_of_mass, com)),
        )
        return _Cluster(com, total, size, left.members + right.members)

    # -- hierarchical attention ----------------------------------------------

    def field_on(self, agent_id: str) -> List[float]:
        """The hierarchical attention field on one agent, O(N log N) worst case.

        The field is the QUMOND translation: a contributor (agent or far
        cluster) at distance d with weight m exerts a coupling g = m / d^2 in
        its direction (a Newtonian-like influence).  The total coupling
        magnitude enters the interpolation nu(|g_tot|/a0), and the *attended*
        field is nu * g_tot -- weak couplings amplified, strong ones passed
        through.

        Args:
            agent_id: the agent to evaluate.

        Returns:
            The attended field vector (the direction the agent is being pulled
            by the swarm's attention).

        Raises:
            KeyError: if the agent is not in the topology.
        """
        if agent_id not in self._by_id:
            raise KeyError(f"unknown agent: {agent_id}")
        target = self._by_id[agent_id]
        g_tot = self._newtonian_field(
            self._root, target, excluded=frozenset({agent_id})
        )
        coupling = _norm(g_tot) / target.context_scale
        attended = (
            _scale(g_tot, nu_std(coupling)) if coupling > 0.0 else [0.0] * len(g_tot)
        )
        return attended

    def _newtonian_field(
        self, cluster: _Cluster, target: AgentNode, excluded: frozenset
    ) -> List[float]:
        """Barnes-Hut traversal: aggregate coupling from ``cluster`` to ``target``.

        The opening criterion: a cluster is taken as a point mass when its
        size / distance < opening_angle; otherwise it is opened (recursed).
        This is the carry-lookahead structure: each tree level contributes
        aggregated "carries" instead of pairwise interactions.
        """
        dim = len(target.position)
        if cluster.total_mass <= 0.0:
            return [0.0] * dim
        delta = _sub(cluster.center_of_mass, target.position)
        dist = _norm(delta)
        # Leaf: direct interaction unless excluded (self) or coincident.
        if len(cluster.members) == 1:
            if cluster.members[0] in excluded or dist == 0.0:
                return [0.0] * dim
            g = cluster.total_mass / (dist * dist)
            return _scale(delta, g / dist)
        # Internal: open or take the point mass.
        if dist > 0.0 and cluster.size / dist < self.opening_angle:
            g = cluster.total_mass / (dist * dist)
            return _scale(delta, g / dist)
        # Coincident internal cluster (dist == 0): open it to separate members.
        # Build the recursion deterministically from stored member positions.
        half = len(cluster.members) // 2
        acc = [0.0] * dim
        for ids in (cluster.members[:half], cluster.members[half:]):
            sub = self._rebuild(ids, excluded)
            if sub is None:
                continue
            contrib = self._newtonian_field(sub, target, excluded)
            acc = [a + c for a, c in zip(acc, contrib)]
        return acc

    def _rebuild(self, agent_ids: List[str], excluded: frozenset) -> Optional[_Cluster]:
        """Rebuild a transient cluster for a subset of member ids.

        Used only on the degenerate coincident-cluster path; members in
        ``excluded`` are dropped (their contribution is identically zero and
        they would create zero-distance interactions).
        """
        members = [
            self._by_id[i] for i in agent_ids if i in self._by_id and i not in excluded
        ]
        if not members:
            return None
        total = sum(a.mass for a in members)
        com = [0.0] * len(members[0].position)
        for a in members:
            com = [c + a.mass * p for c, p in zip(com, a.position)]
        com = [c / total for c in com]
        size = max(_norm(_sub(a.position, com)) for a in members)
        return _Cluster(com, total, size, [a.agent_id for a in members])

    # -- carry-lookahead gradient routing --------------------------------------

    def carry_lookahead_scan(
        self,
        values: Dict[str, float],
        op: Callable[[float, float], float] = lambda a, b: a + b,
        identity: float = 0.0,
    ) -> Dict[str, float]:
        """Work-efficient prefix aggregation over the agent hierarchy.

        The Blelloch up-sweep/down-sweep scan, run on the balanced binary tree
        of the sorted roster.  Given one scalar per agent (a gradient, a credit
        signal, a workload), every agent receives the fold of all agents that
        precede it in the canonical order.  The up-sweep aggregates partial
        sums (carries) up log2(N) levels; the down-sweep routes the carries back
        down -- the exact structure of carry-lookahead addition, executed in
        O(N log N) scalar operations by construction (log2(N) levels, O(N)
        scalar work per level).

        Args:
            values: per-agent input scalars (agents missing from the mapping
                contribute ``identity``).
            op: an associative binary operator (default: addition).
            identity: the operator's identity element.

        Returns:
            Per-agent exclusive prefix: agent k receives op over the values of
            all agents before k in the canonical order.

        Raises:
            ValueError: on an empty roster.
        """
        n = len(self.agents)
        if n == 0:
            raise ValueError("the topology needs at least one agent")
        order = [a.agent_id for a in sorted(self.agents, key=lambda a: a.agent_id)]
        xs = [float(values.get(i, identity)) for i in order]

        # Pad to a power of two with the identity (classic Blelloch scan).
        levels = max(1, (n - 1).bit_length())
        size = 1 << levels
        tree = [identity] * (2 * size)
        for i, x in enumerate(xs):
            tree[size + i] = x

        # Up-sweep: every internal node stores the inclusive fold of its
        # subtree (the aggregated "carry" of that block of agents).  Levels run
        # deepest-first so a parent is folded only after its children.
        for level in range(levels, 0, -1):
            for i in range(1 << (level - 1), 1 << level):
                tree[i] = op(tree[2 * i], tree[2 * i + 1])
        inclusive = tree[:]

        # Down-sweep: route the carries back down.  Each node's value is
        # replaced by its exclusive prefix: the fold over every agent before
        # its block.  log2(N) levels, O(N) work per level, O(N log N) total.
        tree[1] = identity
        for level in range(1, levels + 1):
            for i in range(1 << (level - 1), 1 << level):
                parent_prefix = tree[i]
                left, right = 2 * i, 2 * i + 1
                tree[left] = parent_prefix
                tree[right] = op(parent_prefix, inclusive[left])
        return {order[i]: tree[size + i] for i in range(n)}

    # -- external field effect & screening ------------------------------------

    def apply_context_field(
        self, agent_id: str, external_field: Sequence[float]
    ) -> List[float]:
        """The attended field on an agent under a uniform external context field.

        QUMOND translation (qumond_pm.py ``solve``): the external field enters
        additively before the interpolation, g_tot = g_internal + g_e, and the
        attended field is nu(|g_tot|/a0) g_tot.  A context window biases every
        agent the same way; the interpolation decides whether that bias or the
        swarm's internal pull dominates.

        Args:
            agent_id: the agent to evaluate.
            external_field: the uniform context vector (same dimension as the
                agents' positions).

        Returns:
            The attended field under the biased total coupling.

        Raises:
            KeyError: on unknown agent; ValueError on dimension mismatch.
        """
        if agent_id not in self._by_id:
            raise KeyError(f"unknown agent: {agent_id}")
        target = self._by_id[agent_id]
        if len(external_field) != len(target.position):
            raise ValueError("external field dimension mismatch")
        g_int = self._newtonian_field(
            self._root, target, excluded=frozenset({agent_id})
        )
        g_tot = [gi + ge for gi, ge in zip(g_int, external_field)]
        coupling = _norm(g_tot) / target.context_scale
        if coupling <= 0.0:
            return [0.0] * len(g_tot)
        return _scale(g_tot, nu_std(coupling))

    def sandbox_screening(
        self, external_field: Sequence[float]
    ) -> List[Dict[str, object]]:
        """Screening report: which agents are context-dominated (sandboxed).

        The external-field effect in QUMOND: when the internal dynamics are
        weak relative to the external field, the system is in the
        external-field-dominated (screened) regime.  Per agent this function
        reports the internal and external coupling magnitudes, the ratio, the
        screening flag (external >= internal), and the QUMOND far-field
        amplification factor nu_e (1 + L_e/3) evaluated at the external
        coupling -- the factor by which a sandbox over-weights the shared
        context relative to its naive strength.

        Args:
            external_field: the uniform context vector.

        Returns:
            A list of per-agent screening records, sorted by agent id.
        """
        report: List[Dict[str, object]] = []
        for agent in sorted(self.agents, key=lambda a: a.agent_id):
            g_int = self._newtonian_field(
                self._root, agent, excluded=frozenset({agent.agent_id})
            )
            g_ext_norm = _norm(external_field)
            int_coupling = _norm(g_int) / agent.context_scale
            ext_coupling = g_ext_norm / agent.context_scale
            screened = ext_coupling >= int_coupling
            amplification = (
                far_field_monopole_ratio(ext_coupling) if ext_coupling > 0.0 else 1.0
            )
            report.append(
                {
                    "agent_id": agent.agent_id,
                    "internal_coupling": int_coupling,
                    "external_coupling": ext_coupling,
                    "screened": screened,
                    "far_field_amplification": amplification,
                }
            )
        return report
