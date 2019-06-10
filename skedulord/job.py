class Job:
    def __init__(self):
        pass

    def pipe(self, func, **kwargs):
        func(**kwargs)
        return self
