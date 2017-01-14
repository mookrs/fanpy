"""Internal utility functions."""

import sys


PY3 = sys.version_info >= (3, 0)


def actually_bytes(stringy):
    if PY3:
        if type(stringy) == bytes:
            pass
        elif type(stringy) != str:
            stringy = str(stringy)
        if type(stringy) == str:
            stringy = stringy.encode('utf-8')
    else:
        if type(stringy) == str:
            pass
        elif type(stringy) != unicode:
            stringy = str(stringy)
        if type(stringy) == unicode:
            stringy = stringy.encode('utf-8')
    return stringy
