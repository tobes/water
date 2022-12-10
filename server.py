import json
import socket
import sys
import time
import traceback

import db
import config
import device
import util
import weather



devices = {}
butt = device.Butt()
devices['sensor 1'] = device.Meter(gpio_trigger=23, gpio_echo=24, butt=butt)
devices['pump 1'] = device.Relay(gpio=18)
devices['weather'] = device.Weather()


def status(data):
    out = {}
    for name, device in devices.items():
        out[name] = device.status()
    return out


def pump(data):
    duration = data.get('duration')
    auto = data.get('auto')
    pump = data.get('pump')

    if not pump:
        return {'status': 'fail'}

    if auto:
        w = weather.get_last_period()
        # Check minimum temperatures
        if (
                w['temp_max'] < config.AUTO_MIN_TEMP_MAX or
                w['temp_min'] < config.AUTO_MIN_TEMP_MIN
        ):
            duration = 0
            print('cold')
        else:
            sql = '''
                SELECT datestamp FROM pumps WHERE action="ON"
                ORDER BY datestamp DESC LIMIT 1
            '''
            from datetime import datetime, timedelta
            with db.run_sql(sql, row_factory=True) as result:
                datestamp = result.fetchone()['datestamp']
                d1 = datetime.strptime(datestamp, '%Y-%m-%d %H:%M:%S')
                days = 1 + (datetime.now() - d1).days
           # datestamp = '2022-10-21'
            weather_summary = weather.get_summary(ts=datestamp)
            rain = 0
            for v in weather_summary:
                # each day we reduce the eefective rain
                rain = max(0, rain - config.AUTO_IGNORED_WATER_PER_DAY)
                # add the rain for that day
                rain += v['rain'] 
            if rain <= config.AUTO_MIN_RAIN:
                rain = 0

            duration = (config.AUTO_SECONDS_PER_DEGREE * w['temp_max'])
            duration -= config.AUTO_SECONDS_PER_MM_RAIN * rain

            if duration > 0:
                duration = max(duration, config.AUTO_MIN_SECONDS)
                duration = min(duration, config.AUTO_MAX_SECONDS)

        db.save_data(
            'auto',
            duration=duration,
            datestamp=util.timestamp()
        )
    print(duration)

    if duration > 0:
        dev = devices.get(pump)

        if isinstance(dev, device.Relay):
            pass
            dev.pump_on(seconds=duration)
    return {'status': 'ok'}



COMMANDS = {
    'status': status,
    'pump': pump,
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((config.HOST, config.PORT))
    s.listen()
    running = True
    while running:
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                data = json.loads(data)
                command = COMMANDS[data.get('command', 'status')]
                print(data)
                try:
                    out = command(data.get('data', {}))
                except Exception as e:
                    type, value, exc_traceback = sys.exc_info()
                    print('@@', value)
                    out = {
                        'status': 'error',
                        'error_message': str(e),
                        'error_type': type.__name__,
                        'error_traceback': traceback.format_tb(exc_traceback)
                        }
                out['message_time'] = util.timestamp()
                print(out)
                r = json.dumps(out)
                conn.sendall(r.encode())
                #running = False
