"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from enum import Enum
from typing import Any, Optional

import numpy as np

from .data_item_base import DataItemBase


class ROIDataItem(DataItemBase):

    class Analysis(Enum):
        PROJECTION_X = 0
        PROJECTION_Y = 1

    def __init__(self, data: Optional[np.ndarray] = None):
        super().__init__(data)

    def get(self, type_: Analysis = Analysis.PROJECTION_X) -> Any:
        """Override."""
        if self._data is None:
            return None, None

        if type_ == self.Analysis.PROJECTION_X:
            y = np.mean(self._data, axis=0)
            return np.arange(len(y)), y

        if type_ == self.Analysis.PROJECTION_Y:
            y = np.mean(self._data, axis=1)
            return np.arange(len(y)), y
