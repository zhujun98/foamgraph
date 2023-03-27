"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from collections import OrderedDict
from typing import Optional, Union

import numpy as np

from .backend.QtCore import Qt, QRectF, QSize
from .backend.QtGui import (
    QBrush, QColor, QIcon, QPainterPath, QPen, QTransform
)
from .backend.QtWidgets import QPushButton

from .config import config


class QualitativeColor:

    foreground = config["FOREGROUND_COLOR"][:3]  # black
    background = config["BACKGROUND_COLOR"][:3]  # white-like

    # Base colors from matplotlib
    # ---------------------------
    r = (255, 0, 0)  # red
    g = (0, 128, 0)  # green
    b = (0, 0, 255)  # blue
    c = (0, 192, 192)  # cyan
    m = (192, 0, 192)  # magenta
    y = (192, 192, 0)  # yellow
    k = (0, 0, 0)  # black
    w = (255, 255, 255)  # white

    # CSS colors
    # ----------

    FireBrick = (178, 34, 34)
    Red = (255, 0, 0)

    Pink = (255, 192, 203)

    DarkOrange = (255, 140, 0)
    Orange = (255, 165, 0)

    Yellow = (255, 255, 0)
    Gold = (255, 215, 0)
    Khaki = (240, 230, 140)

    Violet = (238, 130, 238)
    Orchid = (218, 112, 214)
    Magenta = (255, 0, 255)
    Purple = (128, 0, 128)

    ForestGreen = (34, 139, 34)
    Green = (0, 128, 0)
    DarkGreen = (0, 100, 0)

    Cyan = (0, 255, 255)
    DodgerBlue = (30, 144, 255)
    Blue = (0, 0, 255)

    Chocolate = (210, 105, 30)
    Brown = (165, 42, 42)

    White = (255, 255, 255)

    Silver = (192, 192, 192)
    Gray = (128, 128, 128)
    Black = (0, 0, 0)

    @classmethod
    def mkColor(cls, c, *, alpha=255):
        return QColor(*getattr(cls, c), alpha)

    @classmethod
    def mkPen(cls, c: Optional[Union[str, QColor]] = None, *,
              alpha=255, width=1, style=Qt.PenStyle.SolidLine):
        if c is None:
            return QPen(QColor(0, 0, 0, 0), width, Qt.PenStyle.NoPen)
        if not isinstance(c, QColor):
            c = QColor(*getattr(cls, c), alpha)
        pen = QPen(c, width, style)
        pen.setCosmetic(True)
        return pen

    @classmethod
    def mkBrush(cls, c: Optional[Union[str, QColor]] = None, *, alpha=255):
        if c is None:
            return QBrush(QColor(0, 0, 0, 0), Qt.BrushStyle.NoBrush)
        if not isinstance(c, QColor):
            c = QColor(*getattr(cls, c), alpha)
        return QBrush(c)


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

    def _colorAt(self, x: float):
        positions = self.positions
        colors = self.colors
        if x <= positions[0]:
            c = colors[0]
            return c.red(), c.green(), c.blue(), c.alpha()
        if x >= positions[-1]:
            c = colors[-1]
            return c.red(), c.green(), c.blue(), c.alpha()

        x2 = positions[0]
        for i in range(1, len(positions)):
            x1 = x2
            x2 = positions[i]
            if x1 <= x <= x2:
                break

        dx = x2 - x1
        if dx == 0:
            f = 0.
        else:
            f = (x - x1) / dx

        c1 = colors[i-1]
        c2 = colors[i]

        r = c1.red() * (1.-f) + c2.red() * f
        g = c1.green() * (1.-f) + c2.green() * f
        b = c1.blue() * (1.-f) + c2.blue() * f
        a = c1.alpha() * (1.-f) + c2.alpha() * f

        return r, g, b, a

    def getLookUpTable(self, n: int, *, with_alpha: bool = True) -> np.ndarray:
        table = np.empty((n, 4), dtype=np.ubyte)
        for i in range(n):
            table[i] = self._colorAt(i / (n - 1))
        if with_alpha:
            return table
        return table[:, :3]


def createIconButton(filepath: str, size: int, *, description: str = ""):
    """Create a QPushButton with icon.

    :param filepath: path of the icon file.
    :param size: size of the icon (button).
    :param description: tool tip of the button.
    """
    btn = QPushButton()
    icon = QIcon(filepath)
    btn.setIcon(icon)
    btn.setIconSize(QSize(size, size))
    btn.setFixedSize(btn.minimumSizeHint())
    if description:
        btn.setToolTip(description)
    return btn


class FSymbol:

    @classmethod
    def buildSymbols(cls):
        symbols = OrderedDict([
            (name, QPainterPath()) for name in
            ['o', 's', 't', 't1', 't2', 't3', 'd', '+', 'x', 'p', 'h', 'star',
             'arrow_up', 'arrow_right', 'arrow_down', 'arrow_left']])

        symbols['o'].addEllipse(QRectF(-0.5, -0.5, 1., 1.))
        symbols['s'].addRect(QRectF(-0.5, -0.5, 1., 1.))

        coordinates = {
            't': [(-0.5, -0.5), (0, 0.5), (0.5, -0.5)],
            't1': [(-0.5, 0.5), (0, -0.5), (0.5, 0.5)],
            't2': [(-0.5, -0.5), (-0.5, 0.5), (0.5, 0)],
            't3': [(0.5, 0.5), (0.5, -0.5), (-0.5, 0)],
            'd': [(0., -0.5), (-0.4, 0.), (0, 0.5), (0.4, 0)],
            '+': [(-0.5, -0.05), (-0.5, 0.05), (-0.05, 0.05), (-0.05, 0.5),
                  (0.05, 0.5), (0.05, 0.05), (0.5, 0.05), (0.5, -0.05),
                  (0.05, -0.05), (0.05, -0.5), (-0.05, -0.5), (-0.05, -0.05)],
            'p': [(0, -0.5), (-0.4755, -0.1545), (-0.2939, 0.4045),
                  (0.2939, 0.4045), (0.4755, -0.1545)],
            'h': [(0.433, 0.25), (0., 0.5), (-0.433, 0.25), (-0.433, -0.25),
                  (0, -0.5), (0.433, -0.25)],
            'star': [(0, -0.5), (-0.1123, -0.1545), (-0.4755, -0.1545),
                     (-0.1816, 0.059), (-0.2939, 0.4045), (0, 0.1910),
                     (0.2939, 0.4045), (0.1816, 0.059), (0.4755, -0.1545),
                     (0.1123, -0.1545)],
            'arrow_down': [
                (-0.125, 0.125), (0, 0), (0.125, 0.125),
                (0.05, 0.125), (0.05, 0.5), (-0.05, 0.5), (-0.05, 0.125)
            ]
        }

        for k, c in coordinates.items():
            symbols[k].moveTo(*c[0])
            for x, y in c[1:]:
                symbols[k].lineTo(x, y)
            symbols[k].closeSubpath()

        tr = QTransform()
        tr.rotate(45)
        symbols['x'] = tr.map(symbols['+'])
        tr.rotate(45)
        symbols['arrow_right'] = tr.map(symbols['arrow_down'])
        symbols['arrow_up'] = tr.map(symbols['arrow_right'])
        symbols['arrow_left'] = tr.map(symbols['arrow_up'])
        cls._symbol_map = symbols

    _symbol_map = None

    @classmethod
    def mkSymbol(cls, name: str):
        if cls._symbol_map is None:
            cls.buildSymbols()
        return cls._symbol_map[name]
