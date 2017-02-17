

from aiida.orm.backend import Backend
from aiida.orm.implementation.django.log import DjangoLog


class DjangoBackend(Backend):
    def __init__(self):
        self._log = DjangoLog()

    @property
    def log(self):
        return self._log
