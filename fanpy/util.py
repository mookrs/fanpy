"""Internal utility functions."""

import sys
import time

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


class Fail(object):
    """A class to count fails during a repetitive task.

    Args:
        maximum: An integer for the maximum of fails to allow.
        exit: An integer for the exit code when maximum of fail is reached.

    Methods:
        count: Count a fail, exit when maximum of fails is reached.
        wait: Same as count but also sleep for a given time in seconds.
    """
    def __init__(self, maximum=10, exit=1):
        self.i = maximum
        self.exit = exit

    def count(self):
        self.i -= 1
        if self.i == 0:
            print('Too many consecutive fails, exit.')
            sys.exit(self.exit)

    def wait(self, delay=0):
        self.count()
        if delay > 0:
            time.sleep(delay)
