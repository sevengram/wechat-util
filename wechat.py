# -*- coding: utf-8 -*-

from urllib.parse import quote_plus


def build_auth_url(appid, url, extra=None, scope='snsapi_base'):
    redirect_uri = quote_plus(url)
    state = quote_plus('&'.join([k + '=' + v for k, v in extra.items()])) if extra else ''
    return 'https://open.weixin.qq.com/connect/oauth2/authorize?' \
           'appid=%s&redirect_uri=%s&response_type=code&scope=%s&state=%s#wechat_redirect' % (
               appid, redirect_uri, scope, state)
