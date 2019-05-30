import time, random


def delay(func):
    def wrapper(*args, **kwargs):
        secs = random.uniform(0.0, 0.2)
        print('.', end='')
        time.sleep(secs)
        return func(*args, **kwargs)
    return wrapper