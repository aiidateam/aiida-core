# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all logging methods/classes that don't need the ORM."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import collections
import logging
import types

from aiida.manage.configuration import get_config_option

__all__ = ('AIIDA_LOGGER',)

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
    },
    'loggers': {
        'aiida': {
            'handlers': ['console'],
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
        elif isinstance(value, types.LambdaType):  # pylint: disable=no-member
            result[key] = value()
        else:
            result[key] = value

    return result


def configure_logging(with_orm=False, daemon=False, daemon_log_file=None):
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

        # Daemon always needs to run with ORM enabled
        with_orm = True

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

    # Add the `DbLogHandler` if `with_orm` is `True`
    if with_orm:

        handler_dblogger = 'dblogger'

        config['handlers'][handler_dblogger] = {
            'level': get_config_option('logging.db_loglevel'),
            'class': 'aiida.orm.utils.log.DBLogHandler',
        }
        config['loggers']['aiida']['handlers'].append(handler_dblogger)

    dictConfig(config)
