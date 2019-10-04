import time


class Job:
    def __init__(self):
        pass

    def then(self, func, *args, **kwargs):
        func(*args, **kwargs)
        return self

    def wait(self, seconds):
        time.sleep(seconds)
