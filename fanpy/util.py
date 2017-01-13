"""Internal utility functions."""
import contextlib
import re
import sys
import textwrap
import time
import socket

PY_3 = sys.version_info >= (3, 0)
