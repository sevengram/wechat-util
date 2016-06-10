# -*- coding: utf-8 -*-

from util import xmltodict


def transfer(src, copys=None, renames=None, allow_empty=True):
    if not src:
        return {}
    else:
        r1 = {key: src.get(key, '') for key in (copys or [])}
        r2 = {new_key: src.get(key, '') for key, new_key in (renames or [])}
        result = dict(r1, **r2)
        return {k: v for k, v in result.items() if allow_empty or not_empty(v)}


def special_decode(text):
    return text.replace('\x00', '<').replace('\x01', '>').replace('\x02', '&')


def special_encode(text):
    return text.replace('<', '\x00').replace('>', '\x01').replace('&', '\x02')


def dict2xml(dic):
    result = xmltodict.unparse({'xml': dic})
    return special_decode(result[result.index('\n') + 1:])


def xml2dict(xml):
    return xmltodict.parse(xml)['xml']


def not_empty(d):
    return d == 0 or bool(d)
