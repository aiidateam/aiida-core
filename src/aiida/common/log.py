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


def report(self: logging.Logger, msg: str, *args: t.Any, **kwargs: t.Any) -> None:
    """Log a message at the ``REPORT`` level."""
    self.log(LOG_LEVEL_REPORT, msg, *args, **kwargs)


class AiidaLoggerType(logging.Logger):
    def report(self, msg: str, *args: t.Any, **kwargs: t.Any) -> None:
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


class LogLevels(str, enum.Enum):
    """Supported log levels."""

    NOTSET = 'NOTSET'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    REPORT = 'REPORT'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class AdvancedLogLevels(str, enum.Enum):
    """Supported log levels for advanced logger-specific configuration options."""

    NOTSET = 'NOTSET'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    REPORT = 'REPORT'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    INHERIT = 'INHERIT'


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
                'level': lambda: get_config_option('logging.terminal_handler'),
            },
            'cli': {
                'class': 'aiida.cmdline.utils.log.CliHandler',
                'formatter': 'cli',
                'level': lambda: get_config_option('logging.terminal_handler'),
            },
        },
        'loggers': {
            'aiida': {
                'handlers': ['console'],
                'level': lambda: get_config_option('logging.aiida_core_loglevel'),
                'propagate': False,
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


# Maps each handler-side filter option to the logger-level ``*_loglevel`` options whose messages it filters.
_HANDLER_TO_LOGGER: dict[str, tuple[str, ...]] = {
    'logging.terminal_handler': (
        'logging.aiida_loglevel',
        'logging.verdi_loglevel',
        'logging.aiida_core_loglevel',
        'logging.disk_objectstore_loglevel',
        'logging.plumpy_loglevel',
        'logging.kiwipy_loglevel',
        'logging.paramiko_loglevel',
        'logging.alembic_loglevel',
        'logging.aiopika_loglevel',
        'logging.sqlalchemy_loglevel',
    ),
    'logging.database_handler': ('logging.aiida_core_loglevel',),
}


def validate_handler(config: t.Any, option_name: str, scope: str | None = None) -> str | None:
    """Validate that a handler-side filter can take effect given the configured logger levels.

    ``logging.terminal_handler`` and ``logging.database_handler`` filter messages at the output handler, so they can
    only surface messages that a logger actually emits (a record must clear both its logger's level and the handler's
    level). If the handler level is set more verbose (i.e. a lower level) than every relevant logger level
    (``*_loglevel``), no additional messages reach the handler and the setting has no effect until a logger level is
    lowered as well.

    :param config: the loaded configuration, queried through ``config.get_option(name, scope=scope)``.
    :param option_name: name of the option to validate (dotted form, e.g. ``logging.terminal_handler``). Names that
        are not a handler filter are ignored.
    :param scope: the profile name to query the levels for, or ``None`` for the global scope. Must match the scope the
        option was set for, so the check reflects the values that were actually written.
    :returns: a warning message if the handler filter cannot take effect, or ``None`` if it is fine (or not a handler
        option).
    """
    logger_level_options = _HANDLER_TO_LOGGER.get(option_name)
    if logger_level_options is None:
        return None

    log_level = LogLevels(t.cast(str, config.get_option(option_name, scope=scope)))
    fallback_level = LogLevels(t.cast(str, config.get_option('logging.aiida_loglevel', scope=scope)))

    def resolve_level(name: str) -> LogLevels:
        level = AdvancedLogLevels(t.cast(str, config.get_option(name, scope=scope)))
        if level is AdvancedLogLevels.INHERIT:
            return fallback_level
        return LogLevels(level.value)

    # The most verbose logger is the one with the lowest numeric level.
    most_verbose_logger = min(logger_level_options, key=lambda name: LOG_LEVELS[resolve_level(name).value])
    most_verbose_level = resolve_level(most_verbose_logger)

    if LOG_LEVELS[log_level.value] < LOG_LEVELS[most_verbose_level.value]:
        return (
            f'`{option_name}` is set to `{log_level.value}` but no logger emits messages at that level: '
            f'the most verbose logger level is `{most_verbose_logger}` (`{most_verbose_level.value}`). '
        )

    return None


def evaluate_logging_configuration(dictionary: collections.abc.Mapping[t.Any, t.Any]) -> dict[t.Any, t.Any]:
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
    from aiida.manage.configuration import get_config_option

    config = evaluate_logging_configuration(get_logging_config())

    fallback_level = LogLevels(t.cast(str, get_config_option('logging.aiida_loglevel')))

    # Replace ``INHERIT`` logger levels by their inherited fallback value
    for logger in config['loggers'].values():
        level = logger.get('level')
        if isinstance(level, str) and AdvancedLogLevels(level) is AdvancedLogLevels.INHERIT:
            logger['level'] = fallback_level.value

    if daemon is True:
        if daemon_log_file is None:
            msg = 'daemon_log_file has to be defined when configuring logging for the daemon'
            raise ValueError(msg)

        # Remove the `console` stdout stream handler to prevent messages being duplicated in the daemon log file
        for logger in config.get('loggers', {}).values():
            try:
                logger['handlers'].remove('console')
            except ValueError:
                pass

    if daemon_log_file is not None:
        handler_name = 'log_file'
        config.setdefault('handlers', {})
        config['handlers'][handler_name] = {
            'level': 'DEBUG',
            'formatter': 'halfverbose',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(daemon_log_file),
            'encoding': 'utf8',
            'maxBytes': 10000000,  # 10 MB
            'backupCount': 10,
        }

        for logger in config.get('loggers', {}).values():
            logger.setdefault('handlers', []).append(handler_name)

    # If the ``CLI_ACTIVE`` is set, a ``verdi`` command is being executed, so we replace the ``console`` handler with
    # the ``cli`` one for all loggers.
    if CLI_ACTIVE is True and not daemon:
        for logger in config['loggers'].values():
            handlers = logger['handlers']
            try:
                handlers.remove('console')
            except ValueError:
                pass
            handlers.append('cli')
        # If ``CLI_LOG_LEVEL`` is set, a ``verdi`` command is being executed with the ``--verbosity`` option. In this
        # case we override the aiida_loglevel and the cli to be sure it outputed to terminal.
        # Note: One has to also ensure that when reading from the corresponding config options while CLI is active are
        #       also updated. This should be in ``src.aiida.manage.configuration.get_config_option``
        if CLI_LOG_LEVEL is not None:
            config['loggers']['aiida']['level'] = CLI_LOG_LEVEL
            config['handlers']['cli']['level'] = CLI_LOG_LEVEL
            config['handlers']['console']['level'] = CLI_LOG_LEVEL

    # Add the `DbLogHandler` if `with_orm` is `True`
    if with_orm:
        from aiida.manage.configuration import get_config_option

        config['handlers']['database'] = {
            'level': get_config_option('logging.database_handler'),
            'class': 'aiida.orm.utils.log.DBLogHandler',
        }
        config['loggers']['aiida']['handlers'].append('database')

    dictConfig(config)


@contextlib.contextmanager
def override_log_level(level: int = logging.CRITICAL) -> collections.abc.Iterator[None]:
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
