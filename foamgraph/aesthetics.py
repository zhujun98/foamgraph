"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from typing import Union

import numpy as np

from .backend.QtCore import QPointF, Qt
from .backend.QtGui import QBrush, QColor, QLinearGradient, QPen, QPalette

from .pyqtgraph_be import functions as fn

from .config import config


class QualitativeColor:

    foreground = config["FOREGROUND_COLOR"]  # black
    background = config["BACKGROUND_COLOR"]  # white-like

    k = (0, 0, 0)  # black
    i = (251, 154, 153)  # pink
    r = (227, 26, 28)  # red
    o = (255, 127, 0)  # orange
    y = (255, 255, 153)  # yellow
    c = (166, 206, 227)  # cyan
    b = (31, 120, 180)  # blue
    s = (178, 223, 138)  # grass green
    g = (51, 160, 44)  # green
    p = (106, 61, 154)  # purple
    d = (202, 178, 214)  # orchid
    n = (177, 89, 40)  # brown
    v = (192, 192, 192)  # silver
    w = (255, 255, 255)  # white

    roi = (255, 255, 255)
    roi_hover = (255, 255, 0)
    roi_handle = (150, 255, 255)
    roi_handle_hover = (255, 255, 0)

    @classmethod
    def mkColor(cls, c, *, alpha=255):
        return QColor(*getattr(cls, c), alpha)

    @classmethod
    def mkPen(cls, c, *, alpha=255, width=1, style=Qt.PenStyle.SolidLine):
        if c is None:
            return QPen(QColor(0, 0, 0, 0), width, Qt.PenStyle.NoPen)
        pen = QPen(QColor(*getattr(cls, c), alpha), width, style)
        pen.setCosmetic(True)
        return pen

    @classmethod
    def mkBrush(cls, c, *, alpha=255):
        if c is None:
            return QBrush(QColor(0, 0, 0, 0), Qt.BrushStyle.NoBrush)
        return QBrush(QColor(*getattr(cls, c), alpha))


FColor = QualitativeColor


class SequentialColor:

    # red
    r = [
        (153, 0, 13),
        (203, 24, 29),
        (239, 59, 44),
        (251, 106, 74),
        (252, 146, 114)
    ]
    # blue
    b = [
        (158, 202, 225),
        (107, 174, 214),
        (66, 146, 198),
        (33, 113, 181),
        (8, 69, 148),
    ]
    # magenta
    m = [
        (74, 20, 134),
        (106, 81, 163),
        (128, 125, 186),
        (158, 154, 200),
        (188, 189, 220)
    ]
    # green
    g = [
        (161, 217, 155),
        (116, 196, 118),
        (65, 171, 93),
        (35, 139, 69),
        (0, 90, 50),
    ]

    pool = r + b + m + g

    @classmethod
    def _validate_n(cls, n):
        if not isinstance(n, int) or n <= 0:
            raise ValueError("n must be a positive integer!")

    @classmethod
    def mkColor(cls, n, *, alpha=255):
        """Generate n QColors via sequential colors.

        The colors will be repeated if n is larger than the number of
        pre-defined colors.

        :param int n: number of colors.
        """
        cls._validate_n(n)
        lst = cls.pool * (int(n/len(cls.pool)) + 1)
        for c in lst[:n]:
            yield QColor(*c, alpha)

    @classmethod
    def mkPen(cls, n, *, alpha=255, width=1, style=Qt.PenStyle.SolidLine):
        """Generate n QPens via sequential colors.

        The colors will be repeated if n is larger than the number of
        pre-defined colors.

        :param int n: number of colors.
        """
        cls._validate_n(n)
        lst = cls.pool * (int(n/len(cls.pool)) + 1)
        for c in lst[:n]:
            pen = QPen(QColor(*c, alpha), width, style)
            pen.setCosmetic(True)
            yield pen

    @classmethod
    def mkBrush(cls, n, *, alpha=255):
        """Generate n QBrushes via sequential colors.

        The colors will be repeated if n is larger than the number of
        pre-defined colors.

        :param int n: number of colors.
        """
        cls._validate_n(n)
        lst = cls.pool * (int(n/len(cls.pool)) + 1)
        for c in lst[:n]:
            yield QBrush(QColor(*c, alpha))


class ColorMap:
    """
    A ColorMap defines a relationship between a scalar value and a range of colors.
    ColorMaps are commonly used for false-coloring monochromatic images, coloring
    scatter-plot points, and coloring surface plots by height.

    Each color map is defined by a set of colors, each corresponding to a
    particular scalar value. For example:

        | 0.0  -> black
        | 0.2  -> red
        | 0.6  -> yellow
        | 1.0  -> white

    The colors for intermediate values are determined by interpolating between
    the two nearest colors in either RGB or HSV color space.

    To provide user-defined color mappings, see :class:`GradientWidget <pyqtgraph.GradientWidget>`.
    """

    gradients = {
        'thermal': (
            [0, 0.3333, 0.6666, 1],
            [
                (0, 0, 0, 255),
                (185, 0, 0, 255),
                (255, 220, 0, 255),
                (255, 255, 255, 255)
            ],
        ),
        'flame': (
            [0.0, 0.2, 0.5, 0.8, 1.0],
            [
                (0, 0, 0, 255),
                (7, 0, 220, 255),
                (236, 0, 134, 255),
                (246, 246, 0, 255),
                (255, 255, 255, 255)
            ]
        ),
        'grey': (
            [0.0, 1.0],
            [
                (0, 0, 0, 255),
                (255, 255, 255, 255)
            ]
        ),
        'viridis': (
            [0.0, 0.25, 0.5, 0.75, 1.0],
            [
                (68, 1, 84, 255),
                (58, 82, 139, 255),
                (32, 144, 140, 255),
                (94, 201, 97, 255),
                (253, 231, 36, 255)
            ]
        ),
        'inferno': (
            [0.0, 0.25, 0.5, 0.75, 1.0],
            [
                (0, 0, 3, 255),
                (87, 15, 109, 255),
                (187, 55, 84, 255),
                (249, 142, 8, 255),
                (252, 254, 164, 255)
            ]
        ),
        'plasma': (
            [0.0, 0.25, 0.5, 0.75, 1.0],
            [
                (12, 7, 134, 255),
                (126, 3, 167, 255),
                (203, 71, 119, 255),
                (248, 149, 64, 255),
                (239, 248, 33, 255)
            ]
        ),
        'magma': (
            [0.0, 0.25, 0.5, 0.75, 1.0],
            [
                (0, 0, 3, 255),
                (80, 18, 123, 255),
                (182, 54, 121, 255),
                (251, 136, 97, 255),
                (251, 252, 191, 255)
            ]
        ),
    }

    def __init__(self, positions: list, colors: list[tuple]):
        """Initialization.

        :param positions: Position for each color.
        :param colors: Color (RGBA) at each position.
        """
        self.positions = positions
        self.colors = [QColor(*c) for c in colors]

    @classmethod
    def fromName(cls, name: str):
        return ColorMap(*cls.gradients[name])


def set_button_color(btn, color: Union[QColor, str]):
    """Set color for a given button."""
    palette = btn.palette()
    if isinstance(color, QColor):
        palette.setColor(QPalette.ColorRole.Button, color)
    else:
        palette.setColor(QPalette.ColorRole.Button, QualitativeColor.mkColor(color))
    btn.setAutoFillBackground(True)
    btn.setPalette(palette)
