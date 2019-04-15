# -*- coding: utf-8 -*-

import uuid

from aiida.backends.settings import AIIDANODES_UUID_VERSION

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

uuid_func = getattr(uuid, "uuid" + str(AIIDANODES_UUID_VERSION))
