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


def sql_query_2_json(sql=None, values=None, cols=None, process=None):
    if sql:
        with db.run_sql(sql, row_factory=True) as result:
            values = list(map(list, result.fetchall()))
    if process:
        values = process(values)
    output = {
        'cols': cols,
        'values': values,
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
        SELECT date, max_depth, min_depth, last_depth
        FROM level_summary
        ORDER BY date DESC;
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'max', 'type':'int', 'units': 'mm'},
       {'title': 'min', 'type':'int', 'units': 'mm'},
       {'title': 'last', 'type':'int', 'units': 'mm'},
    ]
    return sql_query_2_json(sql=sql, cols=cols)


@app.route("/stats_volume")
def stats_volumes():
    sql = '''
        SELECT date, max_volume, min_volume, last_volume
        FROM level_summary
        ORDER BY date DESC;
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'max', 'type':'float', 'units': 'litres'},
       {'title': 'min', 'type':'float', 'units': 'litres'},
       {'title': 'last', 'type':'float', 'units': 'litres'},
    ]
    return sql_query_2_json(sql=sql, cols=cols)


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
    return sql_query_2_json(sql=sql, cols=cols)


@app.route("/stats_pump")
def stats_pump():
    sql = '''
        SELECT pump, date(datestamp) date, time(datestamp) as time, duration FROM pumps
        WHERE action = 'ON'
        ORDER BY datestamp DESC;
    '''
    cols = [
       {'title': 'pump', 'type':'str'},
       {'title': 'date', 'type':'date'},
       {'title': 'time', 'type':'time'},
       {'title': 'duration', 'type':'seconds'},
    ]
    return sql_query_2_json(sql=sql, cols=cols)


@app.route("/stats_weather")
def stats_weather():
    sql = '''
        SELECT date, temp_min, temp_max, rain
        FROM weather_summary
        ORDER BY date DESC;
    '''

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'min', 'type':'float', 'units': '°C'},
       {'title': 'max', 'type':'float', 'units': '°C'},
       {'title': 'rain', 'type':'float', 'units':'mm'},
    ]

    return sql_query_2_json(sql=sql, cols=cols)


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
