# -*- coding: utf-8 -*-

import uuid

# TODO SP: put this outside of Django
from aiida.settings import AIIDANODES_UUID_VERSION

uuid_func = getattr(uuid, "uuid" + str(AIIDANODES_UUID_VERSION))
