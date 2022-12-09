import os.path as path
import subprocess

from flask import Flask, make_response, render_template

import db
from weather import get_summary

dir_path = path.dirname(path.realpath(__file__))
template_path = path.join(dir_path, 'www')
static_path = path.join(dir_path, 'www/img')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)


def sql_query_2_json(sql):
    with db.run_sql(sql, row_factory=True) as result:
        data = list(map(dict, result.fetchall()))
    response = make_response(data)
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
    return sql_query_2_json(sql)


@app.route("/stats_pump")
def stats_pump():
    sql = '''
        SELECT pump, date(datestamp) date, time(datestamp) as time, duration FROM pumps
        WHERE action = 'ON';
    '''
    return sql_query_2_json(sql)


@app.route("/stats_weather")
def stats_weather():
    data = get_summary(days=-100)
    response = make_response(data)
    response.mimetype = 'application/json'
    return response


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
