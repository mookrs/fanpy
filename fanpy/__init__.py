"""
    fanpy
    ~~~~~
    fanpy is a Python tool that allows you to interact with
    fanfou.com. It is a complete clone from `Python Twitter Tools`.

    :license: MIT.
"""

from .api import Fanfou, FanfouError, FanfouHTTPError, FanfouResponse
from .auth import NoAuth
from .oauth import OAuth

__all__ = [
    'NoAuth',
    'OAuth',
    'Fanfou',
    'FanfouError',
    'FanfouHTTPError',
    'FanfouResponse',
]

__version__ = '0.1.0'
__license__ = 'MIT'
