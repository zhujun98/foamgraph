import pytest

import numpy as np

from foamgraph.algorithms import quick_min_max


class TestStatistics:
    def testQuickMinMax(self):
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
