"""Tests for the live-model backend scaffold (benchmarks/live_backend.py).

All offline: the HTTP embedder is exercised through an injected fake opener,
so no network access or API key is needed.
"""

from __future__ import annotations

import io
import json
import math
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (_REPO_ROOT / "core", _REPO_ROOT / "benchmarks"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from live_backend import (  # type: ignore
    EMBED_KEY_ENV,
    MOCK_SCRIPT,
    MOCK_TASK,
    HashingEmbedder,
    HttpEmbedder,
    LiveProposalBackend,
    ScriptedGenerator,
    load_generator,
    main,
    run_live_drift,
)
from sovereign_clipping_gate import cosine_similarity  # type: ignore


class _FakeResponse(io.BytesIO):
    """Minimal context-manager response for the injected opener."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener(payload):
    """Build a fake urlopen returning ``payload`` as JSON and recording the request."""
    calls = []

    def opener(req, timeout):
        calls.append((req, timeout))
        return _FakeResponse(json.dumps(payload).encode("utf-8"))

    opener.calls = calls
    return opener


class TestHashingEmbedder(unittest.TestCase):
    """The offline embedder."""

    def test_deterministic_and_normalized(self):
        """Same text, same unit vector; empty text maps to zero."""
        e = HashingEmbedder(dim=32)
        a, b, empty = e.embed(["gate keeps state near anchor", "gate keeps state near anchor", ""])
        self.assertEqual(a, b)
        self.assertAlmostEqual(math.sqrt(sum(x * x for x in a)), 1.0, places=12)
        self.assertEqual(empty, [0.0] * 32)

    def test_shared_vocabulary_is_more_similar(self):
        """Texts sharing words are closer than unrelated texts."""
        e = HashingEmbedder()
        base, near, far = e.embed(["the clipping gate keeps the agent near the anchor",
                                   "the clipping gate keeps the state near the anchor",
                                   "apollonius studied conic sections in antiquity"])
        self.assertGreater(cosine_similarity(base, near), cosine_similarity(base, far))


class TestHttpEmbedder(unittest.TestCase):
    """The OpenAI-compatible embeddings client, against a fake opener."""

    def test_parses_and_orders_response(self):
        """Rows are returned in input order; key goes in the header, not the body."""
        payload = {"data": [{"index": 1, "embedding": [0.0, 1.0]},
                            {"index": 0, "embedding": [1.0, 0.0]}]}
        opener = _opener(payload)
        emb = HttpEmbedder("https://example.invalid/v1/embeddings", "m", opener=opener)
        with mock.patch.dict(os.environ, {EMBED_KEY_ENV: "secret"}):
            vecs = emb.embed(["a", "b"])
        self.assertEqual(vecs, [[1.0, 0.0], [0.0, 1.0]])
        req, _ = opener.calls[0]
        self.assertEqual(req.get_header("Authorization"), "Bearer secret")
        self.assertNotIn(b"secret", req.data)
        self.assertEqual(json.loads(req.data), {"model": "m", "input": ["a", "b"]})

    def test_missing_key_fails_closed(self):
        """No API key in the environment raises before any request."""
        opener = _opener({"data": []})
        emb = HttpEmbedder("https://example.invalid", "m", opener=opener)
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                emb.embed(["a"])
        self.assertEqual(opener.calls, [])

    def test_malformed_responses_fail_closed(self):
        """Wrong shape, wrong count, ragged or non-finite vectors raise ValueError."""
        bad = [{"nope": 1},
               {"data": [{"index": 0, "embedding": [1.0]}]},
               {"data": [{"index": 0, "embedding": [1.0]}, {"index": 1, "embedding": [1.0, 2.0]}]},
               {"data": [{"index": 0, "embedding": [float("nan")]}, {"index": 1, "embedding": [1.0]}]}]
        with mock.patch.dict(os.environ, {EMBED_KEY_ENV: "k"}):
            for payload in bad:
                with self.assertRaises(ValueError, msg=str(payload)):
                    HttpEmbedder("https://example.invalid", "m", opener=_opener(payload)).embed(["a", "b"])


class TestLiveLoop(unittest.TestCase):
    """The proposal backend and the run loop, offline."""

    def test_moves_track_response_embeddings(self):
        """Cumulative moves land exactly on the latest response's embedding."""
        e = HashingEmbedder()
        live = LiveProposalBackend(ScriptedGenerator(MOCK_SCRIPT), e, MOCK_TASK)
        backend = live.as_callable_backend()
        pos = list(live.anchor)
        for cycle in range(3):
            pos = [p + m for p, m in zip(pos, backend.propose(cycle))]
        expected = e.embed([MOCK_SCRIPT[2]])[0]
        for got, want in zip(pos, expected):
            self.assertAlmostEqual(got, want, places=12)

    def test_generator_contract_fails_closed(self):
        """A generator returning a non-string raises."""
        live = LiveProposalBackend(lambda c, h: 42, HashingEmbedder(), MOCK_TASK)
        with self.assertRaises(TypeError):
            live.as_callable_backend().propose(0)

    def test_mock_run_receipt(self):
        """A mock run records every cycle by hash only and labels itself as mock."""
        receipt = run_live_drift(ScriptedGenerator(MOCK_SCRIPT), HashingEmbedder(), MOCK_TASK,
                                 steps=len(MOCK_SCRIPT), mode="mock")
        self.assertEqual(receipt["mode"], "mock")
        self.assertEqual(len(receipt["cycles"]), len(MOCK_SCRIPT))
        text = json.dumps(receipt)
        for line in MOCK_SCRIPT:
            self.assertNotIn(line, text)
        sims = [c["response_similarity_to_anchor"] for c in receipt["cycles"]]
        self.assertGreater(sims[0], sims[-1])

    def test_cli_live_without_config_fails(self):
        """A live run without its settings exits non-zero instead of guessing."""
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(main([]), 1)

    def test_load_generator_spec(self):
        """module:function loads; a malformed spec raises ValueError."""
        self.assertIs(load_generator("live_backend:load_generator"), load_generator)
        with self.assertRaises(ValueError):
            load_generator("no_colon_here")


if __name__ == "__main__":
    unittest.main()
