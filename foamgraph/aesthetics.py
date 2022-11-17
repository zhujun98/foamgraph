"""
Distributed under the terms of the BSD 3-Clause License.

The full license is in the file LICENSE, distributed with this software.

Author: Jun Zhu
"""
from .backend.QtCore import Qt, QSize
from .backend.QtGui import QBrush, QColor, QIcon, QPen
from .backend.QtWidgets import QPushButton

from .config import config


class QualitativeColor:

    foreground = config["FOREGROUND_COLOR"]  # black
    background = config["BACKGROUND_COLOR"]  # white-like

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
