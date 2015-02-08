# -*- coding: utf-8 -*-

import json

import tornado.gen
import tornado.httpclient
import tornado.httputil

from util import dtools


type_methods = {
    'json': json.dumps,
    'xml': dtools.dict2xml,
    'form': dtools.urlencode,
    'raw': lambda a: a
}


@tornado.gen.coroutine
def _send_dict(url, method, data, data_type, headers):
    _headers = headers or {}
    if data_type == 'form':
        _headers['Content-Type'] = 'application/x-www-form-urlencoded'
    client = tornado.httpclient.AsyncHTTPClient()
    req = tornado.httpclient.HTTPRequest(
        url=url,
        method=method,
        body=type_methods.get(data_type)(data),
        headers=tornado.httputil.HTTPHeaders(_headers)
    )
    resp = yield client.fetch(req)
    raise tornado.gen.Return(resp)


@tornado.gen.coroutine
def post_dict(url, data, data_type='form', headers=None):
    resp = yield _send_dict(url, 'POST', data, data_type, headers)
    raise tornado.gen.Return(resp)


@tornado.gen.coroutine
def put_dict(url, data, data_type='form', headers=None):
    resp = yield _send_dict(url, 'PUT', data, data_type, headers)
    raise tornado.gen.Return(resp)


@tornado.gen.coroutine
def get_dict(url, data):
    client = tornado.httpclient.AsyncHTTPClient()
    req = tornado.httpclient.HTTPRequest(
        url=url + '?' + dtools.urlencode(data),
        method='GET'
    )
    resp = yield client.fetch(req)
    raise tornado.gen.Return(resp)
