"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from abc import ABC, abstractmethod
from typing import Any


class DataItemBase(ABC):

    def __init__(self, data=None):
        self._data = data

    def setData(self, data) -> None:
        self._data = data

    @abstractmethod
    def get(self, type_) -> Any:
        ...
