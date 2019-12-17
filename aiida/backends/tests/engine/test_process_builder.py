# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test process builder."""
# pylint: disable=no-member,protected-access,no-name-in-module
from collections.abc import Mapping, MutableMapping

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import LinkType
from aiida.engine import WorkChain, Process
from aiida.plugins import CalculationFactory

DEFAULT_INT = 256


class ExampleWorkChain(WorkChain):
    """Defining test work chain."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('dynamic.namespace', dynamic=True)
        spec.input('values', valid_type=orm.Int, help='Port name that overlaps with method of mutable mapping')
        spec.input('name.spaced', valid_type=orm.Int, help='Namespaced port')
        spec.input('name_spaced', valid_type=orm.Str, help='Not actually a namespaced port')
        spec.input('boolean', valid_type=orm.Bool, help='A pointless boolean')
        spec.input('default', valid_type=orm.Int, default=orm.Int(DEFAULT_INT).store())


class LazyProcessNamespace(Process):
    """Process with basic nested namespaces to test "pruning" of empty nested namespaces from the builder."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('namespace')
        spec.input_namespace('namespace.nested')
        spec.input('namespace.nested.bird')
        spec.input('namespace.a')
        spec.input('namespace.c')


class MappingData(Mapping, orm.Data):
    """Data sub class that is also a `Mapping`."""

    def __init__(self, data=None):
        super().__init__()
        if data is None:
            data = {}
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class TestProcessBuilder(AiidaTestCase):
    """Test process builder.    """

    def setUp(self):
        super().setUp()
        self.assertIsNone(Process.current())
        self.process_class = CalculationFactory('templatereplacer')
        self.builder = self.process_class.get_builder()
        self.builder_workchain = ExampleWorkChain.get_builder()
        self.inputs = {
            'dynamic': {
                'namespace': {
                    'alp': orm.Int(1).store()
                }
            },
            'name': {
                'spaced': orm.Int(1).store(),
            },
            'name_spaced': orm.Str('underscored').store(),
            'boolean': orm.Bool(True).store(),
            'metadata': {}
        }

    def tearDown(self):
        super().tearDown()
        self.assertIsNone(Process.current())

    def test_builder_inputs(self):
        """Test the `ProcessBuilder._inputs` method to get the inputs with and without `prune` set to True."""
        builder = LazyProcessNamespace.get_builder()

        # When no inputs are specified specifically, `prune=True` should get rid of completely empty namespaces
        self.assertEqual(builder._inputs(prune=False), {'namespace': {'nested': {}}, 'metadata': {}})
        self.assertEqual(builder._inputs(prune=True), {})

        # With a specific input in `namespace` the case of `prune=True` should now only remove `metadata`
        integer = orm.Int(DEFAULT_INT)
        builder = LazyProcessNamespace.get_builder()
        builder.namespace.a = integer
        self.assertEqual(builder._inputs(prune=False), {'namespace': {'a': integer, 'nested': {}}, 'metadata': {}})
        self.assertEqual(builder._inputs(prune=True), {'namespace': {'a': integer}})

        # A value that is a `Node` instance but also happens to be an "empty mapping" should not be pruned
        empty_node = MappingData()
        builder = LazyProcessNamespace.get_builder()
        builder.namespace.a = empty_node
        self.assertEqual(builder._inputs(prune=False), {'namespace': {'a': empty_node, 'nested': {}}, 'metadata': {}})
        self.assertEqual(builder._inputs(prune=True), {'namespace': {'a': empty_node}})

        # Verify that empty lists are considered as a "value" and are not pruned
        builder = LazyProcessNamespace.get_builder()
        builder.namespace.c = list()
        self.assertEqual(builder._inputs(prune=False), {'namespace': {'c': [], 'nested': {}}, 'metadata': {}})
        self.assertEqual(builder._inputs(prune=True), {'namespace': {'c': []}})

        # Verify that empty lists, even in doubly nested namespace are considered as a "value" and are not pruned
        builder = LazyProcessNamespace.get_builder()
        builder.namespace.nested.bird = list()
        self.assertEqual(builder._inputs(prune=False), {'namespace': {'nested': {'bird': []}}, 'metadata': {}})
        self.assertEqual(builder._inputs(prune=True), {'namespace': {'nested': {'bird': []}}})

    def test_process_builder_attributes(self):
        """Check that the builder has all the input ports of the process class as attributes."""
        for name, _ in self.process_class.spec().inputs.items():
            self.assertTrue(hasattr(self.builder, name))

    def test_process_builder_set_attributes(self):
        """Verify that setting attributes in builder works."""
        label = 'Test label'
        description = 'Test description'

        self.builder.metadata.label = label
        self.builder.metadata.description = description

        self.assertEqual(self.builder.metadata.label, label)
        self.assertEqual(self.builder.metadata.description, description)

    def test_dynamic_setters(self):
        """Verify that the attributes of the DummyWorkChain can be set but defaults are not there."""
        self.builder_workchain.dynamic.namespace = self.inputs['dynamic']['namespace']
        self.builder_workchain.name.spaced = self.inputs['name']['spaced']
        self.builder_workchain.name_spaced = self.inputs['name_spaced']
        self.builder_workchain.boolean = self.inputs['boolean']
        self.assertEqual(self.builder_workchain, self.inputs)

    def test_dynamic_getters_value(self):
        """Verify that getters will return the actual value."""
        self.builder_workchain.dynamic.namespace = self.inputs['dynamic']['namespace']
        self.builder_workchain.name.spaced = self.inputs['name']['spaced']
        self.builder_workchain.name_spaced = self.inputs['name_spaced']
        self.builder_workchain.boolean = self.inputs['boolean']

        # Verify that the correct type is returned by the getter
        self.assertTrue(isinstance(self.builder_workchain.dynamic.namespace, dict))
        self.assertTrue(isinstance(self.builder_workchain.name.spaced, orm.Int))
        self.assertTrue(isinstance(self.builder_workchain.name_spaced, orm.Str))
        self.assertTrue(isinstance(self.builder_workchain.boolean, orm.Bool))

        # Verify that the correct value is returned by the getter
        self.assertEqual(self.builder_workchain.dynamic.namespace, self.inputs['dynamic']['namespace'])
        self.assertEqual(self.builder_workchain.name.spaced, self.inputs['name']['spaced'])
        self.assertEqual(self.builder_workchain.name_spaced, self.inputs['name_spaced'])
        self.assertEqual(self.builder_workchain.boolean, self.inputs['boolean'])

    def test_dynamic_getters_doc_string(self):
        """Verify that getters have the correct docstring."""
        builder = ExampleWorkChain.get_builder()
        self.assertEqual(builder.__class__.name_spaced.__doc__, str(ExampleWorkChain.spec().inputs['name_spaced']))
        self.assertEqual(builder.__class__.boolean.__doc__, str(ExampleWorkChain.spec().inputs['boolean']))

    def test_builder_restart_work_chain(self):
        """Verify that nested namespaces imploded into flat link labels can be reconstructed into nested namespaces."""
        caller = orm.WorkChainNode().store()

        node = orm.WorkChainNode(process_type=ExampleWorkChain.build_process_type())
        node.add_incoming(self.inputs['dynamic']['namespace']['alp'], LinkType.INPUT_WORK, 'dynamic__namespace__alp')
        node.add_incoming(self.inputs['name']['spaced'], LinkType.INPUT_WORK, 'name__spaced')
        node.add_incoming(self.inputs['name_spaced'], LinkType.INPUT_WORK, 'name_spaced')
        node.add_incoming(self.inputs['boolean'], LinkType.INPUT_WORK, 'boolean')
        node.add_incoming(orm.Int(DEFAULT_INT).store(), LinkType.INPUT_WORK, 'default')
        node.add_incoming(caller, link_type=LinkType.CALL_WORK, link_label='CALL_WORK')
        node.store()

        builder = node.get_builder_restart()
        self.assertIn('dynamic', builder)
        self.assertIn('namespace', builder.dynamic)
        self.assertIn('alp', builder.dynamic.namespace)
        self.assertIn('name', builder)
        self.assertIn('spaced', builder.name)
        self.assertIn('name_spaced', builder)
        self.assertIn('boolean', builder)
        self.assertIn('default', builder)
        self.assertEqual(builder.dynamic.namespace['alp'], self.inputs['dynamic']['namespace']['alp'])
        self.assertEqual(builder.name.spaced, self.inputs['name']['spaced'])
        self.assertEqual(builder.name_spaced, self.inputs['name_spaced'])
        self.assertEqual(builder.boolean, self.inputs['boolean'])
        self.assertEqual(builder.default, orm.Int(DEFAULT_INT))

    def test_port_names_overlapping_mutable_mapping_methods(self):  # pylint: disable=invalid-name
        """Check that port names take precedence over `collections.MutableMapping` methods.

        The `ProcessBuilderNamespace` is a `collections.MutableMapping` but since the port names are made accessible
        as attributes, they can overlap with some of the mappings builtin methods, e.g. `values()`, `items()` etc.
        The port names should take precendence in this case and if one wants to access the mapping methods one needs to
        cast the builder to a dictionary first."""
        builder = ExampleWorkChain.get_builder()

        # The `values` method is obscured by a port that also happens to be called `values`, so calling it should raise
        with self.assertRaises(TypeError):
            builder.values()  # pylint: disable=not-callable

        # However, we can assign a node to it
        builder.values = orm.Int(2)

        # Calling the attribute `values` will then actually try to call the node, which should raise
        with self.assertRaises(TypeError):
            builder.values()  # pylint: disable=not-callable

        # Casting the builder to a dict, *should* then make `values` callable again
        self.assertIn(orm.Int(2), dict(builder).values())

        # The mapping methods should not be auto-completed, i.e. not in the values returned by calling `dir`
        for method in [method for method in dir(MutableMapping) if method != 'values']:
            self.assertNotIn(method, dir(builder))

        # On the other hand, all the port names *should* be present
        for port_name in ExampleWorkChain.spec().inputs.keys():
            self.assertIn(port_name, dir(builder))

        # The `update` method is implemented, but prefixed with an underscore to not block the name for a port
        builder.update({'boolean': orm.Bool(False)})
        self.assertEqual(builder.boolean, orm.Bool(False))

    def test_calc_job_node_get_builder_restart(self):
        """Test the `CalcJobNode.get_builder_restart` method."""
        original = orm.CalcJobNode(
            computer=self.computer, process_type='aiida.calculations:arithmetic.add', label='original'
        )
        original.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        original.set_option('max_wallclock_seconds', 1800)

        original.add_incoming(orm.Int(1).store(), link_type=LinkType.INPUT_CALC, link_label='x')
        original.add_incoming(orm.Int(2).store(), link_type=LinkType.INPUT_CALC, link_label='y')
        original.store()

        builder = original.get_builder_restart()

        self.assertIn('x', builder)
        self.assertIn('y', builder)
        self.assertIn('metadata', builder)
        self.assertIn('options', builder.metadata)
        self.assertEqual(builder.x, orm.Int(1))
        self.assertEqual(builder.y, orm.Int(2))
        self.assertDictEqual(builder.metadata.options, original.get_options())

    def test_code_get_builder(self):
        """Test that the `Code.get_builder` method returns a builder where the code is already set."""
        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = 'test_code'
        code.set_input_plugin_name('templatereplacer')
        code.store()

        # Check that I can get a builder
        builder = code.get_builder()
        self.assertEqual(builder.code.pk, code.pk)

        # Check that I can set the parameters
        builder.parameters = orm.Dict(dict={})

        # Check that it complains for an unknown input
        with self.assertRaises(AttributeError):
            builder.unknown_parameter = 3

        # Check that it complains if the type is not the correct one (for the templatereplacer, it should be a Dict)
        with self.assertRaises(ValueError):
            builder.parameters = orm.Int(3)
