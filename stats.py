import json
import time

from datetime import datetime, timedelta

from flask import make_response

import db
import weather

from config import STATS_MAX_DAYS


def stats_depths():
    sql = '''
        SELECT date, min_depth, max_depth, last_depth
        FROM level_summary
        WHERE date > date('now', :offset)
        ORDER BY date DESC;
    '''

    params = {'offset': "-%s day" % STATS_MAX_DAYS}

    values = db.sql_select(sql, params)

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'int', 'units': 'mm'},
       {'title': 'max', 'type':'int', 'units': 'mm'},
       {'title': 'last', 'type':'int', 'units': 'mm'},
    ]

    graph = {
        'dataset': {
            'min': {
                'label': 'Min Depth',
                'type': 'bar',
                'backgroundColor': '#009879',
                'borderColor': '#009879',
                'order': 0,
            },
            'max': {
                'label': 'Max Depth',
                'type': 'bar',
                'backgroundColor': '#999999',
                'borderColor': '#999999',
                'order': 1,
            },
        },
        'axis': {
            'y': {
                'tick_units': 'mm',
                'options':{
                    'beginAtZero': True,
                },
            },
            'x': {
                'stacked': True,
            },
        },
    }

    output = {
        'cols': cols,
        'values': values,
        'graph':graph,
    }
    return output


def stats_volumes():
    sql = '''
        SELECT date, min_volume, max_volume, last_volume
        FROM level_summary
        WHERE date > date('now', :offset)
        ORDER BY date DESC;
    '''

    params = {'offset': "-%s day" % STATS_MAX_DAYS}

    values = db.sql_select(sql, params)

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'float', 'units': 'litres'},
       {'title': 'max', 'type':'float', 'units': 'litres'},
       {'title': 'last', 'type':'float', 'units': 'litres'},
    ]

    graph = {
        'dataset': {
            'min': {
                'label': 'Min Volume',
                'type': 'bar',
                'backgroundColor': '#009879',
                'borderColor': '#009879',
                'order': 0,
            },
            'max': {
                'label': 'Max Volume',
                'type': 'bar',
                'backgroundColor': '#999999',
                'borderColor': '#999999',
                'order': 1,
            },
        },
        'axis': {
            'y': {
                'tick_units': 'L',
                'options':{
                    'beginAtZero': True,
                },
            },
            'x': {
                'stacked': True,
            },
        },
    }

    output = {
        'cols': cols,
        'values': values,
        'graph':graph,
    }
    return output


def stats_auto():

    values = []
    utc = datetime.utcnow()
    dt = utc.replace(hour=19) - timedelta(days=STATS_MAX_DAYS)
    one_day = timedelta(days=1)
    while dt <= utc:
        date = dt.strftime('%Y-%m-%d')
        time = dt.strftime('%H:%M')
        auto = weather.auto_estimate(dt)
        values.append([date, time, auto])
        dt += one_day

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'time', 'type':'time'},
       {'title': 'duration', 'type':'seconds'},
    ]

    graph = {
        'dataset': {
            'duration': {
                'label': 'Duration',
                'type': 'bar',
                'backgroundColor': '#009879',
                'borderColor': '#009879',
            },
        },
        'axis': {
            'y': {
                'tick_units': 'seconds',
                'options':{
                    'beginAtZero': True,
                },
                'ticks': {
                    'stepSize': 10,
                },
            },
        },
    }

    output = {
        'cols': cols,
        'values': values,
        'graph':graph,
    }
    return output


def stats_pump():
    sql = '''
        SELECT date(datestamp) as date,
        pump, time(datestamp) as time, duration
        FROM pumps
        WHERE action = 'ON'
        AND date(datestamp) > date('now', :offset)
        ORDER BY datestamp DESC;
    '''

    params = {'offset': "-%s day" % STATS_MAX_DAYS}

    values = db.sql_select(sql, params)

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'pump', 'type':'str'},
       {'title': 'time', 'type':'time'},
       {'title': 'duration', 'type':'seconds'},
    ]

    graph = {
        'dataset': {
            'duration': {
                'label': 'Duration',
                'type': 'bar',
                'backgroundColor': '#009879',
                'borderColor': '#009879',
            },
        },
        'axis': {
            'y': {
                'tick_units': 'seconds',
                'options':{
                    'beginAtZero': True,
                },
                'ticks': {
                    'stepSize': 10,
                },
            },
        },
    }

    output = {
        'cols': cols,
        'values': values,
        'graph':graph,
    }
    return output


def stats_weather():
    sql = '''
        SELECT date, temp_min, temp_max, rain
        FROM weather_summary
        WHERE date > date('now', :offset)
        ORDER BY date DESC
    '''

    params = {'offset': "-%s day" % (STATS_MAX_DAYS + 1)}

    values = db.sql_select(sql, params)

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'float', 'units': '°C'},
       {'title': 'max', 'type':'float', 'units': '°C'},
       {'title': 'rain', 'type':'float', 'units':'mm'},
    ]

    graph = {
        'dataset': {
            'min': {
                'label': 'Min Temp',
                'tension': 0.1,
                'fill': False,
                'backgroundColor': '#4169E1',
                'borderColor': '#4169E1',
            },
            'max': {
                'label': 'Max Temp',
                'tension': 0.1,
                'fill': False,
                'backgroundColor': '#DC143C',
                'borderColor': '#DC143C',
            },
            'rain': {
                'type': 'bar',
                'label': 'Rainfall',
                'backgroundColor': '#99ccff',
                'borderColor': '#99ccff',
                'yAxisID': 'rain',
            },
        },
        'axis': {
            'y': {
                'tick_units': '°C',
            },
            'rain': {
                'position': 'right',
                'tick_units': 'mm',
                'grid': {
                    'color': '#B0E0E6',
                },
                'ticks': {
                    'color': '#2885c7',
                },
                'options':{
                    'beginAtZero': True,
                },
            },
        },
    }

    output = {
        'cols': cols,
        'values': values,
        'graph':graph,
    }
    return output


def get_stats():
    output = {
        'epoch_time': time.time(),
        'data': [
        {'name': 'Auto','data': stats_auto()},
        {'name': 'Pump','data': stats_pump()},
        {'name': 'Weather','data': stats_weather()},
        {'name': 'Levels','data': stats_depths()},
        {'name': 'Volumes','data': stats_volumes()},
        ],
    }
    response = make_response(json.dumps(output,  separators=(',', ':')))
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
