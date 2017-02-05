# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import pickle
import json

from fanpy import Fanfou, FanfouHTTPError, NoAuth
from fanpy.api import FanfouDictResponse, FanfouListResponse, POST_ACTIONS, method_for_uri

noauth = NoAuth()
fanfou_na = Fanfou(auth=noauth)

AZaz = 'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def get_random_str():
    return ''.join(random.choice(AZaz) for _ in range(10))


def test_FanfouHTTPError_raised_for_invalid_oauth():
    test_passed = False
    try:
        fanfou_na.statuses.mentions()
    except FanfouHTTPError:
        test_passed = True
    assert test_passed


def test_pickle_ability():
    res = FanfouDictResponse({'a': 'b'})
    p = pickle.dumps(res)
    res2 = pickle.loads(p)
    assert res == res2
    assert res2['a'] == 'b'

    res = FanfouListResponse([1, 2, 3])
    p = pickle.dumps(res)
    res2 = pickle.loads(p)
    assert res == res2
    assert res2[2] == 3


def test_json_ability():
    res = FanfouDictResponse({'a': 'b'})
    p = json.dumps(res)
    res2 = json.loads(p)
    assert res == res2
    assert res2['a'] == 'b'

    res = FanfouListResponse([1, 2, 3])
    p = json.dumps(res)
    res2 = json.loads(p)
    assert res == res2
    assert res2[2] == 3


def test_method_for_uri():
    for action in POST_ACTIONS:
        assert method_for_uri(get_random_str() + '/' + action) == 'POST'
    assert method_for_uri('statuses/home_timeline') == 'GET'
