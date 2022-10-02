"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import abc


class _Config(abc.Mapping):
    """Readonly config."""

    _data = {
        # foreground/background color (r, g, b, alpha)
        "FOREGROUND_COLOR": (0, 0, 0, 255),
        "BACKGROUND_COLOR": (225, 225, 225, 255),
        # color map in contour plots, valid options are: thermal, flame,
        # yellowy, bipolar, spectrum, cyclic, greyclip, grey, viridis,
        # inferno, plasma, magma
        "COLOR_MAP": 'plasma',
    }

    def __init__(self):
        super().__init__()

    def __contains__(self, key):
        """Override."""
        return self._data.__contains__(key)

    def __getitem__(self, key):
        """Override."""
        return self._data.__getitem__(key)

    def __len__(self):
        """Override."""
        return self._data.__len__()

    def __iter__(self):
        """Override."""
        return self._data.__iter__()


config = _Config()
