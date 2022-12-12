from flask import make_response

import db


def sql_query_2_json(sql=None, values=None, cols=None, graph=None, process=None):
    if sql:
        with db.run_sql(sql, row_factory=True) as result:
            values = list(map(list, result.fetchall()))
    if process:
        values = process(values)
    output = {
        'cols': cols,
        'values': values,
        'graph':graph,
    }
    return output


def stats_depths():
    sql = '''
        SELECT date, min_depth, max_depth, last_depth
        FROM level_summary
        ORDER BY date DESC;
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'int', 'units': 'mm'},
       {'title': 'max', 'type':'int', 'units': 'mm'},
       {'title': 'last', 'type':'int', 'units': 'mm'},
    ]

    graph = {
        'dataset': {
            'min': {
                'type': 'bar',
                'backgroundColor': '#009879',
                'borderColor': '#009879',
                'order': 0,
            },
            'max': {
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
    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


def stats_volumes():
    sql = '''
        SELECT date, min_volume, max_volume, last_volume
        FROM level_summary
        ORDER BY date DESC;
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'float', 'units': 'litres'},
       {'title': 'max', 'type':'float', 'units': 'litres'},
       {'title': 'last', 'type':'float', 'units': 'litres'},
    ]

    graph = {
        'dataset': {
            'min': {
                'type': 'bar',
                'backgroundColor': '#009879',
                'borderColor': '#009879',
                'order': 0,
            },
            'max': {
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
    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


def stats_auto():
    sql = '''
        SELECT date(datestamp) date, time(datestamp) as time, duration
        FROM auto
        ORDER BY datestamp DESC;
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'time', 'type':'time'},
       {'title': 'duration', 'type':'seconds'},
    ]

    graph = {
        'dataset': {
            'duration': {
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
    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


def stats_pump():
    sql = '''
        SELECT date(datestamp) as date, pump,time(datestamp) as time, duration FROM pumps
        WHERE action = 'ON'
        ORDER BY datestamp DESC;
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'pump', 'type':'str'},
       {'title': 'time', 'type':'time'},
       {'title': 'duration', 'type':'seconds'},
    ]

    graph = {
        'dataset': {
            'duration': {
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
    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


def stats_weather():
    sql = '''
        SELECT date, temp_min, temp_max, rain
        FROM weather_summary
        ORDER BY date DESC
    '''

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'float', 'units': '°C'},
       {'title': 'max', 'type':'float', 'units': '°C'},
       {'title': 'rain', 'type':'float', 'units':'mm'},
    ]

    graph = {
        'dataset': {
            'min': {
                'label': 'Minimum Temperature',
                'tension': 0.1,
                'fill': False,
                'backgroundColor': '#4169E1',
                'borderColor': '#4169E1',
            },
            'max': {
                'label': 'Maximum Temperature',
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
                    'color': '#99ccff',
                },
                'options':{
                    'beginAtZero': True,
                },
            },
        },
    }

    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


def get_stats():
    output = [
        {'name': 'Auto','data': stats_auto()},
        {'name': 'Pump','data': stats_pump()},
        {'name': 'Weather','data': stats_weather()},
        {'name': 'Levels','data': stats_depths()},
        {'name': 'Volumes','data': stats_volumes()},
    ]
    response = make_response(output)
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
