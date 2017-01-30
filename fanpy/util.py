"""Internal utility functions."""

import sys

PY3 = sys.version_info >= (3, 0)


def actually_bytes(s):
    if PY3:
        if type(s) == bytes:
            pass
        elif type(s) != str:
            s = str(s)
        if type(s) == str:
            s = s.encode('utf-8')
    else:
        if type(s) == str:
            pass
        elif type(s) != unicode:
            s = str(s)
        if type(s) == unicode:
            s = s.encode('utf-8')
    return s


def print_nicely(s):
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(s.encode('utf-8'))
        print()
        sys.stdout.buffer.flush()
        sys.stdout.flush()
    else:
        print(s.encode('utf-8'))
