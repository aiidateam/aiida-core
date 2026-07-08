###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.common.log` module."""

import logging
import logging.config
from unittest.mock import Mock

import pytest

from aiida.common import log
from aiida.common.log import capture_logging


def test_logging_before_dbhandler_loaded(caplog):
    """Test that logging still works even if no database is loaded.

    When a profile is loaded, the ``DbLogHandler`` logging handler is configured that redirects log messages to the
    database. This should not break the logging functionality when no database has been loaded yet.
    """
    msg = 'Testing a critical message'
    logger = logging.getLogger()
    logging.getLogger().critical(msg)
    assert caplog.record_tuples == [(logger.name, logging.CRITICAL, msg)]


def test_log_report(caplog):
    """Test that the ``logging`` module is patched such that the ``Logger`` class has the ``report`` method.

    The ``report`` method corresponds to a call to the :meth:``Logger.log`` method where the log level used is the
    :data:`aiida.common.log.LOG_LEVEL_REPORT`.
    """
    msg = 'Testing a report message'
    logger = logging.getLogger()

    with caplog.at_level(logging.REPORT):
        logger.report(msg)

    assert caplog.record_tuples == [(logger.name, logging.REPORT, msg)]


def test_capture_logging():
    """Test the :func:`aiida.common.log.capture_logging` function."""
    logger = logging.getLogger()
    message = 'Some message'
    with capture_logging(logger) as stream:
        logging.getLogger().error(message)
        assert stream.getvalue().strip() == message


class TestValidateHandler:
    """Tests for :func:`aiida.common.log.validate_handler`."""

    def test_warns_when_more_verbose_than_loggers(self):
        """A handler level below every logger level cannot take effect and should return a warning."""
        levels = {'logging.terminal_handler': 'DEBUG', 'logging.aiida_loglevel': 'INFO'}
        config = Mock(get_option=lambda name, scope=None: levels.get(name, 'WARNING'))
        message = log.validate_handler(config, 'logging.terminal_handler')
        assert message is not None
        assert 'take effect' in message

    def test_no_warning_when_effective(self):
        """A handler level a logger actually emits at (here equal to it) is effective and should return ``None``."""
        levels = {'logging.database_handler': 'INFO', 'logging.aiida_loglevel': 'INFO'}
        config = Mock(get_option=lambda name, scope=None: levels.get(name, 'WARNING'))
        assert log.validate_handler(config, 'logging.database_handler') is None


@pytest.mark.presto
class TestVerbosityOverridesCliHandler:
    """Tests for ``--verbosity`` also overriding the ``cli`` handler level."""

    def test_cli_log_level_overrides_cli_handler(self):
        """When ``CLI_LOG_LEVEL`` is set, the ``cli`` handler level should also be overridden."""
        captured_config = {}

        def capture_dict_config(config):
            captured_config.update(config)

        import logging.config

        original_dict_config = logging.config.dictConfig
        original_cli_active = log.CLI_ACTIVE
        original_cli_log_level = log.CLI_LOG_LEVEL

        try:
            log.CLI_ACTIVE = True
            log.CLI_LOG_LEVEL = 'DEBUG'
            logging.config.dictConfig = capture_dict_config
            log.configure_logging()
        finally:
            logging.config.dictConfig = original_dict_config
            log.CLI_ACTIVE = original_cli_active
            log.CLI_LOG_LEVEL = original_cli_log_level

        # The cli handler level should be overridden to DEBUG
        assert captured_config['handlers']['cli']['level'] == 'DEBUG'

    def test_cli_log_level_none_keeps_default(self):
        """When ``CLI_LOG_LEVEL`` is None, the ``cli`` handler level should remain the default."""
        captured_config = {}

        def capture_dict_config(config):
            captured_config.update(config)

        import logging.config

        original_dict_config = logging.config.dictConfig
        original_cli_active = log.CLI_ACTIVE
        original_cli_log_level = log.CLI_LOG_LEVEL

        try:
            log.CLI_ACTIVE = True
            log.CLI_LOG_LEVEL = None
            logging.config.dictConfig = capture_dict_config
            log.configure_logging()
        finally:
            logging.config.dictConfig = original_dict_config
            log.CLI_ACTIVE = original_cli_active
            log.CLI_LOG_LEVEL = original_cli_log_level

        # The cli handler level should remain REPORT (from terminal_handler default)
        assert captured_config['handlers']['cli']['level'] == 'REPORT'
