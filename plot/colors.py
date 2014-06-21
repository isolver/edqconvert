__author__ = 'Sol'

class ColorPalette(object):
    def __init__(self, colors):
        self._colors = colors

    @property
    def colors(self):
        return self._colors

    @property
    def name(self):
        return self.__class__.__name__

    def next(self):
        self._next += 1
        return self._colors[(self._next-1)%len(self._colors)]

    def __len__(self):
        return len(self._colors)

class ThoughtProvoking(ColorPalette):
    def __init__(self):
        colors = (
            (236, 208, 120),
            (217, 91, 67),
            (192, 41, 66),
            (84, 36, 55),
            (83, 119, 122),
            )
        ColorPalette.__init__(self, colors)

class OceanFive(ColorPalette):
    def __init__(self):
        colors = (
            (0,160,176),
            (106,74,60),
            (204,51,63),
            (235,104,65),
            (237,201,81),
            )
        ColorPalette.__init__(self, colors)

class VintageModern(ColorPalette):
    def __init__(self):
        colors = (
            (140,35,24),
            (94,140,106),
            (136,166,94),
            (191,179,90),
            (242,196,90),
            )
        ColorPalette.__init__(self, colors)

class RainingLove(ColorPalette):
    def __init__(self):
        colors = (
            (163,169,72),
            (237,185,46),
            (248,89,49),
            (206,24,54),
            (0,153,137),
            )
        ColorPalette.__init__(self, colors)

class Fashion4(ColorPalette):
    def __init__(self):
        colors = (
            (14,32,95),
            (10,30,101),
            (182,42,32),
            (58,99,10),
            (173,118,9),
            (181,92,32),
            (59,22,142),
            (100,100,100),
            (8,103,81)
            )
        ColorPalette.__init__(self, colors)

class ColorThemeTemplate(ColorPalette):
    def __init__(self):
        colors = (
            )
        ColorPalette.__init__(self, colors)

ColorPalettes=(ThoughtProvoking, OceanFive, VintageModern, RainingLove, Fashion4)