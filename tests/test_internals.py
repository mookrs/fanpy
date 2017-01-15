# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from fanpy.api import method_for_uri, build_uri
from fanpy.util import PY3, actually_bytes


def test_method_for_uri__lookup():
    assert 'POST' == method_for_uri('/blocks/create')
    assert 'POST' == method_for_uri('/statuses/update')
    assert 'POST' == method_for_uri('/account/update_profile_image')
    assert 'GET' == method_for_uri('/friendships/requests')


def test_build_uri():
    uri = build_uri(['1.1', 'foo', 'bar'], {})
    assert uri == '1.1/foo/bar'

    # Interpolation works
    uri = build_uri(['1.1', '_foo', 'bar'], {'_foo': 'asdf'})
    assert uri == '1.1/asdf/bar'

    # But only for strings beginning with _.
    uri = build_uri(['1.1', 'foo', 'bar'], {'foo': 'asdf'})
    assert uri == '1.1/foo/bar'


def test_actually_bytes():
    out_type = str
    if PY3:
        out_type = bytes
    for inp in [b'asdf', 'asdf', 'asdfüü', 1234]:
        assert type(actually_bytes(inp)) == out_type
