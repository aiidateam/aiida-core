#!/usr/bin/env python
from aida.common.utils import load_django
load_django()

from aida.execmanager import *

from aida.common import aidalogger
import logging
aidalogger.setLevel(logging.INFO)

update_jobs()
#retrieve_jobs()


