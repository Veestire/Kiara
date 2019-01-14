import os


class Config:
    def __init__(self):
        self._data = {}

    def __getattr__(self, name):
        name = name.upper()
        if name not in self._data:
            try:
                self._data[name] = int(os.getenv(name))
            except ValueError:
                self._data[name] = os.getenv(name)
        return self._data[name]
