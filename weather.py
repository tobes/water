import json

from urllib.parse import urlencode
from urllib.request import urlopen

import db
import config
import util


def get_weather(save=False):
    query_data = {
        'lat': config.LAT,
        'lon': config.LON,
        'appid': config.WEATHER_API_KEY,
        'units': 'metric',
    }

    query_string = urlencode(query_data)
    content = urlopen(config.WEATHER_API_URL + query_string).read().decode('utf-8')

    if save:
        db.save_data(
            'weather',
            json=content,
            date=util.timestamp()
        )
        db.update_recent_weather()
    return content



def get_summary(ts=None, days=-30):
    sql = '''
        SELECT json, date(datestamp) FROM weather
        WHERE date(datestamp) >= ?
        ORDER BY date(datestamp)
    '''
    if ts == None:
        ts = util.timestamp_zeroed(days=days)

    out = []

    with db.run_sql(sql, (ts,)) as result:
        current_date = None
        rain = 0.0
        temp_min = None
        temp_max = None
        for json_data, date in result:
            if date != current_date:
                if current_date:
                    out.append({
                        'date': current_date,
                        'rain': rain,
                        'temp_min': temp_min,
                        'temp_max': temp_max,
                    })
                #print(current_date, rain, temp_min, temp_max)
                current_date = date
                rain = 0.0
                temp_min = None
                temp_max = None
            data = json.loads(json_data)
            if 'rain' in data:
                rain += data['rain']['1h']
            main = data['main']

            if temp_min is None:
                temp_min = main['temp_min']
            else:
                temp_min = min(temp_min, main['temp_min'])

            if temp_max is None:
                temp_max = main['temp_max']
            else:
                temp_max = max(temp_max, main['temp_max'])
        #print(current_date, rain, temp_min, temp_max)
        out.append({
            'date': current_date,
            'rain': rain,
            'temp_min': temp_min,
            'temp_max': temp_max,
        })
    return out


def get_last_period(days=-1, **td):
    td['days'] = days
    timestamp = util.timestamp(**td)
    sql = 'SELECT json, date(datestamp) FROM weather WHERE datestamp >= ?'
    with db.run_sql(sql, (timestamp,)) as result:
        current_date = None
        rain = 0.0
        temp_min = None
        temp_max = None
        for json_data, date in result:
            data = json.loads(json_data)
            if 'rain' in data:
                rain += data['rain']['1h']
            main = data['main']

            if temp_min is None:
                temp_min = main['temp_min']
            else:
                temp_min = min(temp_min, main['temp_min'])

            if temp_max is None:
                temp_max = main['temp_max']
            else:
                temp_max = max(temp_max, main['temp_max'])
        return {
            'rain': rain,
            'temp_min': temp_min,
            'temp_max': temp_max,
        }


if __name__ == '__main__':
    print(get_last_period())
    print(get_summary())
    print(get_weather())
