# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import MutableMapping

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import LinkType
from aiida.engine import WorkChain, Process
from aiida.plugins import CalculationFactory

DEFAULT_INT = 256


class TestWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(TestWorkChain, cls).define(spec)
        spec.input_namespace('dynamic.namespace', dynamic=True)
        spec.input('values', valid_type=orm.Int, help='Port name that overlaps with method of mutable mapping')
        spec.input('name.spaced', valid_type=orm.Int, help='Namespaced port')
        spec.input('name_spaced', valid_type=orm.Str, help='Not actually a namespaced port')
        spec.input('boolean', valid_type=orm.Bool, help='A pointless boolean')
        spec.input('default', valid_type=orm.Int, default=orm.Int(DEFAULT_INT).store())


class TestProcessBuilder(AiidaTestCase):

    def setUp(self):
        super(TestProcessBuilder, self).setUp()
        self.assertIsNone(Process.current())
        self.process_class = CalculationFactory('templatereplacer')
        self.builder = self.process_class.get_builder()
        self.builder_workchain = TestWorkChain.get_builder()
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
            'metadata': {'options': {}}
        }

    def tearDown(self):
        super(TestProcessBuilder, self).tearDown()
        self.assertIsNone(Process.current())

    def test_process_builder_attributes(self):
        """Check that the builder has all the input ports of the process class as attributes."""
        for name, port in self.process_class.spec().inputs.items():
            self.assertTrue(hasattr(self.builder, name))

    def test_process_builder_set_attributes(self):
        """Verify that setting attributes in builder works."""
        label = 'Test label'
        description = 'Test description'

        self.builder.metadata.label = label
        self.builder.metadata.description = description

        self.assertEquals(self.builder.metadata.label, label)
        self.assertEquals(self.builder.metadata.description, description)

    def test_dynamic_setters(self):
        """Verify that the attributes of the TestWorkChain can be set but defaults are not there."""
        self.builder_workchain.dynamic.namespace = self.inputs['dynamic']['namespace']
        self.builder_workchain.name.spaced = self.inputs['name']['spaced']
        self.builder_workchain.name_spaced = self.inputs['name_spaced']
        self.builder_workchain.boolean = self.inputs['boolean']
        self.assertEquals(self.builder_workchain, self.inputs)

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
        self.assertEquals(self.builder_workchain.dynamic.namespace, self.inputs['dynamic']['namespace'])
        self.assertEquals(self.builder_workchain.name.spaced, self.inputs['name']['spaced'])
        self.assertEquals(self.builder_workchain.name_spaced, self.inputs['name_spaced'])
        self.assertEquals(self.builder_workchain.boolean, self.inputs['boolean'])

    def test_dynamic_getters_doc_string(self):
        """Verify that getters have the correct docstring."""
        builder = TestWorkChain.get_builder()
        self.assertEquals(builder.__class__.name_spaced.__doc__, str(TestWorkChain.spec().inputs['name_spaced']))
        self.assertEquals(builder.__class__.boolean.__doc__, str(TestWorkChain.spec().inputs['boolean']))

    def test_builder_restart_work_chain(self):
        """Verify that nested namespaces imploded into flat link labels can be reconstructed into nested namespaces."""
        node = orm.WorkChainNode(process_type=TestWorkChain.build_process_type())
        node.add_incoming(self.inputs['dynamic']['namespace']['alp'], LinkType.INPUT_WORK, 'dynamic__namespace__alp')
        node.add_incoming(self.inputs['name']['spaced'], LinkType.INPUT_WORK, 'name__spaced')
        node.add_incoming(self.inputs['name_spaced'], LinkType.INPUT_WORK, 'name_spaced')
        node.add_incoming(self.inputs['boolean'], LinkType.INPUT_WORK, 'boolean')
        node.add_incoming(orm.Int(DEFAULT_INT).store(), LinkType.INPUT_WORK, 'default')
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
        self.assertEquals(builder.dynamic.namespace['alp'], self.inputs['dynamic']['namespace']['alp'])
        self.assertEquals(builder.name.spaced, self.inputs['name']['spaced'])
        self.assertEquals(builder.name_spaced, self.inputs['name_spaced'])
        self.assertEquals(builder.boolean, self.inputs['boolean'])
        self.assertEquals(builder.default, orm.Int(DEFAULT_INT))

    def test_port_names_overlapping_mutable_mapping_methods(self):
        """Check that port names take precedence over `collections.MutableMapping` methods.

        The `ProcessBuilderNamespace` is a `collections.MutableMapping` but since the port names are made accessible
        as attributes, they can overlap with some of the mappings builtin methods, e.g. `values()`, `items()` etc.
        The port names should take precendence in this case and if one wants to access the mapping methods one needs to
        cast the builder to a dictionary first.
        """
        builder = TestWorkChain.get_builder()

        # The `values` method is obscured by a port that also happens to be called `values`, so calling it should raise
        with self.assertRaises(TypeError):
            builder.values()

        # However, we can assign a node to it
        builder.values = orm.Int(2)

        # Calling the attribute `values` will then actually try to call the node, which should raise
        with self.assertRaises(TypeError):
            builder.values()

        # Casting the builder to a dict, *should* then make `values` callable again
        self.assertIn(orm.Int(2), dict(builder).values())

        # The mapping methods should not be auto-completed, i.e. not in the values returned by calling `dir`
        for method in [method for method in dir(MutableMapping) if method != 'values']:
            self.assertNotIn(method, dir(builder))

        # On the other hand, all the port names *should* be present
        for port_name in TestWorkChain.spec().inputs.keys():
            self.assertIn(port_name, dir(builder))

        # The `update` method is implemented, but prefixed with an underscore to not block the name for a port
        builder.update({'boolean': orm.Bool(False)})
        self.assertEqual(builder.boolean, orm.Bool(False))

    def test_calc_job_node_get_builder_restart(self):
        """Test the `CalcJobNode.get_builder_restart` method."""
        original = orm.CalcJobNode(computer=self.computer, process_type='aiida.calculations:arithmetic.add', label='original')
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
        self.assertEquals(builder.x, orm.Int(1))
        self.assertEquals(builder.y, orm.Int(2))
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
        self.assertEquals(builder.code.pk, code.pk)

        # Check that I can set the parameters
        builder.parameters = orm.Dict(dict={})

        # Check that it complains for an unknown input
        with self.assertRaises(AttributeError):
            builder.unknown_parameter = 3

        # Check that it complains if the type is not the correct one (for the templatereplacer, it should be a Dict)
        with self.assertRaises(ValueError):
            builder.parameters = orm.Int(3)
