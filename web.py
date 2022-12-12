import os.path
import subprocess

from flask import Flask, make_response, render_template

import db
from weather import get_summary
from device import Butt
from stats import get_stats

dir_path = os.path.dirname(os.path.realpath(__file__))
template_path = os.path.join(dir_path, 'www')
static_path = os.path.join(dir_path, 'www/static')

app = Flask(__name__, template_folder=template_path, static_folder=static_path)


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


@app.route("/stats")
def stats():
    return get_stats()


if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', debug=True)
