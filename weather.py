import json

from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

import db
import config
import util



def weather_json_2_dict(json_data, full=False):
    """
    convert weather json into a more useful dict
    """
    data = json.loads(json_data)
    rain = data.get('rain', {}).get('1h', 0)
    main = data.get('main', {})
    info = {
        'temp': main.get('temp'),
        'temp_min': main.get('temp_min'),
        'temp_max': main.get('temp_max'),
        'humidity': main.get('humidity'),
        'pressure': main.get('pressure'),
        'rain': rain,
    }
    if full:
        info['icon'] = data.get('weather', [{}])[0].get('icon', 'unknown')
        sql = 'SELECT rain FROM weather_summary WHERE date = ?'
        date = datetime.now().strftime('%Y-%m-%d')
        result = db.sql_select(sql, (date,))
        if result:
            info['rain_today'] = result[0][0]

    return info


def past_weather(timestamp=None):
    sql = '''
    SELECT CAST((JULIANDAY(:ts) - JULIANDAY(datestamp)) as INT) AS day,
    MAX(temp_max) as temp_max,
    MIN(temp_min) as temp_min,
    SUM(rain) as rain
    FROM weather_summary_hourly
    GROUP BY day
    HAVING day >=0 and day < 10
    ORDER BY day;
    '''
    ts = util.timestamp_clean(timestamp=timestamp, period=60, hours=-1)
    print('past_weather for', ts)
    return db.sql_select(sql, {'ts':ts}, as_dict=True)


def auto_estimate(timestamp=None):
    recent = past_weather(timestamp)
    # ignore if no data for the day
    if len(recent) == 0 or recent[0]['day'] != 0:
        return 0
    today = recent[0]
    # check we meet the minimum temperatures
    if (
            today['temp_max'] < config.AUTO_MIN_TEMP_MAX or
            today['temp_min'] < config.AUTO_MIN_TEMP_MIN
    ):
        return 0

    rain = 0
    for data in reversed(recent):
        # each day we reduce the effective rain
        rain = max(0, rain - config.AUTO_IGNORED_WATER_PER_DAY)
        # add the rain for that day
        rain += data['rain']
    if rain <= config.AUTO_MIN_RAIN:
        rain = 0

    degrees = today['temp_max'] - config.AUTO_MIN_TEMP_MAX
    duration = (config.AUTO_SECONDS_PER_DEGREE * degrees)
    duration -= config.AUTO_SECONDS_PER_MM_RAIN * rain

    if duration < 0:
        duration = 0

    duration -= duration % 5
    if duration > config.AUTO_MIN_SECONDS:
        duration = min(duration, config.AUTO_MAX_SECONDS)
    return duration
