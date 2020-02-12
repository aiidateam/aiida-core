# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-member
"""Module to test AiiDA processes."""
import threading

import plumpy
from plumpy.utils import AttributesFrozendict

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.lang import override
from aiida.engine import ExitCode, ExitCodesNamespace, Process, run, run_get_pk, run_get_node
from aiida.engine.processes.ports import PortNamespace
from aiida.manage.caching import enable_caching
from aiida.plugins import CalculationFactory

from tests.utils import processes as test_processes


class NameSpacedProcess(Process):
    """Name spaced process."""

    _node_class = orm.WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('some.name.space.a', valid_type=orm.Int)


class TestProcessNamespace(AiidaTestCase):
    """Test process namespace"""

    def setUp(self):
        super().setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super().tearDown()
        self.assertIsNone(Process.current())

    def test_namespaced_process(self):
        """Test that inputs in nested namespaces are properly validated and the link labels
        are properly formatted by connecting the namespaces with underscores."""
        proc = NameSpacedProcess(inputs={'some': {'name': {'space': {'a': orm.Int(5)}}}})

        # Test that the namespaced inputs are AttributesFrozenDicts
        self.assertIsInstance(proc.inputs, AttributesFrozendict)
        self.assertIsInstance(proc.inputs.some, AttributesFrozendict)
        self.assertIsInstance(proc.inputs.some.name, AttributesFrozendict)
        self.assertIsInstance(proc.inputs.some.name.space, AttributesFrozendict)

        # Test that the input node is in the inputs of the process
        input_node = proc.inputs.some.name.space.a
        self.assertTrue(isinstance(input_node, orm.Int))
        self.assertEqual(input_node.value, 5)

        # Check that the link of the process node has the correct link name
        self.assertTrue('some__name__space__a' in proc.node.get_incoming().all_link_labels())
        self.assertEqual(proc.node.get_incoming().get_node_by_label('some__name__space__a'), 5)


