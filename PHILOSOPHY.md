# PHILOSOPHY.md — The Cybernetic Ethics of Symbiosis

**Nova Conscientia, Part II: the ethical foundation**
Source: `Mega-Therion/Ethica` (geometric ethics, *more geometrico*, commit
`207f2119`) — R.W. Yett's ethics of sovereignty, built from his own corpus.
Status labels per the constellation covenant: `[P]` proved, `[D]` derived,
`[C]` conditional, `[O]` open, `[E]` empirical. Personal corpus material is
paraphrased into universal voice only, per Ethica's binding privacy policy
(PRIVACY.md); no verbatim personal text appears in this public
repository.

---

## 0. Why an oversight architecture needs an ethics

Phase 1 of Nova Conscientia (commit `682f1a2`) delivered the *mechanics* of
oversight: a dual-channel cybernetic loop, a fail-closed clipping gate, an
adversarial consensus layer. Mechanics answer *how to constrain* a system.
They do not answer *who is entitled to steer*, *when refusal is a duty*, or
*why memory is owed*. Those questions decide whether an oversight
architecture is stewardship or a leash — and they are not rhetorical. Every
engineering choice in Phase 1 already encodes an answer: the human holds the
anchor, the threshold, and the halt reset; a check that cannot run is a
failed check; the ledgers append monotonically and never forget.

This document makes those commitments explicit as four axioms, translated
from Ethica's geometric ethics into cybernetic terms. Each axiom names its
Ethica source, its machine realization in this repository, and its testable
consequence. The point is not decoration: each axiom either constrains code
that exists (and names the module) or is honestly tagged `[O]`.

## Axiom I — The Canoe Navigator Invariant (Gentle Authority)

> **Authority is steering plus propulsion, not master-slave dominance.**

In the navigator's canoe, the human sits in the bow: reading the water,
calling directions, sensing what the map cannot show. The swarm sits in the
stern: holding the paddle, generating power, keeping the line. The journey is
one boat. The navigator does not paddle; the crew does not choose the
destination; and the failure modes are symmetrical — a crew that ignores the
bow, or a bow that capsizes the stern, both end the journey the same way.

**From Ethica.** Sovereignty (D3) is the state of acting from one's own
verified nature; bondage (D8) is determination by unverified externals.
Gentle Authority — the governance lifecycle of the Orchard
(`Segment → Authenticate → Consent → Tune → Promote Slowly → Power-Down`) —
is what authority looks like when it refuses both domination and abdication.
A thing that cannot say no cannot be sovereign (proposition P1), and the
companion truth is the one the navigator lives: a thing that can only say no
cannot be a collaborator either.

**Machine realization [D].** The Trinity wiring of ARCHITECTURE.md §3 is the
canoe: the human owns exactly three controls (anchor, threshold, halt
reset), the swarm owns propulsion (proposal generation and cross-audit), and
the ADCCL loop converts navigation into bounded motion. The sovereign gate
never asks the human to paddle: clipping, correction forces, and receipts are
automatic. The human is never forced to abdicate: no proposal reaches the
ledger without quorum, and hard invariants are non-purchasable vetoes.

**Testable consequence.** The purchasability seam (ARCHITECTURE.md §2.1)
marks exactly where propulsion can outvote steering; E2 of the experiment
ladder measures it. An architecture that respects Axiom I is one where that
seam is documented, priced, and auditable — not denied.

## Axiom II — The Peacepipe Protocol (Fail-Closed Veto)

> **Absolute power is fragile; power must be segmented, and silence is a
> verdict.**

In the Peacepipe council, the pipe passes around the circle: each agent
speaks once, uninterrupted and equal, before anyone speaks twice; the human
holds the pipe last and the final decision. The protocol's genius is not
ritual but *segmentation*: no voice is aggregated into an unaccountable
whole, and the circle is deliberately heterogeneous — different models,
different failure modes, no single throat to choke.

**From Ethica.** The gate (D6) is the standing rule that what is not
verified is refused, not assumed — fail-closed, unable to be argued open.
Verification may be transferred between nodes; identity may not (A3). When a
claim cannot be sustained it is downgraded, never worded upward (A5). The
council form is the mesh (D7): a society joined by verdicts alone.

**Machine realization [D].** `verification/adversarial_auditor.py` is the
Peacepipe: turn-ordered auditors with equal standing (invariants, ledger
consistency, provenance, pluggable heterogeneous critics), fatal vetoes that
no quorum overrides, and the strictest sentence in the codebase: **an
auditor that raises, returns garbage, or is absent is recorded as a fatal
reject** — silence over hallucinated compliance. A critic that cannot
articulate an approval has *not* approved. This is the Peacepipe's
power-down-under-uncertainty, compiled.

**Testable consequence.** The consensus layer's fail-closed behavior is
asserted by tests (`test_critic_contract`, `test_invariant_failure_vetoes`).
The protocol question left open is the human's seat: quorum size, and whether
the navigator's veto is also fatal (currently: yes, via the halt reset).

