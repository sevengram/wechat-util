# -*- coding: utf-8 -*-

import tornado.web
import tornado.gen

from util import security


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, sign_check=True, *args, **kwargs):
        self.sign_check = sign_check

    def get_all_arguments(self):
        return {k: v[0].decode('utf8') for k, v in self.request.arguments.items()}

    def assign_arguments(self, essential, extra=None):
        try:
            r1 = {key: self.get_argument(key) for key in essential}
            r2 = {key: self.get_argument(key, defult) for key, defult in extra or []}
        except tornado.web.MissingArgumentError:
            raise tornado.web.HTTPError(400)
        for key in essential:
            if not r1.get(key):
                raise tornado.web.HTTPError(400)
        return dict(r1, **r2)

    def check_signature(self, refer_dict, sign_key, method):
        if not sign_key:
            self.send_response(err_code=8002)
            return False
        if not security.check_sign(refer_dict, sign_key, method):
            self.send_response(err_code=8001)
            return False
        return True

    def send_response(self, data=None, err_code=0, err_msg=''):
        resp = {'err_code': err_code,
                'err_msg': err_msg,
                'data': data or ''}
        self.write(resp)
        self.finish()

    def write_error(self, status_code, **kwargs):
        self.write({'err_code': status_code})

    def data_received(self, chunk):
        pass
