###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for utilities dealing with plugins and entry points."""

import pytest

from aiida import __version__ as version_core
from aiida.common.exceptions import EntryPointError
from aiida.engine import WorkChain, calcfunction
from aiida.plugins import CalculationFactory
from aiida.plugins.utils import PluginVersionProvider


@pytest.fixture
def provider():
    """Return an instance of the :class:`aiida.plugins.utils.PluginVersionProvider`."""
    return PluginVersionProvider()


@pytest.fixture
def create_dynamic_plugin_module():
    """Create a fake dynamic module with a certain `plugin` entity, a class or function and the given version."""

    def _factory(plugin, plugin_version, add_module_to_sys=True, add_version=True):
        import sys
        import types
        import uuid

        # Create a new module with a unique name and add the `plugin` and `plugin_version` as attributes
        module_name = f'TestModule{str(uuid.uuid4())[:5]}'
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

    return _factory


class TestPluginVersionProvider:
    """Tests for the :py:class:`~aiida.plugins.utils.PluginVersionProvider` utility class."""

    def test_external_module_import_fail(self, create_dynamic_plugin_module, provider):
        """Test that mapper does not except even if external module cannot be imported."""

        class DummyCalcJob:
            pass

        version_plugin = '0.1.01'
        dynamic_plugin = create_dynamic_plugin_module(DummyCalcJob, version_plugin, add_module_to_sys=False)

        expected_version = {'version': {'core': version_core}}
        assert provider.get_version_info(dynamic_plugin) == expected_version

    def test_external_module_no_version_attribute(self, create_dynamic_plugin_module, provider):
        """Test that mapper does not except even if external module does not define `__version__` attribute."""

        class DummyCalcJob:
            pass

        version_plugin = '0.1.02'
        dynamic_plugin = create_dynamic_plugin_module(DummyCalcJob, version_plugin, add_version=False)

        expected_version = {'version': {'core': version_core}}
        assert provider.get_version_info(dynamic_plugin) == expected_version

    def test_external_module_class(self, create_dynamic_plugin_module, provider):
        """Test the mapper works for a class from an external module."""

        class DummyCalcJob:
            pass

        version_plugin = '0.1.17'
        dynamic_plugin = create_dynamic_plugin_module(DummyCalcJob, version_plugin)

        expected_version = {'version': {'core': version_core, 'plugin': version_plugin}}
        assert provider.get_version_info(dynamic_plugin) == expected_version

    def test_external_module_function(self, create_dynamic_plugin_module, provider):
        """Test the mapper works for a function from an external module."""

        @calcfunction
        def test_calcfunction():
            return

        version_plugin = '0.2.19'
        dynamic_plugin = create_dynamic_plugin_module(test_calcfunction, version_plugin)

        expected_version = {'version': {'core': version_core, 'plugin': version_plugin}}
        assert provider.get_version_info(dynamic_plugin) == expected_version

    def test_calcfunction(self, provider):
        """Test the mapper for a `calcfunction`."""

        @calcfunction
        def test_calcfunction():
            return

        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        assert provider.get_version_info(test_calcfunction) == expected_version

    def test_calc_job(self, provider):
        """Test the mapper for a `CalcJob`."""
        AddArithmeticCalculation = CalculationFactory('core.arithmetic.add')  # noqa: N806

        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        assert provider.get_version_info(AddArithmeticCalculation) == expected_version

    def test_work_chain(self, provider):
        """Test the mapper for a `WorkChain`."""

        class SomeWorkChain(WorkChain):
            """Need to create a dummy class since there is no built-in work chain with entry point in `aiida-core`."""

        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        assert provider.get_version_info(SomeWorkChain) == expected_version

    def test_entry_point_string(self, provider):
        """Test passing an entry point string."""
        expected_version = {'version': {'core': version_core, 'plugin': version_core}}
        assert provider.get_version_info('aiida.calculations:core.arithmetic.add') == expected_version

    def test_entry_point_string_non_existant(self, provider):
        """Test passing an entry point string that doesn't exist."""
        with pytest.raises(EntryPointError, match=r'got string `.*` but could not load corresponding entry point'):
            provider.get_version_info('aiida.calculations:core.non_existing')
