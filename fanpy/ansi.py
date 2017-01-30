"""Support for ANSI colors in command-line client."""

import itertools
import sys

ESC = chr(0x1B)
RESET = '0'

COLORS_NAMED = dict(list(zip(
    ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'],
    [str(x) for x in range(30, 38)]
)))
COLORS_MIDS = [
    color for name, color in COLORS_NAMED.items()
    if name not in ('black', 'white')
]


class AnsiColorException(Exception):
    pass


class ColorMap(object):
    """Object that allows for mapping strings to ansi color values"""
    def __init__(self, colors=COLORS_MIDS):
        """uses the list of ansi `colors` values to initialize the map"""
        self.color_map = {}
        self.color_iter = itertools.cycle(colors)

    def color_for(self, string):
        """Returns an ansi color value given a `string`.
        The same ansi color value is always returned for the same string
        """
        if string not in self.color_map:
            self.color_map[string] = next(self.color_iter)
        return self.color_map[string]


class AnsiCmd(object):
    def __init__(self, force_ansi):
        self.force_ansi = force_ansi

    def cmd_reset(self):
        """Returns the ansi cmd color for a RESET"""
        if sys.stdout.isatty() or self.force_ansi:
            return ESC + '[0m'
        else:
            return ''

    def cmd_color(self, color):
        """Return the ansi cmd color (i.e. escape sequence)
        for the ansi `color` value
        """
        if sys.stdout.isatty() or self.force_ansi:
            return ESC + '[' + color + 'm'
        else:
            return ''

    def cmd_color_named(self, color):
        """Return the ansi cmd_color for a given named `color`"""
        try:
            return self.cmd_color(COLORS_NAMED[color])
        except KeyError:
            raise AnsiColorException('Unknown Color {}'.format(color))

    def cmd_bold(self):
        if sys.stdout.isatty() or self.force_ansi:
            return ESC + '[1m'
        else:
            return ''

    def cmd_underline(self):
        if sys.stdout.isatty() or self.force_ansi:
            return ESC + '[4m'
        else:
            return ''
