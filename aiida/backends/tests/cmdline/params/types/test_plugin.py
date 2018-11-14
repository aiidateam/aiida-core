# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for plugin parameter type."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click
import mock

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.plugins.entry_point import get_entry_point_from_string


class TestPluginParamType(AiidaTestCase):
    """Unit tests for plugin parameter type."""

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
        entry_point = get_entry_point_from_string('aiida.transports:ssh')

        # Invalid entry point strings
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida.transport:ssh')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiid.transports:ssh')

        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida..transports:ssh')

        # Unsupported entry points for all formats
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('aiida.data:structure')

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
        self.assertEquals(param.get_entry_point_from_string('aiida.transports:ssh').name, entry_point.name)
        self.assertEquals(param.get_entry_point_from_string('transports:ssh').name, entry_point.name)
        self.assertEquals(param.get_entry_point_from_string('ssh').name, entry_point.name)

    def test_get_entry_point_from_string_ambiguous(self):
        """
        Test the functionality of the get_entry_point_from_string which will take an entry point string
        and try to map it onto a valid entry point that is part of the groups defined for the parameter.
        """
        param = PluginParamType(group=('aiida.tools.dbexporters', 'aiida.tools.dbimporters'))
        entry_point = get_entry_point_from_string('aiida.tools.dbexporters:tcod')

        # Both groups contain entry point `tcod` so passing only name is ambiguous and should raise
        with self.assertRaises(ValueError):
            param.get_entry_point_from_string('tcod')

        # Passing PARTIAL or FULL should allow entry point to be returned
        self.assertEquals(param.get_entry_point_from_string('aiida.tools.dbexporters:tcod').name, entry_point.name)
        self.assertEquals(param.get_entry_point_from_string('tools.dbexporters:tcod').name, entry_point.name)

    def test_convert(self):
        """
        Test that the convert method returns the correct entry point
        """
        param = PluginParamType(group=('transports', 'data'))

        entry_point = param.convert('aiida.transports:ssh', None, None)
        self.assertEquals(entry_point.name, 'ssh')
        # self.assertTrue(isinstance(entry_point, EntryPoint))

        entry_point = param.convert('transports:ssh', None, None)
        self.assertEquals(entry_point.name, 'ssh')
        # self.assertTrue(isinstance(entry_point, EntryPoint))

        entry_point = param.convert('ssh', None, None)
        self.assertEquals(entry_point.name, 'ssh')
        # self.assertTrue(isinstance(entry_point, EntryPoint))

        entry_point = param.convert('aiida.data:structure', None, None)
        self.assertEquals(entry_point.name, 'structure')
        # self.assertTrue(isinstance(entry_point, EntryPoint))

        entry_point = param.convert('data:structure', None, None)
        self.assertEquals(entry_point.name, 'structure')
        # self.assertTrue(isinstance(entry_point, EntryPoint))

        entry_point = param.convert('structure', None, None)
        self.assertEquals(entry_point.name, 'structure')
        # self.assertTrue(isinstance(entry_point, EntryPoint))

        with self.assertRaises(click.BadParameter):
            param.convert('not_existent', None, None)

    def test_convert_load(self):
        """
        Test that the convert method returns the loaded entry point if load=True at construction time of parameter
        """
        param = PluginParamType(group=('transports', 'data'), load=True)
        entry_point_ssh = get_entry_point_from_string('aiida.transports:ssh')
        entry_point_structure = get_entry_point_from_string('aiida.data:structure')

        entry_point = param.convert('aiida.transports:ssh', None, None)
        self.assertTrue(entry_point, entry_point_ssh)

        entry_point = param.convert('transports:ssh', None, None)
        self.assertTrue(entry_point, entry_point_ssh)

        entry_point = param.convert('ssh', None, None)
        self.assertTrue(entry_point, entry_point_ssh)

        entry_point = param.convert('aiida.data:structure', None, None)
        self.assertTrue(entry_point, entry_point_structure)

        entry_point = param.convert('data:structure', None, None)
        self.assertTrue(entry_point, entry_point_structure)

        entry_point = param.convert('structure', None, None)
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
        entry_point_minimal = 'ssh'
        entry_point_partial = 'transports:ssh'
        entry_point_full = 'aiida.transports:ssh'

        options = [item[0] for item in param.complete(None, 'ss')]
        self.assertIn(entry_point_minimal, options)

        options = [item[0] for item in param.complete(None, 'ssh')]
        self.assertIn(entry_point_minimal, options)

        options = [item[0] for item in param.complete(None, 'transports:ss')]
        self.assertIn(entry_point_partial, options)

        options = [item[0] for item in param.complete(None, 'transports:ssh')]
        self.assertIn(entry_point_partial, options)

        options = [item[0] for item in param.complete(None, 'aiida.transports:ss')]
        self.assertIn(entry_point_full, options)

        options = [item[0] for item in param.complete(None, 'aiida.transports:ssh')]
        self.assertIn(entry_point_full, options)

    def test_complete_amibguity(self):
        """
        Test the complete method which is used for auto completion when the supported groups share an entry point
        with the same name, which can lead to ambiguity. In this case the autocomplete should always return the
        possibilites in the FULL entry point string format. When the user tries to autocomplete
        """
        param = PluginParamType(group=('aiida.tools.dbexporters', 'aiida.tools.dbimporters'))
        entry_point_full_exporters = 'aiida.tools.dbexporters:tcod'
        entry_point_full_importers = 'aiida.tools.dbimporters:tcod'

        options = [item[0] for item in param.complete(None, 'aiida.tools.dbexporters:tc')]
        self.assertIn(entry_point_full_exporters, options)

        options = [item[0] for item in param.complete(None, 'aiida.tools.dbexporters:tcod')]
        self.assertIn(entry_point_full_exporters, options)

        options = [item[0] for item in param.complete(None, 'aiida.tools.dbimporters:tc')]
        self.assertIn(entry_point_full_importers, options)

        options = [item[0] for item in param.complete(None, 'aiida.tools.dbimporters:tcod')]
        self.assertIn(entry_point_full_importers, options)

        # PARTIAL or MINIMAL string formats will not be autocompleted
        options = [item[0] for item in param.complete(None, 'tools.dbimporters:tc')]
        self.assertNotIn(entry_point_full_exporters, options)
        self.assertNotIn(entry_point_full_importers, options)

        options = [item[0] for item in param.complete(None, 'tools.dbimporters:tcod')]
        self.assertNotIn(entry_point_full_exporters, options)
        self.assertNotIn(entry_point_full_importers, options)

        options = [item[0] for item in param.complete(None, 'tc')]
        self.assertNotIn(entry_point_full_exporters, options)
        self.assertNotIn(entry_point_full_importers, options)

        options = [item[0] for item in param.complete(None, 'tcod')]
        self.assertNotIn(entry_point_full_exporters, options)
        self.assertNotIn(entry_point_full_importers, options)
