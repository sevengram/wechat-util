# -*- coding: utf-8 -*-

from itertools import chain

import pymysql

from util.dtools import not_empty


class Sqldb(object):
    def __init__(self, db_name, db_host, db_user, db_pwd):
        self.db_usr = db_user
        self.db_pwd = db_pwd
        self.db_name = db_name
        self.db_host = db_host
        self.connect()

    def connect(self):
        self.connection = pymysql.connect(
            user=self.db_usr, passwd=self.db_pwd, host=self.db_host, db=self.db_name, charset='utf8')

    def execute(self, query, args, cursorclass=pymysql.cursors.DictCursor, commit=False):
        cursor = self.connection.cursor(cursorclass)
        result = None
        try:
            cursor.execute(query, list(args))
            if commit:
                self.connection.commit()
            result = cursor.fetchone()
        except (AttributeError, pymysql.OperationalError) as e:
            self.connection.close()
            self.connect()
            cursor = self.connection.cursor(cursorclass)
            cursor.execute(query, list(args))
            if commit:
                self.connection.commit()
            result = cursor.fetchone()
        finally:
            cursor.close()
            return result

    def fetch_all(self, query, args, cursorclass=pymysql.cursors.DictCursor):
        cursor = self.connection.cursor(cursorclass)
        result = None
        try:
            cursor.execute(query, args)
            result = cursor.fetchall()
        except (AttributeError, pymysql.OperationalError):
            self.connection.close()
            self.connect()
            cursor = self.connection.cursor(cursorclass)
            cursor.execute(query, args)
            result = cursor.fetchall()
        finally:
            cursor.close()
            return list(result or '')

    def get(self, table, queries, select_key='*'):
        queries = {k: v for k, v in queries.items() if not_empty(v)}
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
        equal_queries = {k: v for k, v in queries.items() if
                         not_empty(v) and type(v) is not tuple and type(v) is not list}
        open_range_queries = {k: v for k, v in queries.items() if type(v) is tuple and len(v) == 2}
        close_range_queries = {k: v for k, v in queries.items() if type(v) is list and len(v) == 2}
        conditions = \
            list(map(lambda k: k + '=%s', equal_queries.keys())) + \
            list(map(lambda k: '%s < ' + k + ' AND ' + k + ' < %s', open_range_queries.keys())) + \
            list(map(lambda k: '%s <= ' + k + ' AND ' + k + ' <= %s', close_range_queries.keys()))
        placeholders = ' AND '.join(conditions)
        where_clause = ' WHERE ' + placeholders if placeholders else ''
        values = list(equal_queries.values()) + list(
            chain.from_iterable(list(open_range_queries.values()) + list(close_range_queries.values())))
        count_request = 'SELECT count(1) AS total FROM %s %s' % (table, where_clause)
        records = self.execute(count_request, values)
        total = records['total'] if records else 0
        if total:
            request = 'SELECT %s FROM %s %s LIMIT %s,%s' % (
                select_key, table, where_clause, page_no * page_size, page_size)
            return total, self.fetch_all(request, values)
        else:
            return 0, []

    def set(self, table, data, noninsert=None):
        insert_dict = {k: v for k, v in data.items() if k not in (noninsert or [])}
        columns = ', '.join(insert_dict.keys())
        insert_holders = ', '.join(['%s'] * len(insert_dict))
        request = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, insert_holders)
        self.execute(request, insert_dict.values(), commit=True)

    def update(self, table, data, filters, nonupdate=None):
        update_dict = {k: v for k, v in data.items()
                       if not_empty(v) and k not in (nonupdate or [])}
        update_holders = ', '.join(map(lambda n: n + '=%s', update_dict.keys()))
        where_dict = {k: v for k, v in filters.items() if not_empty(v)}
        if where_dict:
            where_holders = ' AND '.join(map(lambda n: n + '=%s', where_dict.keys()))
            request = 'UPDATE %s SET %s WHERE %s' % (table, update_holders, where_holders)
            self.execute(request, list(update_dict.values()) + list(where_dict.values()), commit=True)

    def replace(self, table, data, noninsert=None, nonupdate=None):
        insert_dict = {k: v for k, v in data.items()
                       if not_empty(v) and k not in (noninsert or [])}
        columns = ', '.join(insert_dict.keys())
        insert_holders = ', '.join(['%s'] * len(insert_dict))
        update_dict = {k: v for k, v in insert_dict.items()
                       if not_empty(v) and k not in (nonupdate or [])}
        update_holders = ', '.join(map(lambda n: n + '=%s', update_dict.keys()))
        request = 'INSERT INTO %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE %s' % (
            table, columns, insert_holders, update_holders)
        self.execute(request, list(insert_dict.values()) + list(update_dict.values()), commit=True)
