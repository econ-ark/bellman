"""Build TestSpec records from merged slot bundles."""

from __future__ import annotations

from typing import Any

from .types import TestSpec


def make_test(slot_bundles: list[dict[str, Any]]) -> tuple[TestSpec, ...]:
    """Wrap each fully-merged slot bundle in a TestSpec; the caller forms the
    bundles, their Cartesian product included."""
    if not slot_bundles:
        return (TestSpec(),)
    return tuple(TestSpec(slots=dict(b)) for b in slot_bundles)
