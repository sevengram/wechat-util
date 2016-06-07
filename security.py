# -*- coding: utf-8 -*-

import base64
import hashlib
import logging
import random
import socket
import string
import struct
from Crypto.Cipher import AES

import time

from util.dtools import not_empty


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
        p = [key, data.get('timestamp', ''), data.get('nonce', ''), data.get('encrypt', '')]
        p.sort()
        return hashlib.sha1(''.join(p)).hexdigest()
    else:
        return ''


def add_sign(data, key, method='md5'):
    data['nonce_str'] = nonce_str()
    data['sign'] = build_sign(data, key, method)


def add_sign_wechat(data, key):
    data['nonce'] = nonce_str()
    data['timestamp'] = str(int(time.time()))
    data['sign'] = build_sign(data, key, 'sha1')


def get_phone_code(openid, phone, magic_str=''):
    if not magic_str:
        magic_str = str(random.random())[-2:]
    s1 = '%02d' % ((int(hashlib.md5(openid + magic_str).hexdigest()[:4], 16) + 123) % 100)
    s2 = '%02d' % ((int(hashlib.md5(phone + magic_str).hexdigest()[:4], 16) + 321) % 100)
    return s1 + s2 + magic_str


class PKCS7Encoder():
    """提供基于PKCS7算法的加解密接口"""

    block_size = 32

    def encode(self, text):
        """ 对需要加密的明文进行填充补位
        @param text: 需要进行填充补位操作的明文
        @return: 补齐明文字符串
        """
        text_length = len(text)
        # 计算需要填充的位数
        amount_to_pad = self.block_size - (text_length % self.block_size)
        if amount_to_pad == 0:
            amount_to_pad = self.block_size
        # 获得补位所用的字符
        pad = chr(amount_to_pad)
        return text + pad * amount_to_pad

    def decode(self, decrypted):
        """
        删除解密后明文的补位字符
        @param decrypted: 解密后的明文
        @return: 删除补位字符后的明文
        """
        pad = ord(decrypted[-1])
        if pad < 1 or pad > 32:
            pad = 0
        return decrypted[:-pad]


class Prpcrypt(object):
    """提供接收和推送给公众平台消息的加解密接口"""

    def __init__(self, key):
        self.key = base64.b64decode(key + "=")
        # 设置加解密模式为AES的CBC模式
        self.mode = AES.MODE_CBC

    def encrypt(self, text, appid):
        """
        对明文进行加密
        @param text: 需要加密的明文
        @param appid: AppID
        @return: 加密得到的字符串
        """
        text = text.encode('utf8')
        appid = appid.encode('utf8')
        # 16位随机字符串添加到明文开头
        text = self.get_random_str() + struct.pack("I", socket.htonl(len(text))) + text + appid
        # 使用自定义的填充方式对明文进行补位填充
        pkcs7 = PKCS7Encoder()
        text = pkcs7.encode(text)
        # 加密
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        ciphertext = cryptor.encrypt(text)
        # 使用BASE64对加密后的字符串进行编码
        return base64.b64encode(ciphertext)

    def decrypt(self, text, appid):
        """
        对解密后的明文进行补位删除
        @param text: 密文
        @param appid: AppID
        @return: 删除填充补位后的明文
        """
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        # 使用BASE64对密文进行解码，然后AES-CBC解密
        plain_text = cryptor.decrypt(base64.b64decode(text))

        pad = ord(plain_text[-1])
        # 去掉补位字符串
        # pkcs7 = PKCS7Encoder()
        # plain_text = pkcs7.encode(plain_text)
        # 去除16位随机字符串
        content = plain_text[16:-pad]
        xml_len = socket.ntohl(struct.unpack("I", content[: 4])[0])
        xml_content = content[4: xml_len + 4]
        from_appid = content[xml_len + 4:]
        if from_appid != appid:
            return None
        return xml_content

    def get_random_str(self):
        """
        随机生成16位字符串
        @return: 16位字符串
        """
        rule = string.letters + string.digits
        return "".join(random.sample(rule, 16))
