"""
    fanpy
    ~~~~~
    fanpy is a Python tool that allows you to interact with
    fanfou.com. It is a clone from `Python Twitter Tools`.

    :license: MIT.
"""

from .api import Fanfou, FanfouError, FanfouHTTPError, FanfouResponse
from .auth import NoAuth
from .oauth import OAuth, read_token_file, write_token_file
from .oauth_dance import oauth_dance

__all__ = [
    'NoAuth',
    'OAuth',
    'oauth_dance',
    'read_token_file',
    'Fanfou',
    'FanfouError',
    'FanfouHTTPError',
    'FanfouResponse',
    'write_token_file',
]

__version__ = '0.2.0'
__license__ = 'MIT'
