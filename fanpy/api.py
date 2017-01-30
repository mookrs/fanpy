# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

try:
    import json
except ImportError:
    import simplejson as json

try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error

import gzip
import re
import sys
from time import sleep, time

from .auth import NoAuth
from .fanfou_globals import POST_ACTIONS
from .util import PY3, actually_bytes


class _DEFAULT(object):
    pass


class FanfouError(Exception):
    """Base Exception thrown by the Fanfou object when there is a
    general error interacting with the API.
    """
    pass


class FanfouHTTPError(FanfouError):
    """Exception thrown by the Fanfou object when there is an
    HTTP error interacting with fanfou.com.
    """

    def __init__(self, e, uri, format, uriparts):
        self.e = e
        self.uri = uri
        self.format = format
        self.uriparts = uriparts
        try:
            data = self.e.fp.read()
        except http_client.IncompleteRead as e:
            data = e.partial
        if self.e.headers.get('Content-Encoding') == 'gzip':
            buf = BytesIO(data)
            f = gzip.GzipFile(fileobj=buf)
            data = f.read()
        if len(data) == 0:
            data = {}
        else:
            data = data.decode('utf-8')
            if self.format == 'json':
                try:
                    data = json.loads(data)
                except ValueError:
                    pass
        self.response_data = data
        super(FanfouHTTPError, self).__init__(str(self))

    def __str__(self):
        fmt = ('.' + self.format) if self.format else ''
        return ('Fanfou HTTP Error {} for URL: {}{}, using parameters: ({})\ndetails: {}'
            .format(self.e.code, self.uri, fmt, self.uriparts, self.response_data))


class FanfouResponse(object):
    """Response from a Fanfou request. Behaves like a list or a string
    (depending on requested format).
    """

    @property
    def x_auth_user(self):
        """The X-AuthUser for that request."""
        return self.headers.get('X-AuthUser', '')


class FanfouDictResponse(dict, FanfouResponse):
    pass


class FanfouListResponse(list, FanfouResponse):
    pass


def wrap_response(response, headers):
    response_type = type(response)
    if response_type is dict:
        res = FanfouDictResponse(response)
        res.headers = headers
    elif response_type is list:
        res = FanfouListResponse(response)
        res.headers = headers
    else:
        res = response
    return res


POST_ACTIONS_RE = re.compile('(' + '|'.join(POST_ACTIONS) + r')(/\d+)?$')


def method_for_uri(uri):
    """Choose METHOD for uri according to `fanfou_globals.py`."""
    if POST_ACTIONS_RE.search(uri):
        return 'POST'
    return 'GET'


def build_uri(orig_uriparts, kwargs):
    """Build the URI from the original uriparts and kwargs. Modifies kwargs.

    :param orig_uriparts: eg: ('statuses', 'user_timeline')
    :param kwargs: eg: {'_id': 'ifanfou'}
    """
    uriparts = []
    for uripart in orig_uriparts:
        # If this part matches a keyword argument (starting with _), use
        # the supplied value. Otherwise, just use the part.
        if uripart.startswith('_'):
            part = str(kwargs.pop(uripart, uripart))
        else:
            part = uripart
        uriparts.append(part)
    uri = '/'.join(uriparts)

    # If an id kwarg is present and there is no id to fill in in
    # the list of uriparts, assume the id goes at the end.
    id = kwargs.pop('id', None)
    if id:
        uri += '/{}'.format(id)

    # eg: `fanfou.statuses.update(status='Hello, world!')` to
    # `statuses/update`
    # eg: `fanfou.statuses.user_timeline._id(_id='ifanfou')` or
    # `fanfou.statuses.user_timeline(id='ifanfou')` to
    # `statuses/user_timeline/ifanfou`
    return uri


