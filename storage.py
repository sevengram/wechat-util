# -*- coding: utf-8 -*-

import hashlib
from itertools import chain

import MySQLdb
import MySQLdb.cursors

from util.dtools import not_empty


def get_redis_key(table, data, keys):
    p = [(k, v.decode('utf8')) if type(v) is str else
         (k, unicode(v))
         for k, v in sorted(data.items()) if not_empty(v) and k in keys]
    return hashlib.md5(
        table + ':' + '&'.join([(k + u'=' + v).encode('utf8') for k, v in p])).hexdigest().upper()


class Storage(object):
    def __init__(self, db_name, db_host, db_user, db_pwd):
        self.db_usr = db_user
        self.db_pwd = db_pwd
        self.db_name = db_name
        self.db_host = db_host
        self.connect()

    def connect(self):
        self.connection = MySQLdb.connect(
            user=self.db_usr, passwd=self.db_pwd, host=self.db_host, db=self.db_name, charset='utf8')

    def execute(self, query, args, cursorclass=MySQLdb.cursors.DictCursor):
        need_commit = query.lower().startswith('update')
        cursor = self.connection.cursor(cursorclass)
        result = None
        try:
            cursor.execute(query, args)
            if need_commit:
                cursor.commit()
            result = cursor.fetchone()
        except (AttributeError, MySQLdb.OperationalError):
            self.connection.close()
            self.connect()
            cursor = self.connection.cursor(cursorclass)
            cursor.execute(query, args)
            if need_commit:
                cursor.commit()
            result = cursor.fetchone()
        finally:
            cursor.close()
            return result

    def fetch_all(self, query, args, cursorclass=MySQLdb.cursors.DictCursor):
        cursor = self.connection.cursor(cursorclass)
        result = None
        try:
            cursor.execute(query, args)
            result = cursor.fetchall()
        except (AttributeError, MySQLdb.OperationalError):
            self.connection.close()
            self.connect()
            cursor = self.connection.cursor(cursorclass)
            cursor.execute(query, args)
            result = cursor.fetchall()
        finally:
            cursor.close()
            return list(result or '')

    def get(self, table, queries, select_key='*'):
        queries = {k: v for k, v in queries.iteritems() if not_empty(v)}
        if not queries:
            return None
        placeholders = ' AND '.join(map(lambda n: n + '=%s', queries.keys()))
        request = 'SELECT %s FROM %s WHERE %s' % (select_key, table, placeholders)
        records = self.execute(request, queries.values())
        if not records:
            return None
        else:
            return records if select_key == '*' else records.get(select_key)

    def get_page_list(self, table, queries, page_no, page_size, select_key='*'):
        equal_queries = {k: v for k, v in queries.iteritems() if
                         not_empty(v) and type(v) is not tuple and type(v) is not list}
        open_range_queries = {k: v for k, v in queries.iteritems() if type(v) is tuple and len(v) == 2}
        close_range_queries = {k: v for k, v in queries.iteritems() if type(v) is list and len(v) == 2}
        conditions = \
            map(lambda k: k + '=%s', equal_queries.keys()) + \
            map(lambda k: '%s < ' + k + ' AND ' + k + ' < %s', open_range_queries.keys()) + \
            map(lambda k: '%s <= ' + k + ' AND ' + k + ' <= %s', close_range_queries.keys())
        placeholders = ' AND '.join(conditions)
        where_clause = ' WHERE ' + placeholders if placeholders else ''
        values = equal_queries.values() + list(
            chain.from_iterable(open_range_queries.values() + close_range_queries.values()))
        count_request = 'SELECT count(1) AS `total` FROM %s %s' % (table, where_clause)
        print count_request
        records = self.execute(count_request, values)
        total = records['total'] if records else 0
        if total:
            request = 'SELECT %s FROM %s %s LIMIT %s,%s' % (
                select_key, table, where_clause, page_no * page_size, page_size)
            print request
            return {'total': total, 'list': self.fetch_all(request, values)}
        else:
            return {'total': 0, 'list': []}

    def set(self, table, data, noninsert=None, nonblank=False):
        insert_dict = {k: v for k, v in data.iteritems()
                       if (not nonblank or not_empty(v)) and k not in (noninsert or [])}
        columns = ', '.join(insert_dict.keys())
        insert_holders = ', '.join(['%s'] * len(insert_dict))
        request = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, insert_holders)
        self.execute(request, insert_dict.values())

    def update(self, table, data, filter_data, nonupdate=None, nonblank=False):
        update_dict = {k: v for k, v in data.iteritems()
                       if (not nonblank or not_empty(v)) and k not in (nonupdate or [])}
        update_holders = ', '.join(map(lambda n: n + '=%s', update_dict.keys()))
        where_dict = {k: v for k, v in filter_data.iteritems() if not_empty(v)}
        if where_dict:
            where_holders = ' AND '.join(map(lambda n: n + '=%s', where_dict.keys()))
            request = 'UPDATE %s SET %s WHERE %s' % (table, update_holders, where_holders)
            self.execute(request, update_dict.values() + where_dict.values())

    def replace(self, table, data, noninsert=None, nonupdate=None, nonblank=False):
        insert_dict = {k: v for k, v in data.iteritems()
                       if (not nonblank or not_empty(v)) and k not in (noninsert or [])}
        columns = ', '.join(insert_dict.keys())
        insert_holders = ', '.join(['%s'] * len(insert_dict))
        update_dict = {k: v for k, v in insert_dict.iteritems()
                       if (not nonblank or not_empty(v)) and k not in (nonupdate or [])}
        update_holders = ', '.join(map(lambda n: n + '=%s', update_dict.keys()))
        request = 'INSERT INTO %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE %s' % (
            table, columns, insert_holders, update_holders)
        self.execute(request, insert_dict.values() + update_dict.values())
