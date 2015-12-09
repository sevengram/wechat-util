# -*- coding: utf-8 -*-

import json
import mimetypes
import urllib

import tornado.gen
import tornado.httpclient
import tornado.httputil
import tornado.curl_httpclient

from util import dtools

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'

type_methods = {
    'json': json.dumps,
    'xml': dtools.dict2xml,
    'form': dtools.urlencode,
    'raw': lambda a: a
}


def build_get_req(url, data, headers=None, proxy_host=None, proxy_port=None):
    return tornado.httpclient.HTTPRequest(
        url=url + '?' + dtools.urlencode(data) if data else url,
        method='GET',
        headers=tornado.httputil.HTTPHeaders(headers or {}),
        validate_cert=False,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        connect_timeout=120,
        request_timeout=120
    )


def build_post_req(url, method, body, headers=None, proxy_host=None, proxy_port=None):
    return tornado.httpclient.HTTPRequest(
        url=url,
        method=method,
        body=body,
        headers=tornado.httputil.HTTPHeaders(headers or {}),
        validate_cert=False,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        connect_timeout=120,
        request_timeout=120
    )


def _send_dict_sync(url, method, data, data_type, headers=None, proxy_host=None, proxy_port=None):
    _headers = headers or {}
    if data_type == 'form':
        _headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    body = type_methods.get(data_type)(data)
    client = tornado.httpclient.HTTPClient()
    return client.fetch(build_post_req(url, method, body, _headers, proxy_host, proxy_port))


@tornado.gen.coroutine
def _send_dict(url, method, data, data_type, headers=None, proxy_host=None, proxy_port=None):
    _headers = headers or {}
    if data_type == 'form':
        _headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    body = type_methods.get(data_type)(data)
    if not proxy_host:
        client = tornado.httpclient.AsyncHTTPClient()
    else:
        client = tornado.curl_httpclient.CurlAsyncHTTPClient()
    resp = yield client.fetch(build_post_req(url, method, body, _headers, proxy_host, proxy_port))
    raise tornado.gen.Return(resp)


def post_dict_sync(url, data, data_type='form', headers=None, proxy_host=None, proxy_port=None):
    return _send_dict_sync(url, 'POST', data, data_type, headers, proxy_host, proxy_port)


@tornado.gen.coroutine
def post_dict(url, data, data_type='form', headers=None, proxy_host=None, proxy_port=None):
    resp = yield _send_dict(url, 'POST', data, data_type, headers, proxy_host, proxy_port)
    raise tornado.gen.Return(resp)


def put_dict_sync(url, data, data_type='form', headers=None, proxy_host=None, proxy_port=None):
    return _send_dict_sync(url, 'PUT', data, data_type, headers, proxy_host, proxy_port)


@tornado.gen.coroutine
def put_dict(url, data, data_type='form', headers=None, proxy_host=None, proxy_port=None):
    resp = yield _send_dict(url, 'PUT', data, data_type, headers, proxy_host, proxy_port)
    raise tornado.gen.Return(resp)


def get_dict_sync(url, data=None, headers=None, proxy_host=None, proxy_port=None):
    client = tornado.httpclient.HTTPClient()
    return client.fetch(build_get_req(url, data, headers, proxy_host, proxy_port))


@tornado.gen.coroutine
def get_dict(url, data=None, headers=None, proxy_host=None, proxy_port=None):
    if not proxy_host:
        client = tornado.httpclient.AsyncHTTPClient()
    else:
        client = tornado.curl_httpclient.CurlAsyncHTTPClient()
    resp = yield client.fetch(build_get_req(url, data, headers, proxy_host, proxy_port))
    raise tornado.gen.Return(resp)


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def build_url(base_url, params):
    return base_url + '?' + urllib.urlencode(params)


def encode_multipart_formdata(fields, files):
    boundary = '----------ThIs_Is_tHe_bouNdaRY_$'
    crlf = '\r\n'
    l = []
    for (key, value) in fields:
        l.append('--' + boundary)
        l.append('Content-Disposition: form-data; name="%s"' % key)
        l.append('')
        l.append(value)
    for (key, filename, value) in files:
        l.append('--' + boundary)
        l.append('Content-Disposition: form-data; name="%s"; filename="%s"' %
                 (key, filename.split('/')[-1]))
        l.append('Content-Type: %s' % get_content_type(filename))
        l.append('')
        l.append(value)
    l.append('--' + boundary + '--')
    l.append('')
    body = crlf.join(l)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body
