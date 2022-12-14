from pathlib import Path

HOST = ''
PORT = 50007

SQLITE_DB = 'water.db'

LEVEL_INTERVAL = 5 * 60
METER_TICKS = 15
METER_REPEAT_DELAY = 0.1
METER_CHECK_INTERVAL = 5

LAT = 51.578066
LON = -0.100738
WEATHER_INTERVAL =  60 * 60
WEATHER_CHECK_INTERVAL =  60 * 5

WEATHER_API_KEY = Path('weather_api_key.secret').read_text().strip()
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather?'


AUTO_MIN_TEMP_MIN = 2  # Minumum temperature must have been at least this
AUTO_MIN_TEMP_MAX = 10  # Maxumum temperature Must have been at least this

AUTO_SECONDS_PER_DEGREE = 12  # number of seconds pump on per degree over AUTO_MIN_TEMP_MAX
AUTO_MIN_SECONDS = 20  # minimum pump time
AUTO_MAX_SECONDS = 300  # maximum pump time

AUTO_MIN_RAIN = 2.0  # Ignore rain less than this
AUTO_SECONDS_PER_MM_RAIN = 15  # reduce pump time per mm of rain over AUTO_MIN_RAIN

AUTO_IGNORED_WATER_PER_DAY = 3 # ignore this much water per day since rain


AUTO_HOUR = 19
AUTO_MINUTE = 5

STATS_MAX_DAYS = 90
