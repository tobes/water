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
        accuracy REAL,
        depth REAL,
        volume REAL
    )
''',

'''
    CREATE TABLE IF NOT EXISTS level_summary(
        sensor INT,
        date,
        max_depth REAL,
        min_depth REAL,
        last_depth REAL,
        max_volume REAL,
        min_volume REAL,
        last_volume REAL,
        accuracy REAL,
        PRIMARY KEY (sensor, date)
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
        date PRIMARY KEY,
        temp_min REAL,
        temp_max REAL,
        rain REAL
    ) ''',
    '''
    CREATE TABLE IF NOT EXISTS weather_summary_hourly(
        datestamp PRIMARY KEY,
        temp REAL,
        temp_min REAL,
        temp_max REAL,
        humidity REAL,
        pressure REAL,
        rain REAL
    ) ''',
    '''
    CREATE TABLE IF NOT EXISTS auto(
        datestamp,
        duration INT
    )
''',
]



@contextmanager
def sql_run(sql, data=None, row_factory=False):
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


def sql_execute(sql, data=None):
    with sqlite3.connect(config.SQLITE_DB) as con:
        con.execute(sql, data or tuple())


def sql_select(sql, data=None, row_factory=False, as_dict=False, as_lists=False):
    with sqlite3.connect(config.SQLITE_DB) as con:
        if row_factory or as_dict:
            con.row_factory = sqlite3.Row
        if as_dict:
            output = list(map(dict, con.execute(sql, data or tuple())))
        elif as_lists:
            output = list(map(list, con.execute(sql, data or tuple())))
        else:
            output = list(con.execute(sql, data or tuple()))
    return output


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


def save_or_update_data(table, primary_key, data):
    if isinstance(data, sqlite3.Row):
        data = dict(data)
    insert_columns = ['%r' % k for k in data]
    update_columns = [k for k in data if k not in primary_key]
    update_set = ['%r=excluded.%r' % (k, k) for k in update_columns]

    sql = 'INSERT INTO %r (' % table
    sql += ', '.join(insert_columns)
    sql += ') VALUES ('
    sql += ', '.join(['?' for k in data])
    sql += ')'
    sql += ' ON CONFLICT('
    sql += ', '.join(primary_key)
    sql += ')'
    sql += ' DO UPDATE SET '
    sql += ', '.join(update_set)

    sql_execute(sql, tuple(v for v in data.values()))


def update_level_sumary_for_date(date, sensor):

    print('update levels for sensor', sensor, date)

    sql = '''
    SELECT (SELECT  min(accuracy) FROM levels
    WHERE date(datestamp) = :date AND sensor = :sensor
    ) as accuracy,
    date(datestamp) as date,
    max(volume) as max_volume,
    min(volume) as min_volume,
    max(depth) as max_depth,
    min(depth) as min_depth
    FROM levels l
    WHERE date(datestamp) = :date AND sensor = :sensor
    AND l.accuracy = accuracy;
    '''
    params = {'date': date, 'sensor': sensor}
    for row in sql_select(sql, params, as_dict=True):
        save_or_update_data('level_summary', ('date', 'sensor'), row)

    sql = '''
    SELECT date(datestamp) as date, l.sensor,
    depth as last_depth, volume as last_volume
    FROM levels l JOIN level_summary ls
    ON date(l.datestamp) = ls.date
    AND l.sensor = ls.sensor
    AND l.accuracy = ls.accuracy
    WHERE date(datestamp) = :date AND l.sensor = :sensor
    ORDER BY datestamp DESC
    LIMIT 1
    '''
    for row in sql_select(sql, params, as_dict=True):
        save_or_update_data('level_summary', ('date', 'sensor'), row)


def update_missing_level_summary():
    sql = '''
        SELECT DISTINCT date(datestamp) as date, l.sensor
        FROM levels l
        LEFT JOIN level_summary ls
        ON date(l.datestamp) = ls.date
        WHERE ls.date IS NULL
        ORDER BY date(datestamp)
    '''

    for update in sql_select(sql):
        update_level_sumary_for_date(*update)


def update_weather():

    sql = '''
        SELECT date(datestamp) as date,
        max(wsh.temp_max) as temp_max,
        min(wsh.temp_min) as temp_min,
        sum(wsh.rain) as rain

        FROM weather_summary_hourly wsh
        LEFT JOIN weather_summary ws
        ON date(wsh.datestamp) = ws.date

        WHERE ws.date IS NULL
        GROUP BY date(datestamp)
        ORDER BY date(datestamp)
    '''

    for update in sql_select(sql, row_factory=True):
        print('update weather_summary for', update['date'])
        save_or_update_data('weather_summary', ('date',), update)


def update_weather_hourly():

    import weather

    sql = '''
        SELECT DISTINCT w.datestamp, w.json
        FROM weather w
        LEFT JOIN weather_summary_hourly wsh
        ON w.datestamp = wsh.datestamp
        WHERE wsh.datestamp IS NULL
        ORDER BY w.datestamp
    '''

    for datestamp, json_data in sql_select(sql):
        print('update weather_summary_hourly', datestamp)
        info = weather.weather_json_2_dict(json_data)
        info['datestamp'] = datestamp
        save_or_update_data('weather_summary_hourly', ('datestamp',), info)


def update_recent_levels():
    sql_execute('DELETE FROM level_summary AS ls WHERE ls.date >= date("now","-2 day")')
    update_missing_level_summary()


def update_recent_weather():
    sql_execute('DELETE FROM weather_summary AS ws WHERE ws.date >= date("now","-1 day")')
    return update_weather()


def update_recent_weather_hourly():
    sql_execute(
        'DELETE FROM weather_summary_hourly AS wsh WHERE wsh.datestamp >= date("now","-1 day")'
    )
    return update_weather_hourly()


# Initiate tables
for sql in sql_create:
    sql_execute(sql)


if __name__ == '__main__':
    update_recent_levels()
    update_missing_level_summary()
    update_recent_weather_hourly()
    update_recent_weather()
