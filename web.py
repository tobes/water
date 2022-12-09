import os.path as path
import subprocess

from flask import Flask, make_response, render_template

import db
from weather import get_summary

dir_path = path.dirname(path.realpath(__file__))
template_path = path.join(dir_path, 'www')
static_path = path.join(dir_path, 'www/img')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)


def sql_query_2_json(sql, cols):
    with db.run_sql(sql, row_factory=True) as result:
        values = list(map(list, result.fetchall()))
    output = {
        'cols': cols,
        'values': values,
    }
    response = make_response(output)
    response.mimetype = 'application/json'
    return response


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/img/<path:path>')
def send_report(path):
    img_path = path.join(dir_path, 'www/img')
    return send_from_directory(img_path, path)


@app.route("/status")
def status():
    data = subprocess.run(['python3', 'client.py', 'status'], stdout=subprocess.PIPE).stdout
    response = make_response(data)
    response.mimetype = 'application/json'
    return response


@app.route("/stats")
def stats_levels():
    sql = '''
        SELECT date(datestamp) as date,
                max(level) as max, min(level) as min
        FROM levels
        WHERE accuracy <3
        GROUP BY date(datestamp);
    '''
    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'max', 'type':'int', 'units': 'mm'},
       {'title': 'min', 'type':'int', 'units': 'mm'},
    ]
    return sql_query_2_json(sql, cols)


@app.route("/stats_pump")
def stats_pump():
    sql = '''
        SELECT pump, date(datestamp) date, time(datestamp) as time, duration FROM pumps
        WHERE action = 'ON';
    '''
    cols = [
       {'title': 'pump', 'type':'str'},
       {'title': 'date', 'type':'date'},
       {'title': 'time', 'type':'time'},
       {'title': 'duration', 'type':'int', 'units': 's'},
    ]
    return sql_query_2_json(sql, cols)


@app.route("/stats_weather")
def stats_weather():
    data = get_summary(days=-100)

    cols = [
       {'title': 'date', 'type':'date'},
       {'title': 'rain', 'type':'time'},
       {'title': 'max temp', 'type':'float', 'units': '°C'},
       {'title': 'min temp', 'type':'float', 'units': '°C'},
    ]
    values = [
        [x['date'], x['rain'], x['temp_max'], x['temp_min']]
        for x in data
    ]
    output = {
        'cols': cols,
        'values': values,
    }
    response = make_response(output)
    response.mimetype = 'application/json'
    return response


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
