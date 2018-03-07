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
from copy import deepcopy
from logging import config
from aiida.common import setup
from aiida.backends.utils import is_dbenv_loaded

# Custom logging level, intended specifically for informative log messages
# reported during WorkChains and Workflows. We want the level between INFO(20)
# and WARNING(30) such that it will be logged for the default loglevel, however
# the value 25 is already reserved for SUBWARNING by the multiprocessing module.
LOG_LEVEL_REPORT = 23
logging.addLevelName(LOG_LEVEL_REPORT, 'REPORT')


# Convenience dictionary of available log level names and their log level integer
LOG_LEVELS = {
    logging.getLevelName(logging.DEBUG): logging.DEBUG,
    logging.getLevelName(logging.INFO): logging.INFO,
    logging.getLevelName(LOG_LEVEL_REPORT): LOG_LEVEL_REPORT,
    logging.getLevelName(logging.WARNING): logging.WARNING,
    logging.getLevelName(logging.ERROR): logging.ERROR,
    logging.getLevelName(logging.CRITICAL): logging.CRITICAL,
}


# The AiiDA logger
aiidalogger = logging.getLogger('aiida')


# A logging filter that can be used to disable logging
class NotInTestingFilter(logging.Filter):

    def filter(self, record):
        from aiida import settings
        return not settings.TESTING_MODE


# A logging handler that will store the log record in the database DbLog table
class DBLogHandler(logging.Handler):

    def emit(self, record):
        # If this is reached before a backend is defined, simply pass
        if not is_dbenv_loaded():
            return

        from aiida.orm.backend import construct
        from django.core.exceptions import ImproperlyConfigured

        try:
            backend = construct()
            backend.log.create_entry_from_record(record)

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


# The default logging dictionary for AiiDA that can be used in conjunction
# with the config.dictConfig method of python's logging module
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s',
        },
        'halfverbose': {
            'format': '%(asctime)s, %(name)s: [%(levelname)s] %(message)s',
            'datefmt': '%m/%d/%Y %I:%M:%S %p',
        },
    },
    'filters': {
        'testing': {
            '()': NotInTestingFilter
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'halfverbose',
            'filters': ['testing']
        },
        'dblogger': {
            # setup.get_property takes the property from the config json file
            # The key used in the json, and the default value, are
            # specified in the _property_table inside aiida.common.setup
            # NOTE: To modify properties, use the 'verdi devel setproperty'
            #   command and similar ones (getproperty, describeproperties, ...)
            'level': setup.get_property('logging.db_loglevel'),
            'class': 'aiida.common.log.DBLogHandler',
        },
    },
    'loggers': {
        'aiida': {
            'handlers': ['console', 'dblogger'],
            'level': setup.get_property('logging.aiida_loglevel'),
            'propagate': False,
        },
        'paramiko': {
            'handlers': ['console'],
            'level': setup.get_property('logging.paramiko_loglevel'),
            'propagate': False,
        },
        'alembic': {
            'handlers': ['console'],
            'level': setup.get_property('logging.alembic_loglevel'),
            'propagate': False,
        },
        'sqlalchemy': {
            'handlers': ['console'],
            'level': setup.get_property('logging.sqlalchemy_loglevel'),
            'propagate': False,
            'qualname': 'sqlalchemy.engine',
        },
    },
}

def configure_logging(daemon=False, daemon_log_file=None):
    """
    Setup the logging by retrieving the LOGGING dictionary from aiida and passing it to
    the python module logging.config.dictConfig. If the logging needs to be setup for the
    daemon running a task for one of the celery workers, set the argument 'daemon' to True
    and specify the path to the log file. This will cause a 'daemon_handler' to be added
    to all the configured loggers, that is a RotatingFileHandler that writes to the log file.

    :param daemon: configure the logging for a daemon task by adding a file handler instead
        of the default 'console' StreamHandler
    :param daemon_log_file: absolute filepath of the log file for the RotatingFileHandler
    """
    config = deepcopy(LOGGING)
    daemon_handler_name = 'daemon_log_file'

    # Add the daemon file handler to all loggers if daemon=True
    if daemon is True:

        if daemon_log_file is None:
            raise ValueError('daemon_log_file has to be defined when configuring for the daemon')

        config.setdefault('handlers', {})
        config['handlers'][daemon_handler_name] = {
            'level': 'DEBUG',
            'formatter': 'halfverbose',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': daemon_log_file,
            'encoding': 'utf8',
            'maxBytes': 100000,
        }

        for name, logger in config.get('loggers', {}).iteritems():
            logger.setdefault('handlers', []).append(daemon_handler_name)

    logging.config.dictConfig(config)


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