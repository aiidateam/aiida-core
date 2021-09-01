# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `PluginParamType`."""

import click

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.plugins.entry_point import get_entry_point_from_string


class TestPluginParamType(AiidaTestCase):
    """Tests for the `PluginParamType`."""

    def test_group_definition(self):
        """
        Test the various accepted syntaxes of defining supported entry point groups. Both single
        values as well as tuples should be allowed. The `aiida.` prefix should also be optional.
        """
        param = PluginParamType(group='calculations')
        self.assertIn('aiida.calculations', param.groups)
        self.assertTrue(len(param.groups), 1)

        param = PluginParamType(group='aiida.calculations')
        self.assertIn('aiida.calculations', param.groups)
        self.assertTrue(len(param.groups), 1)

        param = PluginParamType(group=('calculations',))
        self.assertIn('aiida.calculations', param.groups)
        self.assertTrue(len(param.groups), 1)

        param = PluginParamType(group=('aiida.calculations',))
        self.assertIn('aiida.calculations', param.groups)
        self.assertTrue(len(param.groups), 1)

        param = PluginParamType(group=('aiida.calculations', 'aiida.data'))
        self.assertIn('aiida.calculations', param.groups)
        self.assertIn('aiida.data', param.groups)
        self.assertTrue(len(param.groups), 2)

        param = PluginParamType(group=('aiida.calculations', 'data'))
        self.assertIn('aiida.calculations', param.groups)
        self.assertIn('aiida.data', param.groups)
        self.assertTrue(len(param.groups), 2)

    def test_get_entry_point_from_string(self):
        """
        Test the functionality of the get_entry_point_from_string which will take an entry point string
        and try to map it onto a valid entry point that is part of the groups defined for the parameter.
        """
        param = PluginParamType(group='transports')
        entry_point = get_entry_point_from_string('aiida.transports:core.ssh')

        # Invalid entry point strings
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida.transport:core.ssh')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiid.transports:core.ssh')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida..transports:core.ssh')

        # Unsupported entry points for all formats
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida.data:core.structure')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('data:structure')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('structure')

        # Non-existent entry points for all formats
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida.transports:not_existent')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('transports:not_existent')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('not_existent')

        # Valid entry point strings
        self.assertEqual(param.get_entry_point_from_string('aiida.transports:core.ssh').name, entry_point.name)
        self.assertEqual(param.get_entry_point_from_string('transports:core.ssh').name, entry_point.name)
        self.assertEqual(param.get_entry_point_from_string('core.ssh').name, entry_point.name)

    def test_get_entry_point_from_ambiguous(self):
        """
        Test the functionality of the get_entry_point_from_string which will take an entry point string
        and try to map it onto a valid entry point that is part of the groups defined for the parameter.
        """
        param = PluginParamType(group=('aiida.calculations', 'aiida.parsers'))
        entry_point = get_entry_point_from_string('aiida.calculations:core.arithmetic.add')

        # Both groups contain entry point `arithmetic.add` so passing only name is ambiguous and should raise
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('core.arithmetic.add')

        # Passing PARTIAL or FULL should allow entry point to be returned
        self.assertEqual(
            param.get_entry_point_from_string('aiida.calculations:core.arithmetic.add').name, entry_point.name
        )
        self.assertEqual(param.get_entry_point_from_string('calculations:core.arithmetic.add').name, entry_point.name)

    def test_convert(self):
        """
        Test that the convert method returns the correct entry point
        """
        param = PluginParamType(group=('transports', 'data'))

        entry_point = param.convert('aiida.transports:core.ssh', None, None)
        self.assertEqual(entry_point.name, 'core.ssh')

        entry_point = param.convert('transports:core.ssh', None, None)
        self.assertEqual(entry_point.name, 'core.ssh')

        entry_point = param.convert('core.ssh', None, None)
        self.assertEqual(entry_point.name, 'core.ssh')

        entry_point = param.convert('aiida.data:core.structure', None, None)
        self.assertEqual(entry_point.name, 'core.structure')

        entry_point = param.convert('data:core.structure', None, None)
        self.assertEqual(entry_point.name, 'core.structure')

        entry_point = param.convert('core.structure', None, None)
        self.assertEqual(entry_point.name, 'core.structure')

        with self.assertRaises(click.BadParameter):
            param.convert('not_existent', None, None)

    def test_convert_load(self):
        """
        Test that the convert method returns the loaded entry point if load=True at construction time of parameter
        """
        param = PluginParamType(group=('transports', 'data'), load=True)
        entry_point_ssh = get_entry_point_from_string('aiida.transports:core.ssh')
        entry_point_structure = get_entry_point_from_string('aiida.data:core.structure')

        entry_point = param.convert('aiida.transports:core.ssh', None, None)
        self.assertTrue(entry_point, entry_point_ssh)

        entry_point = param.convert('transports:core.ssh', None, None)
        self.assertTrue(entry_point, entry_point_ssh)

        entry_point = param.convert('core.ssh', None, None)
        self.assertTrue(entry_point, entry_point_ssh)

        entry_point = param.convert('aiida.data:core.structure', None, None)
        self.assertTrue(entry_point, entry_point_structure)

        entry_point = param.convert('data:core.structure', None, None)
        self.assertTrue(entry_point, entry_point_structure)

        entry_point = param.convert('core.structure', None, None)
        self.assertTrue(entry_point, entry_point_structure)

        with self.assertRaises(click.BadParameter):
            param.convert('not_existent', None, None)

    def test_complete_single_group(self):
        """
        Test the complete method which is used for auto completion when there is only a single valid group, which
        means there should never be ambiguity and specifying a full entry point string is not necessary, however,
        when the user decides to user either a FULL or PARTIAL string anyway, the completion should match that syntax
        """
        param = PluginParamType(group=('transports'))
        entry_point_minimal = 'core.ssh'
        entry_point_partial = 'transports:core.ssh'
        entry_point_full = 'aiida.transports:core.ssh'

        options = [item[0] for item in param.complete(None, 'core.ss')]
        self.assertIn(entry_point_minimal, options)

        options = [item[0] for item in param.complete(None, 'core.ssh')]
        self.assertIn(entry_point_minimal, options)

        options = [item[0] for item in param.complete(None, 'transports:core.ss')]
        self.assertIn(entry_point_partial, options)

        options = [item[0] for item in param.complete(None, 'transports:core.ssh')]
        self.assertIn(entry_point_partial, options)

        options = [item[0] for item in param.complete(None, 'aiida.transports:core.ss')]
        self.assertIn(entry_point_full, options)

        options = [item[0] for item in param.complete(None, 'aiida.transports:core.ssh')]
        self.assertIn(entry_point_full, options)

    def test_complete_amibguity(self):
        """
        Test the complete method which is used for auto completion when the supported groups share an entry point
        with the same name, which can lead to ambiguity. In this case the autocomplete should always return the
        possibilites in the FULL entry point string format. When the user tries to autocomplete
        """
        param = PluginParamType(group=('aiida.calculations', 'aiida.parsers'))
        entry_point_full_calculations = 'aiida.calculations:core.arithmetic.add'
        entry_point_full_parsers = 'aiida.parsers:core.arithmetic.add'

        options = [item[0] for item in param.complete(None, 'aiida.calculations:core.arith')]
        self.assertIn(entry_point_full_calculations, options)

        options = [item[0] for item in param.complete(None, 'aiida.calculations:core.arithmetic.add')]
        self.assertIn(entry_point_full_calculations, options)

        options = [item[0] for item in param.complete(None, 'aiida.parsers:core.arith')]
        self.assertIn(entry_point_full_parsers, options)

        options = [item[0] for item in param.complete(None, 'aiida.parsers:core.arithmetic.add')]
        self.assertIn(entry_point_full_parsers, options)

        # PARTIAL or MINIMAL string formats will not be autocompleted
        options = [item[0] for item in param.complete(None, 'parsers:core.arith')]
        self.assertNotIn(entry_point_full_calculations, options)
        self.assertNotIn(entry_point_full_parsers, options)

        options = [item[0] for item in param.complete(None, 'parsers:core.arithmetic.add')]
        self.assertNotIn(entry_point_full_calculations, options)
        self.assertNotIn(entry_point_full_parsers, options)

        options = [item[0] for item in param.complete(None, 'core.arith')]
        self.assertNotIn(entry_point_full_calculations, options)
        self.assertNotIn(entry_point_full_parsers, options)

        options = [item[0] for item in param.complete(None, 'core.arithmetic.add')]
        self.assertNotIn(entry_point_full_calculations, options)
        self.assertNotIn(entry_point_full_parsers, options)
