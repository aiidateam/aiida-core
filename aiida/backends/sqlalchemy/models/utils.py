# -*- coding: utf-8 -*-

import uuid

from aiida.backends.settings import AIIDANODES_UUID_VERSION

uuid_func = getattr(uuid, "uuid" + str(AIIDANODES_UUID_VERSION))
