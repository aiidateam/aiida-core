from aiida.backend.backend import Backend
from aiida.backend.django.log import DjangoLog


class DjangoBackend(Backend):
    def __init__(self):
        self._log = DjangoLog()

    @property
    def log(self):
        return self._log