class FanfouCall(object):
    # Delay after HTTP codes 502, 503 or 504.
    FANFOU_UNAVAILABLE_WAIT = 30

    def __init__(
            self, auth, format, domain, callable_cls, uri='',
            uriparts=None, secure=False, timeout=None, gzip=False):
        self.auth = auth
        self.format = format
        self.domain = domain
        self.callable_cls = callable_cls
        self.uri = uri
        self.uriparts = uriparts
        self.secure = secure
        self.timeout = timeout
        self.gzip = gzip

    # object.__getattr__(self, name)
    # Called when an attribute lookup has not found the attribute in the
    # usual places (eg: it is not an instance attribute nor is it found in
    # the class tree for `self`). `name` is the attribute name.
    # This method should return the (computed) attribute value or
    # raise an `AttributeError` exception.
    # See: https://docs.python.org/3/reference/datamodel.html#object.__getattr__
    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            # eg: `fanfou.statuses.update` will raise this exception,
            # attribute then add to `uriparts`.
            def extend_call(arg):
                return self.callable_cls(
                    auth=self.auth, format=self.format, domain=self.domain,
                    callable_cls=self.callable_cls, secure=self.secure,
                    timeout=self.timeout, gzip=self.gzip,
                    uriparts=self.uriparts + (arg,))
            if k == '_':
                return extend_call
            else:
                return extend_call(k)

    # object.__call__(self[, args...])
    # Called when the instance is "called" as a function; if this method is defined,
    # `x(arg1, arg2, ...)` is a shorthand for `x.__call__(arg1, arg2, ...)`.
    # See: https://docs.python.org/3/reference/datamodel.html#object.__call__
    def __call__(self, **kwargs):
        kwargs = dict(kwargs)
        uri = build_uri(self.uriparts, kwargs)
        method = kwargs.pop('_method', None) or method_for_uri(uri)
        domain = self.domain

        # If an _id kwarg is present, this is treated as id as a CGI
        # param.
        _id = kwargs.pop('_id', None)
        if _id:
            kwargs['id'] = _id

        # If an _timeout is specified in kwargs, use it.
        _timeout = kwargs.pop('_timeout', None)

        secure_str = 's' if self.secure else ''
        dot = '.' if self.format else ''

        # eg: http://api.fanfou.com/1.1/statuses/update.json
        url_base = 'http{}://{}/{}{}{}'.format(
            secure_str, domain, uri, dot, self.format)

        photo = kwargs.pop('photo', None)

        headers = {'Accept-Encoding': 'gzip'} if self.gzip else dict()
        body = None
        arg_data = None

        if self.auth:
            headers.update(self.auth.generate_headers())
            # Because the method uses multipart POST, OAuth is handled a
            # little differently. POST or query string parameters are not
            # used when calculating an OAuth signature basestring or signature.
            arg_data = self.auth.encode_params(
                url_base, method, {} if photo else kwargs)
            if method == 'GET' or photo:
                url_base += '?' + arg_data
            else:
                body = arg_data.encode('utf-8')

        # See: http://www.ietf.org/rfc/rfc1867.txt
        if photo:
            BOUNDARY = b'###Python-Fanfou###'
            bod = []
            bod.append(b'--' + BOUNDARY)
            # Never omit `filename`, otherwise will meet
            # 'lack of photo parameter' or else errors.
            bod.append(
                b'Content-Disposition: form-data; name="photo"; '
                + b'filename="filename"')
            bod.append(b'Content-Type: application/octet-stream')
            bod.append(b'')
            bod.append(actually_bytes(photo))
            for k, v in kwargs.items():
                k = actually_bytes(k)
                v = actually_bytes(v)
                bod.append(b'--' + BOUNDARY)
                bod.append(
                    b'Content-Disposition: form-data; name="' + k + b'"')
                bod.append(b'Content-Type: text/plain;charset=utf-8')
                bod.append(b'')
                bod.append(v)
            bod.append(b'--' + BOUNDARY + b'--')
            bod.append(b'')
            bod.append(b'')
            body = b'\r\n'.join(bod)
            headers['Content-Type'] = \
                b'multipart/form-data; boundary=' + BOUNDARY

            if not PY3:
                url_base = url_base.encode('utf-8')
                for k in headers:
                    headers[actually_bytes(k)] = actually_bytes(headers.pop(k))

        # `url_base` eg: http://api.fanfou.com/statuses/user_timeline.json?
        # id=ifanfou&oauth_consumer_key=<consumer_key>&oauth_nonce=<oauth_nonce>
        # &oauth_signature_method=HMAC-SHA1&oauth_timestamp=<oauth_timestamp>
        # &oauth_token=<oauth_token>&oauth_version=1.0&oauth_signature=<oauth_signature>
        # or `http://api.fanfou.com/statuses/update.json`
        req = urllib_request.Request(url_base, data=body, headers=headers)
        return self._handle_response(req, uri, arg_data, _timeout)

    def _handle_response(self, req, uri, arg_data, _timeout=None):
        kwargs = {}
        if _timeout:
            kwargs['timeout'] = _timeout
        try:
            handle = urllib_request.urlopen(req, **kwargs)
            if handle.headers['Content-Type'] in ['image/jpeg', 'image/png', 'image/gif']:
                print(handle.headers['Content-Type'])
                return handle
            try:
                data = handle.read()
            except http_client.IncompleteRead as e:
                # Even if we don't get all the bytes we should have there
                # may be a complete response in e.partial
                data = e.partial
            if handle.info().get('Content-Encoding') == 'gzip':
                # Handle gzip decompression.
                buf = BytesIO(data)
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
            if len(data) == 0:
                return wrap_response({}, handle.headers)
            elif 'json' == self.format:
                res = json.loads(data.decode('utf-8'))
                return wrap_response(res, handle.headers)
            else:
                return wrap_response(
                    data.decode('utf-8'), handle.headers)
        except urllib_error.HTTPError as e:
            if (e.code == 304):
                return []
            else:
                raise FanfouHTTPError(e, uri, self.format, arg_data)


