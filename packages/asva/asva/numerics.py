"""Generic numerical utilities for DDSL stage operators.

Model-agnostic clamping: ``clamp_value`` replaces the NaN and
infinite entries of a value array by a large negative number;
``clamp_policy`` and ``clamp_scalar`` bring a policy array or
a scalar within given bounds and replace a NaN.
"""

import numpy as np
from numba import njit


@njit
def clamp_value(arr, nan_val=-1e10):
    """Clamp NaN/inf in value arrays.

    NaN -> large negative so state is never chosen.
    """
    result = arr.copy()
    for i in range(len(result)):
        if np.isnan(result[i]) or np.isinf(result[i]):
            result[i] = nan_val
    return result


@njit
def clamp_policy(arr, min_val, max_val):
    """Clamp NaN/inf in policy arrays to valid bounds."""
    result = arr.copy()
    for i in range(len(result)):
        if np.isnan(result[i]):
            result[i] = min_val
        elif result[i] < min_val:
            result[i] = min_val
        elif result[i] > max_val or np.isinf(result[i]):
            result[i] = max_val
    return result


@njit
def clamp_scalar(val, min_val, max_val, nan_replacement):
    """Clamp a single scalar value.

    Returns nan_replacement if NaN.
    """
    if np.isnan(val):
        return nan_replacement
    elif np.isinf(val):
        return max_val if val > 0 else min_val
    elif val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    return val
