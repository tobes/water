import os.path
import subprocess

from flask import Flask, make_response, render_template

import db
from weather import get_summary
from device import Butt

dir_path = os.path.dirname(os.path.realpath(__file__))
template_path = os.path.join(dir_path, 'www')
static_path = os.path.join(dir_path, 'www/static')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)


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
    response = make_response(output)
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(static_path, path)


@app.route("/status")
def status():
    data = subprocess.run(['python3', 'client.py', 'status'], stdout=subprocess.PIPE).stdout
    response = make_response(data)
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/stats_depth")
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
                'tick_units': ' litres',
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


@app.route("/stats_volume")
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
                'tick_units': ' litres',
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


@app.route("/stats_auto")
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
                'tick_units': ' seconds',
                'options':{
                    'beginAtZero': True,
                },
            },
        },
    }
    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


@app.route("/stats_pump")
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
                'tick_units': ' seconds',
                'options':{
                    'beginAtZero': True,
                },
            },
        },
    }
    return sql_query_2_json(sql=sql, cols=cols, graph=graph)


@app.route("/stats_weather")
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
                'tick_units': ' °C',
            },
            'rain': {
                'position': 'right',
                'tick_units': ' mm',
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


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