class Fanfou(FanfouCall):
    """Examples::

        from fanpy import *

        f = Fanfou(auth=OAuth(oauth_token, oauth_token_secret, consumer_key, consumer_secret))

        # Get your home timeline
        f.statuses.home_timeline()

        # Get a particular friend's timeline
        f.statuses.user_timeline(_id='ifanfou')

        # To pass in GET/POST parameters, such as `count`
        f.statuses.home_timeline(count=5)

        # Update your status
        f.statuses.update(status='Hello, world!')

        # Send a direct message
        f.direct_messages.new(user='ifanfou', text='I miss you!')

        # An *optional* `_timeout` parameter can also be used for API
        # calls which take much more time than normal:
        f.search.public_timeline(q='|'.join(A_LIST_OF_100_WORDS), _timeout=1)

        # Overriding Method: GET/POST
        # you should not need to use this method as this library properly
        # detects whether GET or POST should be used, Nevertheless
        # to force a particular method, use `_method`
        t.statuses.update(status='Hello, world!', _method='POST')


        # Send image with your status:
        # - Just read image from the web or from file the regular way:
        with open('example.png', 'rb') as imagefile:
            imagedata = imagefile.read()
        # - Then send the image with a status.
        fanfou.photos.upload(photo=imagedata, status='Upload image.')


    Using the data returned
    -----------------------

    Fanfou API calls return decoded JSON. This is converted into
    a bunch of Python lists, dicts, ints, and strings. For example::

        x = fanfou.statuses.home_timeline()

        # The first status in the timeline
        x[0]

        # The name of the user who wrote the first status
        x[0]['user']['name']


    Getting raw XML data
    --------------------

    If you prefer to get your Fanfou data in XML format, pass
    format='xml' to the Fanfou object when you instantiate it::

        fanfou = Fanfou(format='xml')

    The output will not be parsed in any way. It will be a raw string
    of XML.
    """

    def __init__(
            self, auth=None, format='json',
            domain='api.fanfou.com', secure=False,
            api_version=None):
        """
        Create a new fanfou API connector.

        Pass an `auth` parameter to use the credentials of a specific
        user. Generally you'll want to pass an `OAuth`
        instance::

            fanfou = Fanfou(auth=OAuth(
                    token, token_secret, consumer_key, consumer_secret))


        `domain` lets you change the domain you are connecting. By
        default it's `api.fanfou.com`.

        If `secure` is False you will connect with HTTP instead of
        HTTPS. (Fanfou doesn't support HTTPS until now.)

        `api_version` is used to set the base uri. By default it's
        None.
        """
        if not auth:
            auth = NoAuth()

        if (format not in ('json', 'xml', '')):
            raise ValueError('Unknown data format "{}"'.format(format))

        if api_version is _DEFAULT:
            api_version = '1.1'

        uriparts = ()
        if api_version:
            uriparts += (str(api_version),)

        FanfouCall.__init__(
            self, auth=auth, format=format, domain=domain,
            callable_cls=FanfouCall,
            secure=secure, uriparts=uriparts)


# If a package's `__init__.py` code defines a list named `__all__`,
# it is taken to be the list of module names that should be imported
# when `from package import *` is encountered.
# See: https://docs.python.org/3/tutorial/modules.html#importing-from-a-package
__all__ = ['Fanfou', 'FanfouError', 'FanfouHTTPError', 'FanfouResponse']
