# -*- coding: utf-8 -*-

import base64
import hashlib
import random
from Crypto.Cipher import AES

from util.dtools import not_empty


block_size = AES.block_size
pad = lambda s: s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)
unpad = lambda s: s[0:-ord(s[-1])]


def encrypt(plain, *args):
    return base64.b64encode(AES.new(pad((''.join(args) * 11)[::-3][:29])).encrypt(pad(plain)))


def decrypt(cipher, *args):
    return unpad(AES.new(pad((''.join(args) * 11)[::-3][:29])).decrypt(base64.b64decode(cipher)))


def nonce_str():
    return str(random.random())[2:]


def check_sign(data, key, method):
    if method == 'md5':
        sign = data.get('sign')
        nonce_key = 'nonce_str'
    elif method == 'sha1':
        sign = data.get('signature')
        nonce_key = 'nonce'
    else:
        return False
    if not sign or nonce_key not in data:
        return False
    return build_sign(data, key, method) == sign


def build_sign(data, key, method='md5'):
    if method == 'md5':
        p = [(k, v.decode('utf8')) if type(v) is str else
             (k, unicode(v))
             for k, v in sorted(data.iteritems()) if not_empty(v) and k != 'sign']
        return hashlib.md5(
            (u'&'.join([k + u'=' + v for k, v in p]) + u'&key=' + key).encode('utf8')).hexdigest().upper()
    elif method == 'sha1':
        p = [key, data.get('timestamp', ''), data.get('nonce', '')]
        p.sort()
        return hashlib.sha1(''.join(p)).hexdigest()
    else:
        return ''


def add_sign(data, key, method='md5'):
    data['nonce_str'] = nonce_str()
    data['sign'] = build_sign(data, key, method)


def get_uid(appid, openid):
    return hashlib.md5(appid + '_' + openid).hexdigest()


def get_phone_code(openid, phone, magic_str=''):
    if not magic_str:
        magic_str = str(random.random())[-2:]
    s1 = '%02d' % ((int(hashlib.md5(openid + magic_str).hexdigest()[:4], 16) + 123) % 100)
    s2 = '%02d' % ((int(hashlib.md5(phone + magic_str).hexdigest()[:4], 16) + 321) % 100)
    return s1 + s2 + magic_str