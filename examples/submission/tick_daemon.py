# -*- coding: utf-8 -*-
"""
This is a test to call all the functions that the daemon would call.  This can
be used to test daemon functions using a debugger for example.
"""

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.daemon.tasks import manual_tick_all

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


manual_tick_all()
