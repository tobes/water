import os.path
import subprocess

from flask import Flask, make_response, render_template, request

import db
from device import Butt
from stats import get_stats

dir_path = os.path.dirname(os.path.realpath(__file__))
template_path = os.path.join(dir_path, 'www')
static_path = os.path.join(dir_path, 'www/static')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/sw.js')
def service_worker():
    path = os.path.join(static_path, 'sw.js')
    response = make_response(open(path))
    response.headers['Content-Type'] = 'application/javascript; charset=UTF-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    response.headers['Service-Worker-Allowed'] = 'https://tollington.duckdns.org/'
    return response


@app.route("/status")
def status():
    status_cmd = ['python3', 'client.py', 'status']
    if 'fast' in request.args:
        status_cmd.append('--fast')
    data = subprocess.run(status_cmd, stdout=subprocess.PIPE).stdout
    response = make_response(data)
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/stats")
def stats():
    return get_stats()


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
