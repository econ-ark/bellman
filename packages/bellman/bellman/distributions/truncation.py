"""The numbers of a lognormal law truncated to an interval of the draw.

`TruncatedLogNormal(μ, σ, l, u)` is the law of exp(μ + σ·Z), Z a standard
normal, conditional on l ≤ exp(μ + σ·Z) ≤ u, with σ > 0 and 0 ≤ l < u ≤ ∞
(AMD-SG-036 §2). In the standard-normal variable the window is [z_l, z_u]
with z_l = (ln l − μ)/σ, −∞ at l = 0, and z_u = (ln u − μ)/σ, ∞ at u = ∞:
`standardized_window` gives the two ends, `mass` the probability
Φ(z_u) − Φ(z_l) a standard normal gives the window, read in the tail that
keeps the difference of two values of Φ from cancelling, `density` the
standard normal density, and `support` the interval the draw takes values
in, [l, u] with an end at 0 or at ∞ not attained. Every function takes and
returns Python floats; none reads a stage. The comparator of
`packages/meaning-map-training` integrates the family with them.
"""

from __future__ import annotations

import math
from typing import NamedTuple

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def density(z: float) -> float:
    """The standard normal density at z; zero at an infinite z."""
    return 0.0 if math.isinf(z) else math.exp(-0.5 * z * z) / _SQRT2PI


def mass(lower: float, upper: float) -> float:
    """Φ(upper) − Φ(lower), the probability a standard normal gives
    [lower, upper], read in the tail that keeps the difference from
    cancelling."""
    if lower >= 0.0:
        return 0.5 * (math.erfc(lower / _SQRT2) - math.erfc(upper / _SQRT2))
    if upper <= 0.0:
        return 0.5 * (math.erfc(-upper / _SQRT2) - math.erfc(-lower / _SQRT2))
    return 1.0 - 0.5 * (math.erfc(upper / _SQRT2) + math.erfc(-lower / _SQRT2))


def standardized_window(mean: float, deviation: float, lower: float, upper: float):
    """The ends of the truncation window in the standard-normal variable,
    ((ln l − μ)/σ, (ln u − μ)/σ), with −∞ at l = 0 and ∞ at u = ∞."""
    low = -math.inf if lower == 0.0 else (math.log(lower) - mean) / deviation
    high = math.inf if math.isinf(upper) else (math.log(upper) - mean) / deviation
    return low, high


class Support(NamedTuple):
    """The interval the draw takes values in: its ends, and whether each end
    is attained. The end 0 and the end ∞ are not attained."""

    lower: float
    lower_closed: bool
    upper: float
    upper_closed: bool


def support(lower: float, upper: float) -> Support:
    """The support of the truncated draw, [l, u], open at a lower endpoint 0
    and at an upper endpoint ∞."""
    return Support(lower, lower > 0.0, upper, not math.isinf(upper))
