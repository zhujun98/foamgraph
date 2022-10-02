"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Optional

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
    return (np.nanquantile(x, 1 - q, method='nearest'),
            np.nanquantile(x, q, method='nearest'))


def intersection(rect1: tuple, rect2: tuple) -> tuple:
    """Calculate the intersection area of two rectangles."""
    x = max(rect1[0], rect2[0])
    xx = min(rect1[0] + rect1[2], rect2[0] + rect2[2])
    y = max(rect1[1], rect2[1])
    yy = min(rect1[1] + rect1[3], rect2[1] + rect2[3])
    return x, y, xx - x, yy - y  # (x, y, w, h)


def extract_rect_roi(img: np.ndarray, rect: tuple) \
        -> Optional[np.ndarray]:
    """Extract rectangular ROI from an image."""
    x, y, w, h = intersection((0, 0, img.shape[1], img.shape[0]), rect)
    if w <= 0 or h <= 0:
        return
    return img[y:y+h, x:x+w]
