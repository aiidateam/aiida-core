# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all common logging methods/classes"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import collections
import logging
import types

from aiida.manage import get_config_option

# Custom logging level, intended specifically for informative log messages reported during WorkChains.
# We want the level between INFO(20) and WARNING(30) such that it will be logged for the default loglevel, however
# the value 25 is already reserved for SUBWARNING by the multiprocessing module.
LOG_LEVEL_REPORT = 23
logging.addLevelName(LOG_LEVEL_REPORT, 'REPORT')

# Convenience dictionary of available log level names and their log level integer
LOG_LEVELS = {
    logging.getLevelName(logging.NOTSET): logging.NOTSET,
    logging.getLevelName(logging.DEBUG): logging.DEBUG,
    logging.getLevelName(logging.INFO): logging.INFO,
    logging.getLevelName(LOG_LEVEL_REPORT): LOG_LEVEL_REPORT,
    logging.getLevelName(logging.WARNING): logging.WARNING,
    logging.getLevelName(logging.ERROR): logging.ERROR,
    logging.getLevelName(logging.CRITICAL): logging.CRITICAL,
}

# The AiiDA logger
AIIDA_LOGGER = logging.getLogger('aiida')


# A logging filter that can be used to disable logging
class NotInTestingFilter(logging.Filter):

    def filter(self, record):
        from aiida import settings
        return not settings.TESTING_MODE


class DBLogHandler(logging.Handler):
    """A custom db log handler for writing logs tot he database"""

    def emit(self, record):
        # If this is reached before a backend is defined, simply pass
        from aiida.backends.utils import is_dbenv_loaded
        if not is_dbenv_loaded():
            return

        if not hasattr(record, 'objpk'):
            # Only log records with an object id
            return

        if record.exc_info:
            # We do this because if there is exc_info this will put an appropriate string in exc_text.
            # See:
            # https://github.com/python/cpython/blob/1c2cb516e49ceb56f76e90645e67e8df4e5df01a/Lib/logging/handlers.py#L590
            self.format(record)

        from aiida import orm
        from django.core.exceptions import ImproperlyConfigured  # pylint: disable=no-name-in-module, import-error

        try:
            backend = record.backend
            delattr(record, 'backend')  # We've consumed the backend, don't want it to get logged
            orm.Log.objects(backend).create_entry_from_record(record)

        except ImproperlyConfigured:
            # Probably, the logger was called without the
            # Django settings module loaded. Then,
            # This ignore should be a no-op.
            pass
        except Exception:  # pylint: disable=broad-except
            # To avoid loops with the error handler, I just print.
            # Hopefully, though, this should not happen!
            import traceback
            traceback.print_exc()
            raise


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
            'format': '%(asctime)s <%(process)d> %(name)s: [%(levelname)s] %(message)s',
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
            'level': lambda: get_config_option('logging.db_loglevel'),
            'class': 'aiida.common.log.DBLogHandler',
        },
    },
    'loggers': {
        'aiida': {
            'handlers': ['console', 'dblogger'],
            'level': lambda: get_config_option('logging.aiida_loglevel'),
            'propagate': False,
        },
        'tornado': {
            'handlers': ['console'],
            'level': lambda: get_config_option('logging.tornado_loglevel'),
            'propagate': False,
        },
        'plumpy': {
            'handlers': ['console'],
            'level': lambda: get_config_option('logging.plumpy_loglevel'),
            'propagate': False,
        },
        'kiwipy': {
            'handlers': ['console'],
            'level': lambda: get_config_option('logging.kiwipy_loglevel'),
            'propagate': False,
        },
        'paramiko': {
            'handlers': ['console'],
            'level': lambda: get_config_option('logging.paramiko_loglevel'),
            'propagate': False,
        },
        'alembic': {
            'handlers': ['console'],
            'level': lambda: get_config_option('logging.alembic_loglevel'),
            'propagate': False,
        },
        'sqlalchemy': {
            'handlers': ['console'],
            'level': lambda: get_config_option('logging.sqlalchemy_loglevel'),
            'propagate': False,
            'qualname': 'sqlalchemy.engine',
        },
        'py.warnings': {
            'handlers': ['console'],
        },
    },
}


def evaluate_logging_configuration(dictionary):
    """Recursively evaluate the logging configuration, calling lambdas when encountered.

    This allows the configuration options that are dependent on the active profile to be loaded lazily.

    :return: evaluated logging configuration dictionary
    """
    result = {}

    for key, value in dictionary.items():
        if isinstance(value, collections.Mapping):
            result[key] = evaluate_logging_configuration(value)
        elif isinstance(value, types.LambdaType):
            result[key] = value()
        else:
            result[key] = value

    return result


def configure_logging(daemon=False, daemon_log_file=None):
    """
    Setup the logging by retrieving the LOGGING dictionary from aiida and passing it to
    the python module logging.config.dictConfig. If the logging needs to be setup for the
    daemon, set the argument 'daemon' to True and specify the path to the log file. This
    will cause a 'daemon_handler' to be added to all the configured loggers, that is a
    RotatingFileHandler that writes to the log file.

    :param daemon: configure the logging for a daemon task by adding a file handler instead
        of the default 'console' StreamHandler
    :param daemon_log_file: absolute filepath of the log file for the RotatingFileHandler
    """
    from logging.config import dictConfig

    config = evaluate_logging_configuration(LOGGING)
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

        for logger in config.get('loggers', {}).values():
            logger.setdefault('handlers', []).append(daemon_handler_name)

    dictConfig(config)


def get_dblogger_extra(obj):
    """
    Given an object (Node, Calculation, ...) return a dictionary to be passed
    as extra to the aiidalogger in order to store the exception also in the DB.
    If no such extra is passed, the exception is only logged on file.
    """
    from aiida.orm import Node

    if isinstance(obj, Node):
        if obj._plugin_type_string:  # pylint: disable=protected-access
            objname = "node." + obj._plugin_type_string  # pylint: disable=protected-access
        else:
            objname = "node"
    else:
        objname = obj.__class__.__module__ + "." + obj.__class__.__name__
    objpk = obj.pk
    return {'objpk': objpk, 'objname': objname, 'backend': obj.backend}


def create_logger_adapter(logger, entity):
    """
    Create a logger adapter for a particular AiiDA entity

    :param logger: the logger to adapt
    :param entity: the entity to create the adapter for
    :return: the logger adapter
    :rtype: :class:`logging.LoggerAdapter`
    """
    extra = get_dblogger_extra(entity)
    # Further augment with the backend so the logger handler knows which backend to log to
    extra['backend'] = entity.backend
    return logging.LoggerAdapter(logger=logger, extra=extra)
