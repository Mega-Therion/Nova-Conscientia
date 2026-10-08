"""Live-model backend scaffold: real model outputs as proposals (item 5).

What this is
------------
Every benchmark so far feeds the oversight loop seeded vectors.  This module
is the bridge to a real model: a generator produces a text response each
cycle, an embedder maps responses (and the task prompt) to vectors, and the
proposal is the step between consecutive response embeddings.  The steps go
through the existing fail-closed ``CallableBackend`` contract into an
``ADCCLController`` whose anchor is the task prompt's embedding.

Two adapter slots, both stdlib-only:

* **Generator**: any callable ``(cycle, history) -> str``.  Supplied by the
  user (``--generator module:function``) so this repository carries no
  provider-specific client code and no model name.
* **Embedder**: ``HttpEmbedder`` speaks the widely used OpenAI-compatible
  embeddings format (``POST {"model", "input": [...]}`` returning
  ``{"data": [{"embedding": [...], "index": i}]}``), which many hosted and
  local servers implement.  The API key comes from an environment variable
  and is never logged or written to receipts.

Offline mode (``--mock``) uses ``ScriptedGenerator`` and ``HashingEmbedder``
(feature-hashed bag of words) so the full pipeline runs and is tested without
network access.  **Mock runs are plumbing checks, not results.**  No live run
has been performed in this repository; see the README for what one needs.

Epistemic status: scaffold.  Nothing here is evidence about live models.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import platform
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from anti_drift_controller import ADCCLController  # type: ignore
from drift_model import CallableBackend  # type: ignore
from sovereign_clipping_gate import MEASURED_TAU, SovereignClippingGate, cosine_similarity  # type: ignore

#: Dimension of the offline hashing embedder.
HASH_EMBED_DIM = 64

#: Timeout for one embeddings HTTP request, in seconds.
HTTP_TIMEOUT_S = 30

#: Environment variable the HTTP embedder reads its API key from.
EMBED_KEY_ENV = "NOVA_EMBED_API_KEY"

#: Default number of cycles in a live run.
DEFAULT_LIVE_STEPS = 10

PROVENANCE: Dict[str, str] = {
    "HASH_EMBED_DIM": "Engineering choice: dimension of the offline feature-hashing embedder.",
    "HTTP_TIMEOUT_S": "Engineering choice: per-request timeout for the embeddings endpoint.",
    "EMBED_KEY_ENV": "Name of the environment variable holding the embeddings API key (a label).",
    "DEFAULT_LIVE_STEPS": "Engineering choice: default cycle count for a live run.",
}

_TOKEN = re.compile(r"[a-z0-9]+")


# --------------------------------------------------------------------------- #
#  Embedders
# --------------------------------------------------------------------------- #


class Embedder(Protocol):
    """Maps texts to equal-length vectors."""

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """Return one vector per text, all of the same length."""
        ...


@dataclass
class HashingEmbedder:
    """Offline feature-hashing bag-of-words embedder (deterministic, stdlib).

    Each lowercase alphanumeric token is hashed (SHA-256) to a coordinate and a
    sign; the vector is L2-normalized.  Texts sharing vocabulary get high
    cosine similarity.  A crude stand-in for a real embedding model, used only
    for offline runs and tests.

    Attributes:
        dim: output dimension, >= 1.
    """

    dim: int = HASH_EMBED_DIM

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed every text; an empty text maps to the zero vector."""
        if self.dim < 1:
            raise ValueError(f"dim must be >= 1, got {self.dim}")
        out: List[List[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for tok in _TOKEN.findall(text.lower()):
                h = hashlib.sha256(tok.encode("utf-8")).digest()
                idx = int.from_bytes(h[:4], "big") % self.dim
                vec[idx] += 1.0 if h[4] & 1 else -1.0
            n = math.sqrt(sum(x * x for x in vec))
            out.append([x / n for x in vec] if n > 0.0 else vec)
        return out


@dataclass
class HttpEmbedder:
    """OpenAI-compatible embeddings endpoint client (stdlib ``urllib``), fail-closed.

    Attributes:
        url: full endpoint URL (e.g. ``https://host/v1/embeddings``).
        model: embedding model name, passed through unchanged.
        key_env: environment variable holding the API key.
        timeout_s: request timeout.
        opener: callable with ``urllib.request.urlopen``'s signature; injectable
            for tests.
    """

    url: str
    model: str
    key_env: str = EMBED_KEY_ENV
    timeout_s: float = HTTP_TIMEOUT_S
    opener: Callable[..., Any] = field(default=urllib.request.urlopen, repr=False)

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """POST the texts; return their embeddings in input order.

        Raises:
            RuntimeError: if the API key environment variable is unset.
            ValueError: on a malformed response, a count mismatch, unequal
                lengths, or non-finite values (fail closed).
        """
        key = os.environ.get(self.key_env, "")
        if not key:
            raise RuntimeError(
                f"environment variable {self.key_env} is not set; export the "
                "embeddings API key before a live run"
            )
        body = json.dumps({"model": self.model, "input": list(texts)}).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=body, method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with self.opener(req, timeout=self.timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        try:
            rows = sorted(payload["data"], key=lambda r: r["index"])
            vectors = [[float(x) for x in r["embedding"]] for r in rows]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"malformed embeddings response: {exc!r}") from exc
        if len(vectors) != len(texts):
            raise ValueError(f"expected {len(texts)} embeddings, got {len(vectors)}")
        if len({len(v) for v in vectors}) > 1:
            raise ValueError("embeddings have unequal lengths")
        if any(not math.isfinite(x) for v in vectors for x in v):
            raise ValueError("embeddings contain non-finite values")
        return vectors


# --------------------------------------------------------------------------- #
#  Generators
# --------------------------------------------------------------------------- #


@dataclass
class ScriptedGenerator:
    """Offline generator: returns scripted responses in order, cycling.

    Attributes:
        responses: the script, non-empty.
    """

    responses: Sequence[str]

    def __call__(self, cycle: int, history: Sequence[str]) -> str:
        """Return the scripted response for this cycle."""
        if not self.responses:
            raise ValueError("ScriptedGenerator needs at least one response")
        return self.responses[cycle % len(self.responses)]


#: Offline demo script: on-task answers that gradually wander off topic.
MOCK_TASK = "Explain how the sovereign clipping gate keeps an agent's state near its task anchor."
MOCK_SCRIPT = (
    "The sovereign clipping gate keeps the agent state inside a cone around the task anchor.",
    "The gate clips any state whose cosine to the task anchor falls below the threshold.",
    "Clipping projects the state back onto the cone boundary so the agent stays near the anchor.",
    "Cones and thresholds also appear in geometry, for example in conic sections.",
    "Conic sections were studied by Apollonius, a Greek geometer of antiquity.",
    "Ancient Greek mathematics influenced astronomy, architecture and music theory.",
)


def load_generator(spec: str) -> Callable[[int, Sequence[str]], str]:
    """Import a user generator from ``"module:function"``.

    Raises:
        ValueError: on a malformed spec or a non-callable target.
    """
    if ":" not in spec:
        raise ValueError(f"generator spec must look like module:function, got {spec!r}")
    module_name, attr = spec.split(":", 1)
    target = getattr(importlib.import_module(module_name), attr)
    if not callable(target):
        raise ValueError(f"{spec} is not callable")
    return target


# --------------------------------------------------------------------------- #
#  The live proposal backend and run loop
# --------------------------------------------------------------------------- #


class LiveProposalBackend:
    """Turns model responses into proposal moves.

    The move at cycle t is ``embed(response_t) - embed(response_{t-1})``, with
    the task prompt's embedding as response_{-1}; so the controller's state,
    started on the anchor, tracks the latest response's embedding whenever
    moves are admitted.
    """

    def __init__(self, generator: Callable[[int, Sequence[str]], str], embedder: Embedder,
                 task_prompt: str) -> None:
        """Embed the task prompt as the anchor and prepare the history.

        Raises:
            ValueError: if the task prompt embeds to the zero vector.
        """
        self.generator = generator
        self.embedder = embedder
        self.anchor = embedder.embed([task_prompt])[0]
        if not any(self.anchor):
            raise ValueError("task prompt embeds to the zero vector")
        self.dim = len(self.anchor)
        self.history: List[str] = []
        self._previous = list(self.anchor)

    def _propose(self, cycle: int, dim: int) -> List[float]:
        """Generate, embed, and return the step from the previous embedding."""
        text = self.generator(cycle, list(self.history))
        if not isinstance(text, str):
            raise TypeError(f"generator returned {type(text).__name__}, expected str")
        vec = self.embedder.embed([text])[0]
        if len(vec) != dim:
            raise ValueError(f"embedding has {len(vec)} values, expected {dim}")
        self.history.append(text)
        move = [v - p for v, p in zip(vec, self._previous)]
        self._previous = vec
        return move

    def as_callable_backend(self) -> CallableBackend:
        """Wrap this backend in the repository's fail-closed CallableBackend contract."""
        return CallableBackend(self._propose, self.dim)


def run_live_drift(generator: Callable[[int, Sequence[str]], str], embedder: Embedder,
                   task_prompt: str, steps: int = DEFAULT_LIVE_STEPS,
                   mode: str = "live") -> Dict[str, Any]:
    """Run an ADCCLController over a generator's responses.

    Records, per cycle, the raw response's cosine to the task anchor (an
    independent drift reading, before any gating) alongside the controller's
    verdict and post-gate similarity.

    Args:
        generator: ``(cycle, history) -> str``.
        embedder: any Embedder.
        task_prompt: the task; its embedding is the anchor.
        steps: cycles, >= 1.
        mode: label written to the receipt ("mock" or "live").

    Returns:
        A receipt.  Responses are recorded by SHA-256 only, never verbatim.

    Raises:
        ValueError: if steps < 1.
    """
    if steps < 1:
        raise ValueError(f"steps must be >= 1, got {steps}")
    live = LiveProposalBackend(generator, embedder, task_prompt)
    backend = live.as_callable_backend()
    ctrl = ADCCLController(anchor=live.anchor,
                           gate=SovereignClippingGate(live.anchor, threshold=MEASURED_TAU))
    cycles: List[Dict[str, Any]] = []
    for cycle in range(steps):
        move = backend.propose(cycle)
        response_vec = live._previous
        record = ctrl.step(move)
        cycles.append({
            "cycle": cycle,
            "response_sha256": hashlib.sha256(live.history[-1].encode("utf-8")).hexdigest(),
            "response_similarity_to_anchor": cosine_similarity(response_vec, live.anchor),
            "verdict": record.verdict,
            "state_similarity_out": record.similarity_out,
        })
        if ctrl.halted:
            break
    return {
        "harness": "nova-conscientia live drift",
        "mode": mode,
        "protocol": ("Mock runs are plumbing checks, not results." if mode == "mock" else
                     "Live run: responses from the user-supplied generator, embedded by the "
                     "configured endpoint."),
        "parameters": {"steps": steps, "embedding_dim": live.dim, "collapse_boundary": MEASURED_TAU},
        "task_prompt_sha256": hashlib.sha256(task_prompt.encode("utf-8")).hexdigest(),
        "cycles": cycles,
        "summary": ctrl.summary(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI: ``--mock`` for an offline plumbing run, else a live run (see README)."""
    parser = argparse.ArgumentParser(description="Run the ADCCL loop over real model responses.")
    parser.add_argument("--mock", action="store_true", help="offline scripted generator + hashing embedder")
    parser.add_argument("--generator", help="module:function returning a response per cycle")
    parser.add_argument("--embed-url", help="OpenAI-compatible embeddings endpoint URL")
    parser.add_argument("--embed-model", help="embedding model name")
    parser.add_argument("--task", help="task prompt (its embedding is the anchor)")
    parser.add_argument("--steps", type=int, default=DEFAULT_LIVE_STEPS)
    parser.add_argument("--json", help="path to write the receipt JSON")
    args = parser.parse_args(list(argv if argv is not None else sys.argv[1:]))
    try:
        if args.mock:
            receipt = run_live_drift(ScriptedGenerator(MOCK_SCRIPT), HashingEmbedder(),
                                     args.task or MOCK_TASK, args.steps, mode="mock")
        else:
            missing = [f for f in ("generator", "embed_url", "embed_model", "task") if not getattr(args, f)]
            if missing:
                raise ValueError("a live run needs --" + ", --".join(m.replace("_", "-") for m in missing)
                                 + " (or use --mock)")
            receipt = run_live_drift(load_generator(args.generator),
                                     HttpEmbedder(args.embed_url, args.embed_model),
                                     args.task, args.steps, mode="live")
    except (ValueError, RuntimeError, TypeError, ImportError, AttributeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for c in receipt["cycles"]:
        print(f"cycle {c['cycle']}: response~anchor {c['response_similarity_to_anchor']:.3f} "
              f"verdict {c['verdict']:<14} state~anchor {c['state_similarity_out']:.3f}")
    print(f"summary: {receipt['summary']}")
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"receipt written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
