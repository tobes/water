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


def sql_select(sql, data=None, row_factory=False):
    with sqlite3.connect(config.SQLITE_DB) as con:
        if row_factory:
            con.row_factory = sqlite3.Row
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

    with sql_run(sql_max_accurracy, (date, sensor)) as result:
        for row in result:
            max_accuracy = row[0]

    with sql_run(sql_accurate, (max_accuracy, max_accuracy, date, sensor)) as result:
        for row in result:
            record = level_record(row, date=date, sensor=sensor, accuracy=0)
            save_data('level_summary', **record)
            print('update levels for', date, 'accuracy', max_accuracy)


def update_levels():
    sql = '''
        SELECT DISTINCT date(datestamp) as date, l.sensor
        FROM levels l
        LEFT JOIN level_summary ls
        ON date(l.datestamp) = ls.date
        WHERE ls.date IS NULL
        ORDER BY date(datestamp)
    '''

    for update in sql_select(sql):
        print('update levels for', update[0])
        update_levels_for_date(*update)


def update_weather():

    import weather

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
    import json

    sql = '''
        SELECT DISTINCT w.datestamp, w.json
        FROM weather w
        LEFT JOIN weather_summary_hourly wsh
        ON w.datestamp = wsh.datestamp
        WHERE wsh.datestamp IS NULL
        ORDER BY w.datestamp
    '''

    output = []

    for datestamp, json_data in sql_select(sql):
        print('update weather_summary_hourly', datestamp)
        data = json.loads(json_data)
        rain = data.get('rain', {}).get('1h', 0)
        main = data.get('main', {})
        info = {
            'datestamp': datestamp,
            'temp': main.get('temp'),
            'temp_min': main.get('temp_min'),
            'temp_max': main.get('temp_max'),
            'humidity': main.get('humidity'),
            'pressure': main.get('pressure'),
            'rain': rain,
        }
        save_or_update_data('weather_summary_hourly', ('datestamp',), info)
    return output


def update_recent_levels():
    sql_execute('DELETE FROM level_summary AS ls WHERE ls.date >= date("now","-5 day")')
    update_levels()


def update_recent_weather():
    sql_execute('DELETE FROM weather_summary AS ws WHERE ws.date >= date("now","-1 day")')
    return update_weather()


def update_recent_weather_hourly():
    sql_execute(
        'DELETE FROM weather_summary_hourly AS wsh WHERE wsh.datestamp >= date("now","-1 day")'
    )
    return update_weather_hourly()


def clean_timestamps():
    TABLE = "weather"
    PERIOD = config.WEATHER_INTERVAL // 60
   # TS = {'hours': -1}
    TS = {}


    import util
    from datetime import datetime
    sql= 'SELECT datestamp FROM ' + TABLE +' WHERE datestamp > "2022-12-19 19:00:00"'
    timestamps = []
    with sql_run(sql) as result:
        for (timestamp, ) in result:
            timestamps.append(timestamp)

    for timestamp in timestamps:
        ts = datetime.fromisoformat(timestamp)
        new_ts = util.timestamp_clean(ts, period=PERIOD, **TS)
        if timestamp != new_ts:
            print('%r %r'%(timestamp,new_ts))
         #   sql= 'UPDATE ' + TABLE + ' SET datestamp=? WHERE datestamp=?'
         #   sql_execute(sql, (new_ts, timestamp))


# Initiate tables
for sql in sql_create:
    sql_execute(sql)


if __name__ == '__main__':
    update_recent_levels()
    update_recent_weather()
