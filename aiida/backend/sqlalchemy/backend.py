from aiida.backend.backend import Backend
from aiida.backend.sqlalchemy.log import SqlaLog


class SqlaBackend(Backend):
    def __init__(self):
        self._log = SqlaLog()

    @property
    def log(self):
        return self._log
