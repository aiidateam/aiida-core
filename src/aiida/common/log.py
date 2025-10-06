###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all logging methods/classes that don't need the ORM."""

from __future__ import annotations

import collections.abc
import contextlib
import enum
import io
import logging
import types
import typing as t

from aiida.common.typing import FilePath

__all__ = ('AIIDA_LOGGER', 'override_log_level')

# Custom logging level, intended specifically for informative log messages reported during WorkChains.
# We want the level between INFO(20) and WARNING(30) such that it will be logged for the default loglevel, however
# the value 25 is already reserved for SUBWARNING by the multiprocessing module.
LOG_LEVEL_REPORT = 23

# Add the custom log level to the :mod:`logging` module and add a corresponding report logging method.
logging.addLevelName(LOG_LEVEL_REPORT, 'REPORT')


def report(self: logging.Logger, msg, *args, **kwargs):
    """Log a message at the ``REPORT`` level."""
    self.log(LOG_LEVEL_REPORT, msg, *args, **kwargs)


class AiidaLoggerType(logging.Logger):
    def report(self, msg: str, *args, **kwargs) -> None:
        """Log a message at the ``REPORT`` level."""


setattr(logging, 'REPORT', LOG_LEVEL_REPORT)
setattr(logging.Logger, 'report', report)
setattr(logging.LoggerAdapter, 'report', report)

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

LogLevels = enum.Enum('LogLevels', {key: key for key in LOG_LEVELS})  # type: ignore[misc]

AIIDA_LOGGER = t.cast(AiidaLoggerType, logging.getLogger('aiida'))

CLI_ACTIVE: bool | None = None
"""Flag that is set to ``True`` if the module is imported by ``verdi`` being called."""

CLI_LOG_LEVEL: str | None = None
"""Set if ``verdi`` is called with ``--verbosity`` flag specified, and is set to corresponding log level."""


# The default logging dictionary for AiiDA that can be used in conjunction
# with the config.dictConfig method of python's logging module
def get_logging_config() -> dict[str, t.Any]:
    from aiida.manage.configuration import get_config_option

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d ' '%(thread)d %(message)s',
            },
            'halfverbose': {
                'format': '%(asctime)s <%(process)d> %(name)s: [%(levelname)s] %(message)s',
                'datefmt': '%m/%d/%Y %I:%M:%S %p',
            },
            'cli': {'class': 'aiida.cmdline.utils.log.CliFormatter'},
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'halfverbose',
            },
            'cli': {'class': 'aiida.cmdline.utils.log.CliHandler', 'formatter': 'cli'},
        },
        'loggers': {
            'aiida': {
                'handlers': ['console'],
                'level': lambda: get_config_option('logging.aiida_loglevel'),
                'propagate': True,
            },
            'verdi': {
                'handlers': ['cli'],
                'level': lambda: get_config_option('logging.verdi_loglevel'),
                'propagate': False,
            },
            'disk_objectstore': {
                'handlers': ['console'],
                'level': lambda: get_config_option('logging.disk_objectstore_loglevel'),
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
            'aio_pika': {
                'handlers': ['console'],
                'level': lambda: get_config_option('logging.aiopika_loglevel'),
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


def evaluate_logging_configuration(dictionary: collections.abc.Mapping) -> dict:
    """Recursively evaluate the logging configuration, calling lambdas when encountered.

    This allows the configuration options that are dependent on the active profile to be loaded lazily.

    :return: evaluated logging configuration dictionary
    """
    result = {}

    for key, value in dictionary.items():
        if isinstance(value, collections.abc.Mapping):
            result[key] = evaluate_logging_configuration(value)
        elif isinstance(value, types.LambdaType):
            result[key] = value()
        else:
            result[key] = value

    return result


def configure_logging(with_orm: bool = False, daemon: bool = False, daemon_log_file: FilePath | None = None) -> None:
    """Setup the logging by retrieving the LOGGING dictionary from aiida and passing it to
    the python module logging.config.dictConfig. If the logging needs to be setup for the
    daemon, set the argument 'daemon' to True and specify the path to the log file. This
    will cause a 'daemon_handler' to be added to all the configured loggers, that is a
    RotatingFileHandler that writes to the log file.

    :param with_orm: configure logging to the backend storage.
        We don't configure this by default, since it would load the modules that slow the CLI
    :param daemon: configure the logging for a daemon task by adding a file handler instead
        of the default 'console' StreamHandler
    :param daemon_log_file: absolute filepath of the log file for the RotatingFileHandler
    """
    from logging.config import dictConfig

    # Evaluate the `LOGGING` configuration to resolve the lambdas that will retrieve the correct values based on the
    # currently configured profile.
    config = evaluate_logging_configuration(get_logging_config())
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
            'maxBytes': 10000000,  # 10 MB
            'backupCount': 10,
        }

        for logger in config.get('loggers', {}).values():
            logger.setdefault('handlers', []).append(daemon_handler_name)
            try:
                # Remove the `console` stdout stream handler to prevent messages being duplicated in the daemon log file
                logger['handlers'].remove('console')
            except ValueError:
                pass

    # If the ``CLI_ACTIVE`` is set, a ``verdi`` command is being executed, so we replace the ``console`` handler with
    # the ``cli`` one for all loggers.
    if CLI_ACTIVE is True and not daemon:
        for logger in config['loggers'].values():
            handlers = logger['handlers']
            if 'console' in handlers:
                handlers.remove('console')
            handlers.append('cli')

    # If ``CLI_LOG_LEVEL`` is set, a ``verdi`` command is being executed with the ``--verbosity`` option. In this case
    # we override the log levels of the ``aiida`` and ``verdi`` loggers with the specified log level. The other loggers
    # are left untouched as they can become very noisy for lower log levels and drown out the useful information. Users
    # can still configure those manually beforehand through the config options.
    if CLI_LOG_LEVEL is not None:
        for name, logger in config['loggers'].items():
            if name in ['aiida', 'verdi', 'disk_objectstore']:
                logger['level'] = CLI_LOG_LEVEL

    # Add the `DbLogHandler` if `with_orm` is `True`
    if with_orm:
        from aiida.manage.configuration import get_config_option

        config['handlers']['db_logger'] = {
            'level': get_config_option('logging.db_loglevel'),
            'class': 'aiida.orm.utils.log.DBLogHandler',
        }
        config['loggers']['aiida']['handlers'].append('db_logger')

    dictConfig(config)


@contextlib.contextmanager
def override_log_level(level=logging.CRITICAL):
    """Temporarily adjust the log-level of logger."""
    logging.disable(level=level)
    try:
        yield
    finally:
        logging.disable(level=logging.NOTSET)


@contextlib.contextmanager
def capture_logging(logger: logging.Logger = AIIDA_LOGGER) -> t.Generator[io.StringIO, None, None]:
    """Capture logging to a stream in memory.

    Note, this only copies any content that is being logged to a stream in memory. It does not interfere with any other
    existing stream handlers. In this sense, this context manager is non-destructive.

    :param logger: The logger whose output to capture.
    :returns: A stream to which the logged content is captured.
    """
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)
