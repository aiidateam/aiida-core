# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import logging
from aiida import LOG_LEVEL_REPORT
from aiida.backends.utils import is_dbenv_loaded

LOG_LEVELS = {
    logging.getLevelName(logging.DEBUG): logging.DEBUG,
    logging.getLevelName(logging.INFO): logging.INFO,
    logging.getLevelName(LOG_LEVEL_REPORT): LOG_LEVEL_REPORT,
    logging.getLevelName(logging.WARNING): logging.WARNING,
    logging.getLevelName(logging.ERROR): logging.ERROR,
    logging.getLevelName(logging.CRITICAL): logging.CRITICAL,
}


def get_dblogger_extra(obj):
    """
    Given an object (Node, Calculation, ...) return a dictionary to be passed
    as extra to the aiidalogger in order to store the exception also in the DB.
    If no such extra is passed, the exception is only logged on file.
    """
    from aiida.orm import Node

    if isinstance(obj, Node):
        if obj._plugin_type_string:
            objname = "node." + obj._plugin_type_string
        else:
            objname = "node"
    else:
        objname = obj.__class__.__module__ + "." + obj.__class__.__name__
    objpk = obj.pk
    return {'objpk': objpk, 'objname': objname}


class DBLogHandler(logging.Handler):
    def emit(self, record):
        # If this is reached before a backend is defined, simply pass
        if not is_dbenv_loaded():
            return

        from aiida.orm.backend import construct
        from django.core.exceptions import ImproperlyConfigured

        try:
            backend   = construct()
            log_entry = backend.log.create_entry_from_record(record)

        except ImproperlyConfigured:
            # Probably, the logger was called without the
            # Django settings module loaded. Then,
            # This ignore should be a no-op.
            pass
        except Exception:
            # To avoid loops with the error handler, I just print.
            # Hopefully, though, this should not happen!
            import traceback

            traceback.print_exc()