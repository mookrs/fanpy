"""Internal utility functions."""

import sys
import textwrap

PY3 = sys.version_info >= (3, 0)


def actually_bytes(string):
    if PY3:
        if type(string) == bytes:
            pass
        elif type(string) != str:
            string = str(string)
        if type(string) == str:
            string = string.encode('utf-8')
    else:
        if type(string) == str:
            pass
        elif type(string) != unicode:
            string = str(string)
        if type(string) == unicode:
            string = string.encode('utf-8')
    return string


def print_nicely(s):
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(s.encode('utf-8'))
        print()
        sys.stdout.buffer.flush()
        sys.stdout.flush()
    else:
        print(s.encode('utf-8'))


def align_text(text, left_margin=17, max_width=160):
    lines = []
    for line in text.split('\n'):
        temp_lines = textwrap.wrap(line, max_width - left_margin)
        temp_lines = [(' ' * left_margin + line) for line in temp_lines]
        lines.append('\n'.join(temp_lines))
    ret = '\n'.join(lines)
    return ret.lstrip()
