import sqlite3

from contextlib import contextmanager

import config

butt = None

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
    CREATE TABLE IF NOT EXISTS level_summary(
        sensor INT,
        date,
        max_depth INT,
        min_depth INT,
        last_depth INT,
        max_volume INT,
        min_volume INT,
        last_volume INT,
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
        datestamp
        json
    )
''',

'''
    CREATE TABLE IF NOT EXISTS weather_summary(
        date,
        temp_min REAL,
        temp_max REAL,
        rain REAL
    )
''',
'''
    CREATE TABLE IF NOT EXISTS auto(
        datestamp,
        duration INT
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


def update_levels_for_date(date, sensor):

    # FIXME use proper butt
    global butt
    if butt is None:
        from device import Butt
        butt = Butt()

    sql_max_accurracy = '''
        SELECT min(accuracy)
        FROM levels
        WHERE date(datestamp) = ?
        AND sensor = ?
    '''

    sql_accurate = '''
        SELECT max(level2) as max, min(level2) as min,
        (SELECT (level2) FROM levels WHERE
          date(datestamp) = date(l.datestamp)
          AND accuracy = ?
          ORDER BY datestamp DESC
            LIMIT 1
        ) AS last
        FROM levels l
        WHERE accuracy = ?
        AND date(datestamp) = ?
        AND sensor = ?
    '''

    def level_record(row, date=None, sensor=None, accuracy=None):
        min_ = butt.calculate_stats(row[0])
        max_ = butt.calculate_stats(row[1])
        last = butt.calculate_stats(row[2])
        return dict(
            date=date,
            sensor=sensor,
            min_depth=min_['depth'],
            max_depth=max_['depth'],
            min_volume=min_['volume'],
            max_volume=max_['volume'],
            last_depth=last['depth'],
            last_volume=last['volume'],
            accuracy=accuracy,
        )

    with run_sql(sql_max_accurracy, (date, sensor)) as result:
        for row in result:
            max_accuracy = row[0]

    with run_sql(sql_accurate, (max_accuracy, max_accuracy, date, sensor)) as result:
        for row in result:
            record = level_record(row, date=date, sensor=sensor, accuracy=0)
            save_data('level_summary', **record)
            print('update levels for', date, 'accuracy', max_accuracy)


def update_levels():
    sql = '''
        SELECT DISTINCT l.sensor, date(datestamp) as date
        FROM levels l
        LEFT JOIN level_summary ls ON date(l.datestamp) = ls.date
        WHERE ls.date IS NULL
        ORDER BY date(datestamp)
    '''

    updates = []

    with run_sql(sql) as result:
        for row in result:
            sensor = row[0]
            date = row[1]
            updates.append([date, sensor])

    for update in updates:
        update_levels_for_date(*update)


def update_weather():

    import weather

    sql = '''
        SELECT DISTINCT date(datestamp) as date
        FROM weather w
        LEFT JOIN weather_summary ws ON date(w.datestamp) = ws.date
        WHERE ws.date IS NULL
        ORDER BY date(datestamp)
    '''

    updates = []
    output = []

    with run_sql(sql) as result:
        for row in result:
            updates.append(row[0])

    for update in updates:
        summary = weather.get_summary(ts=update, days=1)
        if summary:
            output.append(summary[0])
            print('update weather for', summary[0]['date'])
            save_data('weather_summary', **summary[0])
    return output


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


def execute_sql(sql, data=None):
    con = sqlite3.connect(config.SQLITE_DB)
    con.execute(sql, data or tuple())
    con.commit()
    con.close()


def update_recent_levels():
    execute_sql('DELETE FROM level_summary AS ls WHERE ls.date >= date("now","-1 day")')
    update_levels()


def update_recent_weather():
    execute_sql('DELETE FROM weather_summary AS ws WHERE ws.date >= date("now","-1 day")')
    return update_weather()


if __name__ == '__main__':
    update_recent_levels()
    update_recent_weather()
