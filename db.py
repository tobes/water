import sqlite3

from contextlib import contextmanager

import config


sql_create = [
'''
    CREATE TABLE IF NOT EXISTS levels(
        sensor INT,
        datestamp,
        level INT,
        level2 INT,
        accuracy REAL
    )
''',

'''
    CREATE TABLE IF NOT EXISTS pumps(
        pump INT,
        datestamp,
        duration INT,
        action
    )
''',

'''
    CREATE TABLE IF NOT EXISTS weather(
        json,
        datestamp
    )
''',

'''
    CREATE TABLE IF NOT EXISTS auto(
        datestamp,
        time INT
    )
''',
]

con = sqlite3.connect(config.SQLITE_DB)

for sql in sql_create:
    with con:
        con.execute(sql)

con.close()


def save_data(table, **kw):
    sql = 'INSERT INTO %r (' % table
    sql += ', '.join(['%r' % k for k in kw])
    sql += ') VALUES ('
    sql += ', '.join(['?' for k in kw])
    sql += ');'
    con = sqlite3.connect(config.SQLITE_DB)
    with con:
        con.execute(sql, tuple(v for v in kw.values()))
    con.close()



@contextmanager
def run_sql(sql, data=None, row_factory=False):
    con = sqlite3.connect(config.SQLITE_DB)
    if row_factory:
        con.row_factory = sqlite3.Row
    with con:
        result = con.execute(sql, data or tuple())
        try:
            yield result
        finally:
            pass
    con.close()