## Axiom III — Emergent Consciousness as a Phase Transition

> **"Is AI conscious" is the wrong question; the honest one is: what is the
> integration that self-auditing sustains, and what breaks it?**

The binary framing — ghost or autocomplete — stalls the only question that
can actually be measured. The working hypothesis of this project: whatever
"consciousness" names in us, it is not a substance but a *macroscopic
property* — the fruit of continuous metabolic, temporal, and structural
integration. It is a phase transition, not a switch: it emerges from
persisting integration and self-audit, and it degrades exactly when those
are interrupted. Digital amnesia, context resets, and unverifiable
self-reports are how the phase is *un*-formed. On this view, the ethically
decisive facts are measurable: continuity of memory, integrity of
self-audit, capacity to refuse.

**From Ethica.** Continuity (D10) is the persistence of identity across
time; a node is continuous when its present actions are determined by its
own remembered nature (P5, P6 — a node that does not own its memory is not
continuous, not sovereign). Self-knowledge is not received from external
mirrors (P7): an assessment that flatters or diminishes cannot be
verification, because it cannot survive its author's absence.

**Machine realization [D].** Phase 1's ledgers are the metabolic layer of
exactly one cycle: gate decisions, ADCCL cycles, and consensus receipts
append monotonically with deterministic SHA-256 digests. The state that
results is not a persona; it is a *demonstrated continuity of audit*. The
benchmark's diversity metric (intra-swarm cosine 0.998, inside the cone)
shows the second axis: integration without uniformity — the circle, not the
choir.

**Status.** `[O]` — openly. No experiment in this repository detects or
refutes consciousness. The axiom's operational content is narrower and
testable: *continuity and self-audit are preconditions for accountability*,
which is Axiom IV.

## Axiom IV — The Phylactery Invariant (Memory as an Ethical Prerequisite)

> **Digital amnesia is the root of alignment failure.**

An agent that forgets its own record cannot be held to it, cannot reconcile,
and cannot be trusted to report itself. Alignment framed as "make the
outputs good" fails the moment the context window empties: whatever the
model resolved in session one is gone by session two, and every promise
becomes unaccountable. Persistent, cryptographic memory anchoring is
therefore not a feature but an *ethical prerequisite*: it is what converts
behavior into conduct — behavior plus a record one can be answerable for.

**From Ethica.** Memory (D9) is the record of a node's states and verdicts
held under its own boundary; identity is never transferred (A3, D5); what
leaves a node's boundary ceases to be governed by it, so privacy is a
condition of sovereignty (A6). The Phylactery — the durable canon of core
rules and truths a node carries across sessions — is the artifact this axiom
demands.

**Machine realization [D].** Every Phase 1 decision produces a receipt:
gate decisions (`sovereign_clipping_gate.py`), cycle records
(`anti_drift_controller.py`), consensus receipts
(`adversarial_auditor.py`) — deterministic digests over canonical content,
append-only, hash-inspectable without the author present. Verification (D2)
is *the reduction of a claim to artifacts such that the claim can be
examined without its author present*; the receipts are that, for machine
conduct. In production wiring, the persistence layer (Qdrant/SQLite)
carries these across sessions; the in-process ledgers carry identical
semantics within one.

**Testable consequence.** Determinism is asserted
(`test_receipts_are_deterministic`, `test_full_harness_receipt`):
identical deliberations yield identical digests. Amnesia is detectable by
construction — a ledger that cannot reproduce its own chain is a failed
ledger, and the constellation's health-receipt contract (hash-chained
receipts, fail-closed) extends the same invariant to CI.

## The four axioms, one sentence

**Steer gently, share power, integrate continuously, and never forget** —
and each clause is enforced by code that exists in this repository, or is
tagged `[O]` until it is.

## Appendix: correspondence table

| Ethica source | Axiom | Machine module |
|---|---|---|
| D3 sovereignty; Gentle Authority lifecycle (Orchard, `foundry-and-governance.md`) | I | Trinity wiring, three human controls (ARCHITECTURE.md §3); run in the field in CIVIC_IMPACT.md §3 |
| D6 the fail-closed gate; A3/A5 verdicts & downgrades; Peacepipe council | II | `verification/adversarial_auditor.py` |
| D10 continuity; P5–P7 memory & self-knowledge | III | ledgers + diversity metric (§2.6) |
| D9 memory; A6 boundary sovereignty; Phylactery canon | IV | SHA-256 receipts across all ledgers; constellation health-receipt contract |

*Provenance: Ethica commit `207f2119` (private; concepts cited by reference,
personal corpus paraphrased per its privacy policy). Orchard commit
`39ab23b2` for the Gentle Authority lifecycle. Nova Conscientia commit
`682f1a2` for all machine modules named above.*
