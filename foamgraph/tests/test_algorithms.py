import pytest

import numpy as np

from foamgraph.algorithms import (
    extract_rect_roi, quick_min_max, intersection
)


def test_quick_min_max():
    # test array size <= 1e5
    arr = np.array([[np.nan, 1, 2, 3, 4], [5, 6, 7, 8, np.nan]])
    assert quick_min_max(arr) == (1., 8.)
    assert quick_min_max(arr, q=1.0) == (1, 8)
    assert quick_min_max(arr, q=0.9) == (2, 7)
    assert quick_min_max(arr, q=0.7) == (3, 6)
    assert quick_min_max(arr, q=0.3) == (3, 6)

    with pytest.raises(ValueError):
        quick_min_max(arr, q=1.1)

    # test array size > 1e5
    arr = np.ones((1000, 1000), dtype=np.float32)
    assert quick_min_max(arr) == (1, 1)
    assert quick_min_max(arr, q=0.9) == (1, 1)

    arr[::3] = 2
    assert quick_min_max(arr) == (1., 2.)
    assert quick_min_max(arr, q=0.9) == (1, 2)


def test_intersection():
    # one contains the other
    assert intersection((0, 0, 100, 80), (0, 0, 50, 30)) == (0, 0, 50, 30)
    assert intersection((0, 0, 50, 30), (0, 0, 100, 80)) == (0, 0, 50, 30)
    assert intersection((5, 2, 10, 5), (0, 0, 50, 50)) == (5, 2, 10, 5)
    assert intersection((0, 0, 50, 50), (5, 2, 10, 5)) == (5, 2, 10, 5)

    # no interaction
    assert intersection((0, 0, 100, 100), (-10, -10, 5, 5)) == (0, 0, -5, -5)
    assert intersection((-10, -10, 5, 5), (0, 0, 100, 100)) == (0, 0, -5, -5)
    assert intersection((0, 0, 100, 100), (-10, -10, 10, 10)) == (0, 0, 0, 0)
    assert intersection((-10, -10, 10, 10), (0, 0, 100, 100)) == (0, 0, 0, 0)

    # partially intersect
    assert intersection((0, 0, 10, 10), (-10, -10, 15, 15)) == (0, 0, 5, 5)
    assert intersection((-10, -10, 15, 15), (0, 0, 10, 10)) == (0, 0, 5, 5)

    assert intersection((1, 1, 10, 10), (5, 10, 15, 15)) == (5, 10, 6, 1)
    assert intersection((5, 10, 15, 15), (1, 1, 10, 10)) == (5, 10, 6, 1)

    assert intersection((0, 0, 10, 20), (2, -2, 4, 24)) == (2, 0, 4, 20)
    assert intersection((2, -2, 4, 24), (0, 0, 10, 20)) == (2, 0, 4, 20)


def test_extract_rect_roi():
    assert extract_rect_roi(np.ones((10, 10)), (-10, -10, 15, 15)).shape == (5, 5)
    assert extract_rect_roi(np.ones((100, 100)), (-10, -10, 5, 5)) is None
