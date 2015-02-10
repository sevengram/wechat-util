# -*- coding: utf-8 -*-

import urllib

from util import xmltodict


def transfer(src, copys=None, renames=None, nonblank=False):
    if not src:
        return {}
    else:
        r1 = {key: src.get(key, '') for key in (copys or [])}
        r2 = {new_key: src.get(key, '') for key, new_key in (renames or [])}
        result = dict(r1, **r2)
        return {k: v for k, v in result.iteritems() if not_empty(v)} if nonblank else result


def filter_data(src, nonblank=False, delkeys=None):
    if type(src) is list:
        return [filter_data(d, nonblank, delkeys) for d in src]
    elif type(src) is dict:
        return {k: v for k, v in src.iteritems() if
                (not nonblank or not_empty(v)) and k not in (delkeys or [])} if src else {}
    else:
        return src


def special_decode(text):
    return text.replace('\x00', '<').replace('\x01', '>').replace('\x02', '&')


def special_encode(text):
    return text.replace('<', '\x00').replace('>', '\x01').replace('&', '\x02')


def urlencode(dic):
    return urllib.urlencode(dict_str(dic))


def dict2xml(dic):
    result = xmltodict.unparse({'xml': dict_unicode(dic)})
    return special_decode(result[result.index('\n') + 1:])


def xml2dict(xml):
    return xmltodict.parse(xml)['xml']


def dict_unicode(src, encoding='utf8'):
    return {k: v.decode(encoding) if type(v) is str else v for k, v in src.iteritems()}


def dict_str(src, encoding='utf8'):
    return {k: v.encode(encoding) if type(v) is unicode else v for k, v in src.iteritems()}


def not_empty(d):
    return d == 0 or bool(d)