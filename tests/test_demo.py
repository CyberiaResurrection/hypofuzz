"""Tests for the hypofuzz library."""

import json
from itertools import islice

import hypothesis.strategies as st
from hypothesis import assume
from hypothesis.internal.conjecture.data import Status

import hypofuzz

JSON_STRATEGY = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(),
    extend=lambda x: st.lists(x, max_size=3)
    | st.dictionaries(st.text(), x, max_size=3),
)


def encode_decode(x):
    assert x == json.loads(json.dumps(x))


def test_fuzz_demo():
    fuzzer = hypofuzz.FuzzProcess(
        encode_decode, JSON_STRATEGY.map(lambda x: ((), {"x": x}))
    )
    fuzzer.startup()
    for _ in range(100):
        fuzzer.run_one()

    results = {r.status for r in fuzzer.pool}
    assert Status.INTERESTING in results
    assert Status.VALID in results


def test_fuzz_status_demo():
    gen = hypofuzz.fuzz_in_generator(
        test=encode_decode,
        strategy=(
            st.lists(st.floats()).map(lambda x: assume(x) and x)
            | st.binary(min_size=10_000, max_size=10_000)
        ).map(lambda x: ((), {"x": x})),
    )
    results = {r.status for r in islice(gen, 100)}
    # Sees all statuses: OVERRUN when asked for too many bytes, INVALID when
    # the all-zero example fails the filter, VALID for most examples, and
    # INTERESTING when `nan` is in the list.
    assert results == set(Status)
