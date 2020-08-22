"""
Distributed under the terms of the MIT License.

The full license is in the file BSD_LICENSE, distributed with this software.

Copyright (C) Jun Zhu. All rights reserved.
"""
import numpy as np


def quick_min_max(x, q=None):
    """Estimate the min/max values of input by down-sampling.

    :param numpy.ndarray x: data, 2D array for now.
    :param float/None q: quantile when calculating the min/max, which
        must be within [0, 1].

    :return tuple: (min, max)
    """
    if not isinstance(x, np.ndarray):
        raise TypeError("Input must be a numpy.ndarray!")

    if x.ndim != 2:
        raise ValueError("Input must be a 2D array!")

    while x.size > 1e5:
        sl = [slice(None)] * x.ndim
        sl[np.argmax(x.shape)] = slice(None, None, 2)
        x = x[tuple(sl)]

    if q is None:
        return np.nanmin(x), np.nanmax(x)

    if q < 0.5:
        q = 1 - q

    # Let np.nanquantile to handle the case when q is outside [0, 1]
    # caveat: nanquantile is about 30 times slower than nanmin/nanmax
    return (np.nanquantile(x, 1 - q, interpolation='nearest'),
            np.nanquantile(x, q, interpolation='nearest'))
