"""
Visit the Fanfou open platform and create a new application:

    http://fanfou.com/apps.new

This will get you a CONSUMER_KEY and CONSUMER_SECRET.

When users run your application they have to authenticate your app
with their Fanfou account. A few HTTP calls to Fanfou are required
to do this. Please see the fanpy.oauth_dance module to see how this
is done. If you are making a command-line app, you can use the
oauth_dance() function directly.

Performing the "oauth dance" gets you an ouath token and oauth token secret
that authenticate the user with Fanfou. You should save these for
later so that the user doesn't have to do the oauth dance again.

read_token_file() and write_token_file() are utility methods to read and
write OAuth token and secret key values. The values are stored as
strings in the file.

Finally, you can use the OAuth authenticator to connect to Fanfou. In
code it all goes like this:

    from fanpy import *

    MY_FANFOU_CREDS = os.path.expanduser('~/.my_app_credentials')
    if not os.path.exists(MY_FANFOU_CREDS):
        oauth_dance('My App Name', CONSUMER_KEY, CONSUMER_SECRET,
                    MY_FANFOU_CREDS)

    oauth_token, oauth_token_secret = read_token_file(MY_FANFOU_CREDS)

    fanfou = Fanfou(auth=OAuth(
        oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

    # Now work with Fanfou
    fanfou.statuses.update(status='Hello, world!')

"""

from __future__ import print_function

import base64
import hashlib
import hmac

from random import getrandbits
from time import time

from .auth import Auth, MissingCredentialsError
from .util import PY3

try:
    from urllib.parse import quote, urlencode
except ImportError:
    from urllib2 import quote
    from urllib import urlencode


def write_token_file(filename, oauth_token, oauth_token_secret):
    """Write a token file to hold the oauth token and oauth token secret."""
    with open(filename, 'w') as oauth_file:
        print(oauth_token, file=oauth_file)
        print(oauth_token_secret, file=oauth_file)


def read_token_file(filename):
    """Read a token file and return the oauth token and oauth token secret."""
    with open(filename) as oauth_file:
        return oauth_file.readline().strip(), oauth_file.readline().strip()


class OAuth(Auth):
    """An OAuth 1.0a authenticator."""

    def __init__(self, token, token_secret, consumer_key, consumer_secret):
        """
        Create the authenticator. If you are in the initial stages of
        the OAuth dance and don't yet have a token or token_secret,
        pass empty strings for these params.
        """
        self.token = token
        self.token_secret = token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        if token_secret is None or consumer_secret is None:
            raise MissingCredentialsError(
                'You must supply strings for token_secret and consumer_secret, not None.')

    def encode_params(self, base_url, method, params):
        """

        :param base_url: eg: http://api.fanfou.com/statuses/update.json
        :param method: GET or POST or others
        :param params: eg: {'status': 'test'}
        """
        params = params.copy()

        if self.token:
            params['oauth_token'] = self.token

        params['oauth_consumer_key'] = self.consumer_key
        params['oauth_signature_method'] = 'HMAC-SHA1'
        params['oauth_version'] = '1.0'
        params['oauth_timestamp'] = str(int(time()))
        params['oauth_nonce'] = str(getrandbits(64))

        enc_params = urlencode_noplus(sorted(params.items()))
        message = '&'.join(
            oauth_escape(i) for i in [method.upper(), base_url, enc_params])

        key = self.consumer_secret + '&' + oauth_escape(self.token_secret)

        hash_obj = hmac.new(key.encode(), message.encode(), hashlib.sha1)
        signature = base64.b64encode(hash_obj.digest())

        return enc_params + '&' + 'oauth_signature=' + oauth_escape(signature)

    def generate_headers(self):
        return {}


# Apparently contrary to the HTTP RFCs, spaces in arguments must be encoded as
# '%20' rather than '+' when constructing an OAuth signature.
# So here is a specialized version which does exactly that.
# In Python 2, since there is no safe option for urlencode, we force it by hand.
def urlencode_noplus(query):
    if not PY3:
        new_query = []
        TILDE = '____TILDE____'
        for k, v in query:
            if type(k) is unicode:
                k = k.encode('utf-8')
            k = str(k).replace('~', TILDE)
            if type(v) is unicode:
                v = v.encode('utf-8')
            v = str(v).replace('~', TILDE)
            new_query.append((k, v))
        return urlencode(new_query).replace(TILDE, '~').replace('+', '%20')

    return urlencode(query, safe='~').replace('+', '%20')


def oauth_escape(val):
    return quote(val, safe='~')
