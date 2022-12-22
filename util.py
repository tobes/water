import threading
import time

from datetime import datetime, timedelta


def timestamp(**td):
    """
    return datetime in ISO format without microseconds

    **td can give a timedelta offset  eg days=1

    """
    td = timedelta(**td)
    return (datetime.now() + td).replace(microsecond=0).isoformat(sep=' ')

def timestamp_zeroed(**td):
    """
    return datetime in ISO format without microseconds.
    always at 00:00:00

    **td can give a timedelta offset  eg days=1

    """
    td = timedelta(**td)
    replace = {
        'hour': 0,
        'minute': 0,
        'second': 0,
        'microsecond': 0,
    }
    return (datetime.now() + td).replace(**replace).isoformat(sep=' ')



def timestamp_clean(timestamp=None, period=1, **td):
    """
    return datetime in ISO format without microseconds.
    always at 00:00:00

    **td can give a timedelta offset  eg days=1

    """
    if timestamp is None:
        timestamp = datetime.now()
    td = timedelta(**td)
    timestamp += td
    replace = {
        'second': 0,
        'microsecond': 0,
    }
    replace['minute'] = int(period * int(float(timestamp.minute)/period))
    timestamp = timestamp.replace(**replace)
    return timestamp.isoformat(sep=' ')



def thread_runner(function, interval=None, seconds=None, kwargs=None):
    """ spawn a thread to run function at interval """
    if interval:
        seconds = (interval - (time.time() % interval))
        if seconds < 1:
            seconds += interval
    thread = threading.Timer(seconds, function, kwargs=kwargs)
    thread.start()
    return thread
