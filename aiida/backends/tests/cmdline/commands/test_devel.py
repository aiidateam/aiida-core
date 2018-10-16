# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi devel`."""
from __future__ import absolute_import
import tempfile

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_devel
from aiida.common import setup as aiida_cfg
from aiida.common.setup import _property_table, exists_property, get_property, del_property


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiDevel(AiidaTestCase):
    """Tests for `verdi devel`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiDevel, cls).setUpClass()

        cls._old_aiida_config_folder = None
        cls._new_aiida_config_folder = tempfile.mkdtemp()
        cls._old_aiida_config_folder = aiida_cfg.AIIDA_CONFIG_FOLDER

        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._new_aiida_config_folder
        aiida_cfg.create_base_dirs()

        cls.profile_name = 'aiida_dummy_profile_1234'
        cls.dummy_profile = {}
        cls.dummy_profile['backend'] = 'django'
        cls.dummy_profile['db_host'] = 'localhost'
        cls.dummy_profile['db_port'] = '5432'
        cls.dummy_profile['email'] = 'dummy@localhost'
        cls.dummy_profile['db_name'] = cls.profile_name
        cls.dummy_profile['db_user'] = 'dummy_user'
        cls.dummy_profile['db_pass'] = 'dummy_pass'
        cls.dummy_profile['repo'] = aiida_cfg.AIIDA_CONFIG_FOLDER + '/repository_' + cls.profile_name

        aiida_cfg.create_config_noninteractive(profile=cls.profile_name, **cls.dummy_profile)
        aiida_cfg.set_default_profile(cls.profile_name, force_rewrite=True)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """
        Remove dummy profiles created in setUpClass.

        :param args: list of arguments
        :param kwargs: list of keyword arguments
        """
        import os
        import shutil

        aiida_cfg.AIIDA_CONFIG_FOLDER = cls._old_aiida_config_folder

        if os.path.isdir(cls._new_aiida_config_folder):
            shutil.rmtree(cls._new_aiida_config_folder)

    def setUp(self):
        self.runner = CliRunner()

    def tearDown(self):
        """Delete any properties that were set."""
        for prop in sorted(_property_table.keys()):
            if exists_property(prop):
                del_property(prop)

    def test_describe_properties(self):
        """Test the `verdi devel describeproperties` command"""
        result = self.runner.invoke(cmd_devel.devel_describeproperties, [])

        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > 0)

        for prop in _property_table:
            self.assertIn(prop, result.output)

    def test_list_properties(self):
        """Test the `verdi devel listproperties` command"""

        # Since dummy configuration does not have explicit properties set, with default options the result is empty
        options = []
        result = self.runner.invoke(cmd_devel.devel_listproperties, options)
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) == 0)

        # Toggling the all flag should show all available options
        for flag in ['-a', '--all']:

            options = [flag]
            result = self.runner.invoke(cmd_devel.devel_listproperties, options)
            self.assertIsNone(result.exception)
            self.assertTrue(len(get_result_lines(result)) > 0)

            for prop in _property_table:
                self.assertIn(prop, result.output)

    def test_set_property(self):
        """Test the `verdi devel setproperty` command."""
        property_name = 'daemon.timeout'
        property_values = [10, 20]

        for property_value in property_values:
            options = [property_name, str(property_value)]
            result = self.runner.invoke(cmd_devel.devel_setproperty, options)

            self.assertIsNone(result.exception)
            self.assertEquals(get_property(property_name), property_value)

    def test_get_property(self):
        """Test the `verdi devel getproperty` command."""
        property_name = 'daemon.timeout'
        property_value = 30

        options = [property_name, str(property_value)]
        result = self.runner.invoke(cmd_devel.devel_setproperty, options)

        options = [property_name]
        result = self.runner.invoke(cmd_devel.devel_getproperty, options)
        self.assertIsNone(result.exception)
        self.assertEquals(str(property_value), result.output.strip())

    def test_del_property(self):
        """Test the `verdi devel delproperty` command."""
        property_name = 'daemon.timeout'
        property_value = 30

        options = [property_name, str(property_value)]
        result = self.runner.invoke(cmd_devel.devel_setproperty, options)

        options = [property_name]
        result = self.runner.invoke(cmd_devel.devel_delproperty, options)
        self.assertIsNone(result.exception)
        self.assertIn(property_name, result.output.strip())
        self.assertFalse(exists_property(property_name))