class ProcessStackTest(Process):
    """Test process stack."""

    _node_class = orm.WorkflowNode

    @override
    def run(self):
        pass

    @override
    def on_create(self):
        # pylint: disable=attribute-defined-outside-init
        super().on_create()
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        """The therad must match the one used in on_create because process
        stack is using thread local storage to keep track of who called who."""
        super().on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(AiidaTestCase):
    """Test AiiDA process."""

    def setUp(self):
        super().setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super().tearDown()
        self.assertIsNone(Process.current())

    @staticmethod
    def test_process_stack():
        run(ProcessStackTest)

    def test_inputs(self):
        with self.assertRaises(ValueError):
            run(test_processes.BadOutput)

    def test_spec_metadata_property(self):
        """`Process.spec_metadata` should return the metadata port namespace of its spec."""
        self.assertIsInstance(Process.spec_metadata, PortNamespace)
        self.assertEqual(Process.spec_metadata, Process.spec().inputs['metadata'])

    def test_input_link_creation(self):
        """Test input link creation."""
        dummy_inputs = ['a', 'b', 'c', 'd']

        inputs = {string: orm.Str(string) for string in dummy_inputs}
        inputs['metadata'] = {'store_provenance': True}
        process = test_processes.DummyProcess(inputs)

        for entry in process.node.get_incoming().all():
            self.assertTrue(entry.link_label in inputs)
            self.assertEqual(entry.link_label, entry.node.value)
            dummy_inputs.remove(entry.link_label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

    @staticmethod
    def test_none_input():
        """Check that if we pass no input the process runs fine."""
        run(test_processes.DummyProcess)

    def test_input_after_stored(self):
        """Verify that adding an input link after storing a `ProcessNode` will raise because it is illegal."""
        from aiida.common import LinkType
        process = test_processes.DummyProcess()

        with self.assertRaises(ValueError):
            process.node.add_incoming(orm.Int(1), link_type=LinkType.INPUT_WORK, link_label='illegal_link')

    def test_seal(self):
        _, p_k = run_get_pk(test_processes.DummyProcess)
        self.assertTrue(orm.load_node(pk=p_k).is_sealed)

    def test_description(self):
        """Testing setting a process description."""
        dummy_process = test_processes.DummyProcess(inputs={'metadata': {'description': "Rockin' process"}})
        self.assertEqual(dummy_process.node.description, "Rockin' process")

        with self.assertRaises(ValueError):
            test_processes.DummyProcess(inputs={'metadata': {'description': 5}})

    def test_label(self):
        """Test setting a label."""
        dummy_process = test_processes.DummyProcess(inputs={'metadata': {'label': 'My label'}})
        self.assertEqual(dummy_process.node.label, 'My label')

        with self.assertRaises(ValueError):
            test_processes.DummyProcess(inputs={'label': 5})

    def test_work_calc_finish(self):
        process = test_processes.DummyProcess()
        self.assertFalse(process.node.is_finished_ok)
        run(process)
        self.assertTrue(process.node.is_finished_ok)

    @staticmethod
    def test_save_instance_state():
        """Test save instance's state."""
        proc = test_processes.DummyProcess()
        # Save the instance state
        bundle = plumpy.Bundle(proc)
        proc.close()
        bundle.unbundle()

    def test_exit_codes(self):
        """Test the properties to return various (sub) sets of existing exit codes."""
        ArithmeticAddCalculation = CalculationFactory('arithmetic.add')  # pylint: disable=invalid-name

        exit_codes = ArithmeticAddCalculation.exit_codes
        self.assertIsInstance(exit_codes, ExitCodesNamespace)
        for _, value in exit_codes.items():
            self.assertIsInstance(value, ExitCode)

        exit_statuses = ArithmeticAddCalculation.get_exit_statuses(['ERROR_NO_RETRIEVED_FOLDER'])
        self.assertIsInstance(exit_statuses, list)
        for entry in exit_statuses:
            self.assertIsInstance(entry, int)

        with self.assertRaises(AttributeError):
            ArithmeticAddCalculation.get_exit_statuses(['NON_EXISTING_EXIT_CODE_LABEL'])

    def test_exit_codes_invalidate_cache(self):
        """
        Test that returning an exit code with 'invalidates_cache' set to ``True``
        indeed means that the ProcessNode will not be cached from.
        """
        # Sanity check that caching works when the exit code is not returned.
        with enable_caching():
            _, node1 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(False))
            _, node2 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(False))
            self.assertEqual(node1.get_extra('_aiida_hash'), node2.get_extra('_aiida_hash'))
            self.assertIn('_aiida_cached_from', node2.extras)

        with enable_caching():
            _, node3 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(True))
            _, node4 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(True))
            self.assertEqual(node3.get_extra('_aiida_hash'), node4.get_extra('_aiida_hash'))
            self.assertNotIn('_aiida_cached_from', node4.extras)

    def test_valid_cache_hook(self):
        """
        Test that the is_valid_cache behavior can be specified from
        the method in the Process sub-class.
        """
        # Sanity check that caching works when the hook returns True.
        with enable_caching():
            _, node1 = run_get_node(test_processes.IsValidCacheHook)
            _, node2 = run_get_node(test_processes.IsValidCacheHook)
            self.assertEqual(node1.get_extra('_aiida_hash'), node2.get_extra('_aiida_hash'))
            self.assertIn('_aiida_cached_from', node2.extras)

        with enable_caching():
            _, node3 = run_get_node(test_processes.IsValidCacheHook, not_valid_cache=orm.Bool(True))
            _, node4 = run_get_node(test_processes.IsValidCacheHook, not_valid_cache=orm.Bool(True))
            self.assertEqual(node3.get_extra('_aiida_hash'), node4.get_extra('_aiida_hash'))
            self.assertNotIn('_aiida_cached_from', node4.extras)

    def test_process_type_with_entry_point(self):
        """For a process with a registered entry point, the process_type will be its formatted entry point string."""
        from aiida.orm import Code

        code = Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.store()

        parameters = orm.Dict(dict={})
        template = orm.Dict(dict={})
        options = {
            'resources': {
                'num_machines': 1,
                'tot_num_mpiprocs': 1
            },
            'max_wallclock_seconds': 1,
        }

        inputs = {
            'code': code,
            'parameters': parameters,
            'template': template,
            'metadata': {
                'options': options,
            }
        }

        entry_point = 'templatereplacer'
        process_class = CalculationFactory(entry_point)
        process = process_class(inputs=inputs)

        expected_process_type = 'aiida.calculations:{}'.format(entry_point)
        self.assertEqual(process.node.process_type, expected_process_type)

        # Verify that process_class on the calculation node returns the original entry point class
        recovered_process = process.node.process_class
        self.assertEqual(recovered_process, process_class)

    def test_process_type_without_entry_point(self):
        """
        For a process without a registered entry point, the process_type will fall back on the fully
        qualified class name
        """
        process = test_processes.DummyProcess()
        expected_process_type = '{}.{}'.format(process.__class__.__module__, process.__class__.__name__)
        self.assertEqual(process.node.process_type, expected_process_type)

        # Verify that process_class on the calculation node returns the original entry point class
        recovered_process = process.node.process_class
        self.assertEqual(recovered_process, process.__class__)

    def test_output_dictionary(self):
        """Verify that a dictionary can be passed as an output for a namespace."""

        class TestProcess1(Process):
            """Defining a new TestProcess class for testing."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input_namespace('namespace', valid_type=orm.Int, dynamic=True)
                spec.output_namespace('namespace', valid_type=orm.Int, dynamic=True)

            def run(self):
                self.out('namespace', self.inputs.namespace)

        results, node = run_get_node(TestProcess1, namespace={'alpha': orm.Int(1), 'beta': orm.Int(2)})

        self.assertTrue(node.is_finished_ok)
        self.assertEqual(results['namespace']['alpha'], orm.Int(1))
        self.assertEqual(results['namespace']['beta'], orm.Int(2))

    def test_output_validation_error(self):
        """Test that a process is marked as failed if its output namespace validation fails."""

        class TestProcess1(Process):
            """Defining a new TestProcess class for testing."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('add_outputs', valid_type=orm.Bool, default=orm.Bool(False))
                spec.output_namespace('integer.namespace', valid_type=orm.Int, dynamic=True)
                spec.output('required_string', valid_type=orm.Str, required=True)

            def run(self):
                if self.inputs.add_outputs:
                    self.out('required_string', orm.Str('testing').store())
                    self.out('integer.namespace.two', orm.Int(2).store())

        _, node = run_get_node(TestProcess1)

        # For default inputs, no outputs will be attached, causing the validation to fail at the end so an internal
        # exit status will be set, which is a negative integer
        self.assertTrue(node.is_finished)
        self.assertFalse(node.is_finished_ok)
        self.assertEqual(node.exit_status, TestProcess1.exit_codes.ERROR_MISSING_OUTPUT.status)
        self.assertEqual(node.exit_message, TestProcess1.exit_codes.ERROR_MISSING_OUTPUT.message)

        # When settings `add_outputs` to True, the outputs should be added and validation should pass
        _, node = run_get_node(TestProcess1, add_outputs=orm.Bool(True))
        self.assertTrue(node.is_finished)
        self.assertTrue(node.is_finished_ok)
        self.assertEqual(node.exit_status, 0)
