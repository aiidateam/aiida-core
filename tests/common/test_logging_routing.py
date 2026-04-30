###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the logging routing filters (Phase 2 of the logging redesign).

Tests cover:
- Phase 2a: ``terminal_loglevel`` handler-level filter on ``console`` and ``cli`` handlers
- Phase 2b: ``logfile_loglevel`` handler-level filter on daemon log handler
- Phase 2c: ``--verbosity`` override of ``cli`` handler level
"""

import pytest

from aiida.common import log as log_module


@pytest.mark.presto
class TestTerminalLoglevelHandlerFilter:
    """Tests for ``terminal_loglevel`` as handler-level filter on console and cli handlers."""

    def test_console_handler_has_level(self):
        """The ``console`` handler in the logging config should have a ``level`` key."""
        config = log_module.get_logging_config()
        assert 'level' in config['handlers']['console'], 'console handler should have a level key'

    def test_cli_handler_has_level(self):
        """The ``cli`` handler in the logging config should have a ``level`` key."""
        config = log_module.get_logging_config()
        assert 'level' in config['handlers']['cli'], 'cli handler should have a level key'

    def test_console_handler_level_is_callable(self):
        """The ``console`` handler level should be a lambda (lazy evaluation)."""
        config = log_module.get_logging_config()
        assert callable(config['handlers']['console']['level'])

    def test_cli_handler_level_is_callable(self):
        """The ``cli`` handler level should be a lambda (lazy evaluation)."""
        config = log_module.get_logging_config()
        assert callable(config['handlers']['cli']['level'])

    def test_console_handler_level_evaluates_to_report(self):
        """The ``console`` handler level should evaluate to ``REPORT`` by default."""
        config = log_module.get_logging_config()
        level = config['handlers']['console']['level']
        assert level() == 'REPORT'

    def test_cli_handler_level_evaluates_to_report(self):
        """The ``cli`` handler level should evaluate to ``REPORT`` by default."""
        config = log_module.get_logging_config()
        level = config['handlers']['cli']['level']
        assert level() == 'REPORT'

    def test_evaluate_logging_configuration_resolves_handler_levels(self):
        """``evaluate_logging_configuration`` should resolve lambdas inside handler dicts."""
        config = log_module.get_logging_config()
        evaluated = log_module.evaluate_logging_configuration(config)
        assert evaluated['handlers']['console']['level'] == 'REPORT'
        assert evaluated['handlers']['cli']['level'] == 'REPORT'


@pytest.mark.presto
class TestSystemLoglevelDaemonHandler:
    """Tests for ``logfile_loglevel`` as handler-level filter on the daemon log handler."""

    def test_daemon_handler_uses_logfile_loglevel(self, tmp_path):
        """When ``daemon=True``, the daemon handler should use ``logfile_loglevel`` (default: DEBUG)."""
        daemon_log = tmp_path / 'daemon.log'

        # We need to capture the config dict BEFORE dictConfig is called.
        # We do this by monkeypatching dictConfig to capture its argument.
        captured_config = {}

        def capture_dict_config(config):
            captured_config.update(config)

        import logging.config

        original = logging.config.dictConfig

        try:
            logging.config.dictConfig = capture_dict_config
            log_module.configure_logging(daemon=True, daemon_log_file=str(daemon_log))
        finally:
            logging.config.dictConfig = original

        assert 'daemon_log_file' in captured_config['handlers']
        # The daemon handler level should be DEBUG (the default for logfile_loglevel)
        assert captured_config['handlers']['daemon_log_file']['level'] == 'DEBUG'


@pytest.mark.presto
class TestVerbosityOverridesCliHandler:
    """Tests for ``--verbosity`` also overriding the ``cli`` handler level (Phase 2c)."""

    def test_cli_log_level_overrides_cli_handler(self):
        """When ``CLI_LOG_LEVEL`` is set, the ``cli`` handler level should also be overridden."""
        captured_config = {}

        def capture_dict_config(config):
            captured_config.update(config)

        import logging.config

        original_dict_config = logging.config.dictConfig
        original_cli_active = log_module.CLI_ACTIVE
        original_cli_log_level = log_module.CLI_LOG_LEVEL

        try:
            log_module.CLI_ACTIVE = True
            log_module.CLI_LOG_LEVEL = 'DEBUG'
            logging.config.dictConfig = capture_dict_config
            log_module.configure_logging()
        finally:
            logging.config.dictConfig = original_dict_config
            log_module.CLI_ACTIVE = original_cli_active
            log_module.CLI_LOG_LEVEL = original_cli_log_level

        # The cli handler level should be overridden to DEBUG
        assert captured_config['handlers']['cli']['level'] == 'DEBUG'

    def test_cli_log_level_none_keeps_default(self):
        """When ``CLI_LOG_LEVEL`` is None, the ``cli`` handler level should remain the default."""
        captured_config = {}

        def capture_dict_config(config):
            captured_config.update(config)

        import logging.config

        original_dict_config = logging.config.dictConfig
        original_cli_active = log_module.CLI_ACTIVE
        original_cli_log_level = log_module.CLI_LOG_LEVEL

        try:
            log_module.CLI_ACTIVE = True
            log_module.CLI_LOG_LEVEL = None
            logging.config.dictConfig = capture_dict_config
            log_module.configure_logging()
        finally:
            logging.config.dictConfig = original_dict_config
            log_module.CLI_ACTIVE = original_cli_active
            log_module.CLI_LOG_LEVEL = original_cli_log_level

        # The cli handler level should remain REPORT (from terminal_loglevel default)
        assert captured_config['handlers']['cli']['level'] == 'REPORT'
