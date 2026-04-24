###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the logging-related configuration options added by the logging redesign.

Tests cover:
- Phase 1a: New ``logging.terminal_loglevel`` and ``logging.logfile_loglevel`` options
- Phase 1b: Existing per-logger options marked as advanced
- Phase 1c: ``Option.advanced`` property
"""

import pytest

from aiida.manage.configuration.options import Option, get_option, get_option_names


@pytest.mark.presto
class TestNewLoggingOptions:
    """Tests for the two new routing options."""

    def test_terminal_loglevel_exists(self):
        """The ``logging.terminal_loglevel`` option should exist."""
        option = get_option('logging.terminal_loglevel')
        assert isinstance(option, Option)

    def test_terminal_loglevel_default(self):
        """The ``logging.terminal_loglevel`` option should default to ``REPORT``."""
        option = get_option('logging.terminal_loglevel')
        assert option.default == 'REPORT'

    def test_logfile_loglevel_exists(self):
        """The ``logging.logfile_loglevel`` option should exist."""
        option = get_option('logging.logfile_loglevel')
        assert isinstance(option, Option)

    def test_logfile_loglevel_default(self):
        """The ``logging.logfile_loglevel`` option should default to ``INFO``."""
        option = get_option('logging.logfile_loglevel')
        assert option.default == 'INFO'

    def test_new_options_are_not_advanced(self):
        """The new routing options should NOT be marked as advanced."""
        for name in ('logging.terminal_loglevel', 'logging.logfile_loglevel'):
            option = get_option(name)
            assert option.advanced is False, f'{name} should not be advanced'

    def test_new_options_are_not_global_only(self):
        """The new routing options should be settable per-profile."""
        for name in ('logging.terminal_loglevel', 'logging.logfile_loglevel'):
            option = get_option(name)
            assert option.global_only is False, f'{name} should not be global_only'

    def test_new_options_in_option_names(self):
        """The new options should appear in the list of all option names."""
        names = get_option_names()
        assert 'logging.terminal_loglevel' in names
        assert 'logging.logfile_loglevel' in names


@pytest.mark.presto
class TestAdvancedLoggingOptions:
    """Tests for the advanced flag on existing per-logger options."""

    ADVANCED_LOGGING_OPTIONS = [
        'logging.aiida_loglevel',
        'logging.verdi_loglevel',
        'logging.disk_objectstore_loglevel',
        'logging.db_loglevel',
        'logging.plumpy_loglevel',
        'logging.kiwipy_loglevel',
        'logging.paramiko_loglevel',
        'logging.alembic_loglevel',
        'logging.sqlalchemy_loglevel',
        'logging.circus_loglevel',
        'logging.aiopika_loglevel',
    ]

    @pytest.mark.parametrize('option_name', ADVANCED_LOGGING_OPTIONS)
    def test_existing_logging_options_are_advanced(self, option_name):
        """Each of the 11 existing per-logger options should be marked as advanced."""
        option = get_option(option_name)
        assert option.advanced is True, f'{option_name} should be marked as advanced'


@pytest.mark.presto
class TestOptionAdvancedProperty:
    """Tests for the ``Option.advanced`` property."""

    def test_non_logging_option_not_advanced(self):
        """A non-logging option like ``daemon.timeout`` should not be advanced."""
        option = get_option('daemon.timeout')
        assert option.advanced is False

    def test_advanced_returns_bool(self):
        """The ``advanced`` property should always return a bool."""
        option = get_option('daemon.timeout')
        assert isinstance(option.advanced, bool)


@pytest.mark.presto
class TestVerdiLoglevelDescription:
    """Test that the verdi_loglevel description was updated."""

    def test_verdi_loglevel_description_is_source_filter(self):
        """The ``logging.verdi_loglevel`` description should indicate it is a source-level filter."""
        option = get_option('logging.verdi_loglevel')
        # It should NOT say "console" anymore — it's a source filter, not a routing filter
        assert 'console' not in option.description.lower()
        assert 'source' in option.description.lower()
