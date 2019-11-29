# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for utilities dealing with plugins and entry points."""

from aiida import __version__ as version_core
from aiida.backends.testbase import AiidaTestCase
from aiida.engine import calcfunction, WorkChain
from aiida.plugins import CalculationFactory
from aiida.plugins.utils import PluginVersionProvider


class TestPluginVersionProvider(AiidaTestCase):
    """Tests for the :py:class:`~aiida.plugins.utils.PluginVersionProvider` utility class."""

    # pylint: disable=no-init,old-style-class,too-few-public-methods,no-member

    def setUp(self):
        super().setUp()
        self.provider = PluginVersionProvider()

    @staticmethod
    def create_dynamic_plugin_module(plugin, plugin_version, add_module_to_sys=True, add_version=True):
        """Create a fake dynamic module with a certain `plugin` entity, a class or function and the given version."""
        import sys
        import types
        import uuid

        # Create a new module with a unique name and add the `plugin` and `plugin_version` as attributes
        module_name = 'TestModule{}'.format(str(uuid.uuid4())[:5])
        dynamic_module = types.ModuleType(module_name, 'Dynamically created module for testing purposes')
        setattr(plugin, '__module__', dynamic_module.__name__)
        setattr(dynamic_module, plugin.__name__, plugin)

        # For tests that need to fail, this flag can be set to `False`
        if add_version:
            setattr(dynamic_module, '__version__', plugin_version)

        # Get the `DummyClass` plugin from the dynamically created test module
        dynamic_plugin = getattr(dynamic_module, plugin.__name__)

        # Make the dynamic module importable unless the test requests not to, to test an unimportable module
        if add_module_to_sys:
            sys.modules[dynamic_module.__name__] = dynamic_module

        return dynamic_plugin

    def test_external_module_import_fail(self):
        """Test that mapper does not except even if external module cannot be imported."""

        class DummyCalcJob():
            pass

        version_plugin = '0.1.01'
        dynamic_plugin = self.create_dynamic_plugin_module(DummyCalcJob, version_plugin, add_module_to_sys=False)

        expected_version = {'version': {'core': version_core}}
        self.assertEqual(self.provider.get_version_info(dynamic_plugin), expected_version)

    def test_external_module_no_version_attribute(self):
        """Test that mapper does not except even if external module does not define `__version__` attribute."""

        class DummyCalcJob():
            pass

        version_plugin = '0.1.02'
        dynamic_plugin = self.create_dynamic_plugin_module(DummyCalcJob, version_plugin, add_version=False)

        expected_version = {'version': {'core': version_core}}
        self.assertEqual(self.provider.get_version_info(dynamic_plugin), expected_version)

    def test_external_module_class(self):
        """Test the mapper works for a class from an external module."""

        class DummyCalcJob():
            pass

        version_plugin = '0.1.17'
        dynamic_plugin = self.create_dynamic_plugin_module(DummyCalcJob, version_plugin)

        expected_version = {'version': {'core': version_core, 'plugin': version_plugin}}
        self.assertEqual(self.provider.get_version_info(dynamic_plugin), expected_version)

    def test_external_module_function(self):
        """Test the mapper works for a function from an external module."""

        @calcfunction
        def test_calcfunction():
            return

        version_plugin = '0.2.19'
        dynamic_plugin = self.create_dynamic_plugin_module(test_calcfunction, version_plugin)

        expected_version = {'version': {'core': version_core, 'plugin': version_plugin}}
        self.assertEqual(self.provider.get_version_info(dynamic_plugin), expected_version)

    def test_calcfunction(self):
        """Test the mapper for a `calcfunction`."""

        @calcfunction
        def test_calcfunction():
            return

        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        self.assertEqual(self.provider.get_version_info(test_calcfunction), expected_version)

    def test_calc_job(self):
        """Test the mapper for a `CalcJob`."""
        AddArithmeticCalculation = CalculationFactory('arithmetic.add')  # pylint: disable=invalid-name

        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        self.assertEqual(self.provider.get_version_info(AddArithmeticCalculation), expected_version)

    def test_work_chain(self):
        """Test the mapper for a `WorkChain`."""

        class SomeWorkChain(WorkChain):
            """Need to create a dummy class since there is no built-in work chain with entry point in `aiida-core`."""

        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        self.assertEqual(self.provider.get_version_info(SomeWorkChain), expected_version)
