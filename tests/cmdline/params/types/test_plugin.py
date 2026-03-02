###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `PluginParamType`."""

from unittest.mock import MagicMock, patch

import click
import pytest

from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.plugins.entry_point import get_entry_point_from_string


class TestPluginParamType:
    """Tests for the `PluginParamType`."""

    def test_group_definition(self):
        """Test the various accepted syntaxes of defining supported entry point groups. Both single
        values as well as tuples should be allowed. The `aiida.` prefix should also be optional.
        """
        param = PluginParamType(group='calculations')
        assert 'aiida.calculations' in param.groups
        assert len(param.groups) == 1

        param = PluginParamType(group='aiida.calculations')
        assert 'aiida.calculations' in param.groups
        assert len(param.groups) == 1

        param = PluginParamType(group=('calculations',))
        assert 'aiida.calculations' in param.groups
        assert len(param.groups) == 1

        param = PluginParamType(group=('aiida.calculations',))
        assert 'aiida.calculations' in param.groups
        assert len(param.groups) == 1

        param = PluginParamType(group=('aiida.calculations', 'aiida.data'))
        assert 'aiida.calculations' in param.groups
        assert 'aiida.data' in param.groups
        assert len(param.groups) == 2

        param = PluginParamType(group=('aiida.calculations', 'data'))
        assert 'aiida.calculations' in param.groups
        assert 'aiida.data' in param.groups
        assert len(param.groups) == 2

    def test_get_entry_point_from_string(self):
        """Test the functionality of the get_entry_point_from_string which will take an entry point string
        and try to map it onto a valid entry point that is part of the groups defined for the parameter.
        """
        param = PluginParamType(group='transports')
        entry_point = get_entry_point_from_string('aiida.transports:core.ssh')

        # Invalid entry point strings
        with pytest.raises(ValueError):
            param.get_entry_point_from_string('aiida.transport:core.ssh')

        with pytest.raises(ValueError):
            param.get_entry_point_from_string('aiid.transports:core.ssh')

        with pytest.raises(ValueError):
            param.get_entry_point_from_string('aiida..transports:core.ssh')

        # Unsupported entry points for all formats
        with pytest.raises(ValueError):
            param.get_entry_point_from_string('aiida.data:core.structure')

        with pytest.raises(ValueError):
            param.get_entry_point_from_string('data:structure')

        with pytest.raises(ValueError):
            param.get_entry_point_from_string('structure')

        # Non-existent entry points for all formats
        with pytest.raises(ValueError):
            param.get_entry_point_from_string('aiida.transports:not_existent')

        with pytest.raises(ValueError):
            param.get_entry_point_from_string('transports:not_existent')

        with pytest.raises(ValueError):
            param.get_entry_point_from_string('not_existent')

        # Valid entry point strings
        assert param.get_entry_point_from_string('aiida.transports:core.ssh').name == entry_point.name
        assert param.get_entry_point_from_string('transports:core.ssh').name == entry_point.name
        assert param.get_entry_point_from_string('core.ssh').name == entry_point.name

    def test_get_entry_point_from_ambiguous(self):
        """Test the functionality of the get_entry_point_from_string which will take an entry point string
        and try to map it onto a valid entry point that is part of the groups defined for the parameter.
        """
        param = PluginParamType(group=('aiida.calculations', 'aiida.parsers'))
        entry_point = get_entry_point_from_string('aiida.calculations:core.arithmetic.add')

        # Both groups contain entry point `arithmetic.add` so passing only name is ambiguous and should raise
        with pytest.raises(ValueError):
            param.get_entry_point_from_string('core.arithmetic.add')

        # Passing PARTIAL or FULL should allow entry point to be returned
        assert param.get_entry_point_from_string('aiida.calculations:core.arithmetic.add').name == entry_point.name
        assert param.get_entry_point_from_string('calculations:core.arithmetic.add').name == entry_point.name

    def test_convert(self):
        """Test that the convert method returns the correct entry point"""
        param = PluginParamType(group=('transports', 'data'))

        entry_point = param.convert('aiida.transports:core.ssh', None, None)
        assert entry_point.name == 'core.ssh'

        entry_point = param.convert('transports:core.ssh', None, None)
        assert entry_point.name == 'core.ssh'

        entry_point = param.convert('core.ssh', None, None)
        assert entry_point.name == 'core.ssh'

        entry_point = param.convert('aiida.data:core.structure', None, None)
        assert entry_point.name == 'core.structure'

        entry_point = param.convert('data:core.structure', None, None)
        assert entry_point.name == 'core.structure'

        entry_point = param.convert('core.structure', None, None)
        assert entry_point.name == 'core.structure'

        with pytest.raises(click.BadParameter):
            param.convert('not_existent', None, None)

    def test_convert_load(self):
        """Test that the convert method returns the loaded entry point if load=True at construction time of parameter"""
        param = PluginParamType(group=('transports', 'data'), load=True)
        entry_point_ssh = get_entry_point_from_string('aiida.transports:core.ssh')
        entry_point_structure = get_entry_point_from_string('aiida.data:core.structure')

        entry_point = param.convert('aiida.transports:core.ssh', None, None)
        assert entry_point, entry_point_ssh

        entry_point = param.convert('transports:core.ssh', None, None)
        assert entry_point, entry_point_ssh

        entry_point = param.convert('core.ssh', None, None)
        assert entry_point, entry_point_ssh

        entry_point = param.convert('aiida.data:core.structure', None, None)
        assert entry_point, entry_point_structure

        entry_point = param.convert('data:core.structure', None, None)
        assert entry_point, entry_point_structure

        entry_point = param.convert('core.structure', None, None)
        assert entry_point, entry_point_structure

        with pytest.raises(click.BadParameter):
            param.convert('not_existent', None, None)

    def test_complete_single_group(self):
        """Test the complete method which is used for auto completion when there is only a single valid group, which
        means there should never be ambiguity and specifying a full entry point string is not necessary, however,
        when the user decides to user either a FULL or PARTIAL string anyway, the completion should match that syntax
        """
        param = PluginParamType(group='transports')
        entry_point_minimal = 'core.ssh'
        entry_point_partial = 'transports:core.ssh'
        entry_point_full = 'aiida.transports:core.ssh'

        options = [item.value for item in param.shell_complete(None, None, 'core.ss')]
        assert entry_point_minimal in options

        options = [item.value for item in param.shell_complete(None, None, 'core.ssh')]
        assert entry_point_minimal in options

        options = [item.value for item in param.shell_complete(None, None, 'transports:core.ss')]
        assert entry_point_partial in options

        options = [item.value for item in param.shell_complete(None, None, 'transports:core.ssh')]
        assert entry_point_partial in options

        options = [item.value for item in param.shell_complete(None, None, 'aiida.transports:core.ss')]
        assert entry_point_full in options

        options = [item.value for item in param.shell_complete(None, None, 'aiida.transports:core.ssh')]
        assert entry_point_full in options

    def test_complete_amibguity(self):
        """Test the complete method which is used for auto completion when the supported groups share an entry point
        with the same name, which can lead to ambiguity. In this case the autocomplete should always return the
        possibilites in the FULL entry point string format. When the user tries to autocomplete
        """
        param = PluginParamType(group=('aiida.calculations', 'aiida.parsers'))
        entry_point_full_calculations = 'aiida.calculations:core.arithmetic.add'
        entry_point_full_parsers = 'aiida.parsers:core.arithmetic.add'

        options = [item.value for item in param.shell_complete(None, None, 'aiida.calculations:core.arith')]
        assert entry_point_full_calculations in options

        options = [item.value for item in param.shell_complete(None, None, 'aiida.calculations:core.arithmetic.add')]
        assert entry_point_full_calculations in options

        options = [item.value for item in param.shell_complete(None, None, 'aiida.parsers:core.arith')]
        assert entry_point_full_parsers in options

        options = [item.value for item in param.shell_complete(None, None, 'aiida.parsers:core.arithmetic.add')]
        assert entry_point_full_parsers in options

        # PARTIAL or MINIMAL string formats will not be autocompleted
        options = [item.value for item in param.shell_complete(None, None, 'parsers:core.arith')]
        assert entry_point_full_calculations not in options
        assert entry_point_full_parsers not in options

        options = [item.value for item in param.shell_complete(None, None, 'parsers:core.arithmetic.add')]
        assert entry_point_full_calculations not in options
        assert entry_point_full_parsers not in options

        options = [item.value for item in param.shell_complete(None, None, 'core.arith')]
        assert entry_point_full_calculations not in options
        assert entry_point_full_parsers not in options

        options = [item.value for item in param.shell_complete(None, None, 'core.arithmetic.add')]
        assert entry_point_full_calculations not in options
        assert entry_point_full_parsers not in options

    def test_shell_complete_includes_help_text(self):
        """Test that shell_complete populates CompletionItem.help with the plugin docstring."""

        class PluginWithDoc:
            """My plugin description.\n\nMore details here."""

        class PluginWithoutDoc:
            pass

        ep_with_doc = MagicMock()
        ep_with_doc.name = 'plugin.with_doc'
        ep_with_doc.load.return_value = PluginWithDoc

        ep_without_doc = MagicMock()
        ep_without_doc.name = 'plugin.without_doc'
        ep_without_doc.load.return_value = PluginWithoutDoc

        ep_failing = MagicMock()
        ep_failing.name = 'plugin.failing'
        ep_failing.load.side_effect = ImportError('cannot load')

        fake_entry_points = [
            ('aiida.test_group', ep_with_doc),
            ('aiida.test_group', ep_without_doc),
            ('aiida.test_group', ep_failing),
        ]

        param = PluginParamType(group='transports')

        param._entry_points = fake_entry_points
        with patch.object(
            param, 'get_possibilities', return_value=['plugin.with_doc', 'plugin.without_doc', 'plugin.failing']
        ):
            items = param.shell_complete(None, None, '')

        assert len(items) == 3
        assert items[0].value == 'plugin.with_doc'
        assert items[0].help == 'My plugin description.'
        assert items[1].value == 'plugin.without_doc'
        assert items[1].help is None
        assert items[2].value == 'plugin.failing'
        assert items[2].help is None
