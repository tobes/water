import json
import os
import statistics
import time
import threading

from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    import pigpio
except ModuleNotFoundError:
    print('pigpio not found!')
    pigpio = None

import db
import config
import util
import weather



if pigpio:
    # start pigpio service
    try:
        f = open('/var/run/pigpio.pid')
        f.close()
    except IOError:
        os.system('sudo pigpiod')
        print('starting pigpio')
        time.sleep(1)
        print('pigpio started')

    p = pigpio.pi()
else:
    # allow running without pigpio for development reasons
    class Null:
        def __getattr__(self, attr):
            def fn(*args, **kw):
                pass
            return fn

    p = Null()
    pigpio = Null()


class Device:
    pass


class Butt:
    def __init__(self):
        self.max_distance = 875
        self.total_volume = 200
        self.min_distance = 105

    def calculate_stats(self, distance):
        depth = self.max_distance - distance
        volume = (depth / (self.max_distance - self.min_distance)) * self.total_volume
        return {
            'depth': depth,
            'volume': round(volume, 1),
        }


class Weather:

    def __init__(self):
        self.thread = None
        self.update_time = None
        self.state = None
        self.day_summary = {}
        self.get_weather()

        self.day_summary = db.update_recent_weather()[-1]

    def get_weather(self, save=False):
        query_data = {
            'lat': config.LAT,
            'lon': config.LON,
            'appid': config.WEATHER_API_KEY,
            'units': 'metric',
        }

        query_string = urlencode(query_data)
        try:
            content = urlopen(config.WEATHER_API_URL + query_string).read().decode('utf-8')

            self.state = json.loads(content)
            self.update_time = util.timestamp()
            if save:
                db.save_data(
                    'weather',
                    json=content,
                    datestamp=util.timestamp()
                )
                # update summary table
                updates = db.update_recent_weather()
                self.day_summary = updates[-1]
            #print(content)
        except Exception as e:
            print('ERROR:',e)

    def auto(self, save=False):
        self.get_weather()
        kwargs = dict(save=True)
        util.thread_runner(self.auto, interval=config.WEATHER_INTERVAL, kwargs=kwargs)

    def status(self):
        out = {
            'state': self.state,
            'day_summary': self.day_summary,
            'update_time': self.update_time,
        }
        return out


class Relay:

    def __init__(self, gpio):
        self.gpio = gpio
        self.thread = None
        self.state = 'OFF'
        self.pump_seconds=0
        self.off_time = 0
        self.update_time = None
        p.set_mode(gpio, pigpio.OUTPUT)
        p.write(gpio, 1)

    def pump_off(self):
        if self.thread:
            self.thread.cancel()
        p.write(self.gpio, 1)
        print('pump off')
        self.state = 'OFF'
        self.update_time = util.timestamp()

        db.save_data(
            'pumps',
            pump=1,
            datestamp=self.update_time,
            action='OFF',
            duration=self.pump_seconds,
        )
        self.pump_seconds=0

    def pump_on(self, seconds):
        p.write(self.gpio, 0)
        print('pump on')
        self.state = 'ON'
        self.update_time = util.timestamp()
        self.off_time = time.time() + seconds
        self.thread = threading.Timer(seconds, self.pump_off)
        self.thread.start()
        self.pump_seconds=seconds

        db.save_data(
            'pumps',
            pump=1,
            datestamp=self.update_time,
            action='ON',
            duration=seconds,
        )

    def status(self):
        out = {
            'state': self.state,
            'update_time': self.update_time,
        }
        now = time.time()
        if now > self.off_time:
            remaining = 0
        else:
            remaining = int(self.off_time - now)
        out['remaining'] = remaining
        return out

    def auto(self, action=False):
        w = weather.get_last_period()
        # if we have no weather info don't process
        if  action and w['temp_max'] is not None:
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

        now = datetime.now()
        wanted = now.replace(
                hour=config.AUTO_HOUR,
                minute=config.AUTO_MINUTE,
                second=0,
                microsecond=0
        )
        if wanted < now:
            wanted += timedelta(days=1)
        delay = (wanted - now).total_seconds()
        util.thread_runner(self.auto, seconds=delay, kwargs={'action': True})

class Meter:

    def __init__(self, gpio_trigger, gpio_echo, butt, **kw):
        self.gpio_trigger = gpio_trigger
        self.gpio_echo = gpio_echo
        self.butt = Butt()
        self.pulse_start = 0
        self.pulse_end = 0
        self.distance = 0
        self.accuracy = 0
        self.update_time = None
        self.ticks = []
        self.save=False
        self.thread = None

        p.set_mode(gpio_trigger, pigpio.OUTPUT)
        p.write(gpio_trigger, 0)
        p.set_mode(gpio_echo, pigpio.INPUT)
        p.set_pull_up_down(gpio_echo, pigpio.PUD_DOWN)

        def cbf_pulse_length(gpio, level, tick):
            if level:
                self.pulse_start = tick
            else:
                pulse_end = tick
                self.ticks.append(pigpio.tickDiff(self.pulse_start, pulse_end))
                if len(self.ticks) < config.METER_TICKS:
                    time.sleep(config.METER_REPEAT_DELAY)
                    p.gpio_trigger(self.gpio_trigger, 10, 1)
                else:
                    cut = (config.METER_TICKS - 1) // 2

                    ticks = sorted(self.ticks)[cut:-cut]
                    self.distance = int(sum(ticks) / len(ticks) * 0.1715)
                    self.distance2 = int(statistics.geometric_mean(self.ticks) * 0.1715)
                    self.accuracy = round(statistics.pstdev(self.ticks), 2)
                    self.update_time = util.timestamp()
                    if self.save:
                        db.save_data(
                            'levels',
                            sensor=1,
                            datestamp=self.update_time,
                            level=self.distance,
                            level2=self.distance2,
                            accuracy=self.accuracy,
                        )

                    if self.thread == None:
                        seconds = (config.LEVEL_INTERVAL - (time.time() % config.LEVEL_INTERVAL))
                        if seconds < 1:
                            seconds += config.LEVEL_INTERVAL
                        self.thread = threading.Timer(seconds, self.get_distance, kwargs=dict(save=True))
                        self.thread.start()

        p.callback(gpio_echo, pigpio.EITHER_EDGE, cbf_pulse_length)

        self.get_distance()

    def get_distance(self, save=False):
        if self.thread:
            self.thread.cancel()
            self.thread = None
        self.ticks = []
        self.save = save
        p.gpio_trigger(self.gpio_trigger, 10, 1)

    def status(self):
        self.get_distance()
        butt_data = self.butt.calculate_stats(self.distance2)
        return {
            'depth': butt_data['depth'],
            'volume': butt_data['volume'],
            'distance': self.distance2,
            'accuracy': self.accuracy,
            'update_time': self.update_time,
        }
