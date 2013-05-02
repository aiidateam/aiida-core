#!/usr/bin/env python
from aida.common.utils import load_django
load_django()

from aida.execmanager import daemon

from aida.common import aidalogger
import logging
aidalogger.setLevel(logging.DEBUG)

daemon()


