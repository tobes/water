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
devices['sensor 1'] = device.Meter(id=1, gpio_trigger=23, gpio_echo=24)
devices['pump 1'] = device.Relay(gpio=18)
devices['weather'] = device.Weather()


def status(data):
    fast = data.get('fast')
    out = {}
    for name, device in devices.items():
        out[name] = device.status(fast=fast)
    return out


def pump(data):
    duration = data.get('duration', 0)
    auto = data.get('auto')
    pump = data.get('pump')

    if not pump:
        return {'status': 'fail'}

    if duration > 0:
        dev = devices.get(pump)

        if isinstance(dev, device.Relay):
            pass
            dev.pump_on(seconds=duration)
    return {'status': 'ok'}


# start any device auto methods
for device in devices.values():
    if hasattr(device, 'auto'):
        device.auto()

COMMANDS = {
    'status': status,
    'pump': pump,
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((config.HOST, config.PORT))
    s.listen()
    running = True
    while running:
        try:
            conn, addr = s.accept()
        except KeyboardInterrupt:
            sys.exit()
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
                    out = command(data)
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
                out['epoch_time'] = int(time.time())
              #  print(out)
                r = json.dumps(out)
                conn.sendall(r.encode())
                #running = False
