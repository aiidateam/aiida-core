###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test AiiDA processes."""

import threading

import plumpy
import pytest
from plumpy.utils import AttributesFrozendict

from aiida import orm
from aiida.common.lang import override
from aiida.engine import ExitCode, ExitCodesNamespace, Process, run, run_get_node, run_get_pk
from aiida.engine.processes.ports import PortNamespace
from aiida.manage.caching import disable_caching, enable_caching
from aiida.orm import to_aiida_type
from aiida.orm.nodes.caching import NodeCaching
from aiida.plugins import CalculationFactory
from tests.utils import processes as test_processes


class NameSpacedProcess(Process):
    """Name spaced process."""

    _node_class = orm.WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('some.name.space.a', valid_type=orm.Int)


class TestProcessNamespace:
    """Test process namespace"""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    def test_namespaced_process(self):
        """Test that inputs in nested namespaces are properly validated and the link labels
        are properly formatted by connecting the namespaces with underscores.
        """
        proc = NameSpacedProcess(inputs={'some': {'name': {'space': {'a': orm.Int(5)}}}})

        # Test that the namespaced inputs are AttributesFrozenDicts
        assert isinstance(proc.inputs, AttributesFrozendict)
        assert isinstance(proc.inputs.some, AttributesFrozendict)
        assert isinstance(proc.inputs.some.name, AttributesFrozendict)
        assert isinstance(proc.inputs.some.name.space, AttributesFrozendict)

        # Test that the input node is in the inputs of the process
        input_node = proc.inputs.some.name.space.a
        assert isinstance(input_node, orm.Int)
        assert input_node.value == 5

        # Check that the link of the process node has the correct link name
        assert 'some__name__space__a' in proc.node.base.links.get_incoming().all_link_labels()
        assert proc.node.base.links.get_incoming().get_node_by_label('some__name__space__a') == 5
        assert proc.node.inputs.some.name.space.a == 5
        assert proc.node.inputs['some']['name']['space']['a'] == 5


class ProcessStackTest(Process):
    """Test process stack."""

    _node_class = orm.WorkflowNode

    @override
    async def run(self):
        pass

    @override
    def on_create(self):
        super().on_create()
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        """The therad must match the one used in on_create because process
        stack is using thread local storage to keep track of who called who.
        """
        super().on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess:
    """Test AiiDA process."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        assert Process.current() is None
        self.computer = aiida_localhost
        yield
        assert Process.current() is None

    @staticmethod
    def test_process_stack():
        run(ProcessStackTest)

    def test_inputs(self):
        with pytest.raises(ValueError):
            run(test_processes.BadOutput)

    def test_spec_metadata_property(self):
        """`Process.spec_metadata` should return the metadata port namespace of its spec."""
        assert isinstance(Process.spec_metadata, PortNamespace)
        assert Process.spec_metadata == Process.spec().inputs['metadata']

    def test_input_link_creation(self):
        """Test input link creation."""
        dummy_inputs = ['a', 'b', 'c', 'd']

        inputs = {string: orm.Str(string) for string in dummy_inputs}
        inputs['metadata'] = {'store_provenance': True}
        process = test_processes.DummyProcess(inputs)

        for entry in process.node.base.links.get_incoming().all():
            assert entry.link_label in inputs
            assert entry.link_label == entry.node.value
            dummy_inputs.remove(entry.link_label)

        # Make sure there are no other inputs
        assert not dummy_inputs

    @staticmethod
    def test_none_input():
        """Check that if we pass no input the process runs fine."""
        run(test_processes.DummyProcess)

    def test_input_after_stored(self):
        """Verify that adding an input link after storing a `ProcessNode` will raise because it is illegal."""
        from aiida.common import LinkType

        process = test_processes.DummyProcess()

        with pytest.raises(ValueError):
            process.node.base.links.add_incoming(orm.Int(1), link_type=LinkType.INPUT_WORK, link_label='illegal_link')

    def test_seal(self):
        _, p_k = run_get_pk(test_processes.DummyProcess)
        assert orm.load_node(pk=p_k).is_sealed

    def test_description(self):
        """Testing setting a process description."""
        dummy_process = test_processes.DummyProcess(inputs={'metadata': {'description': "Rockin' process"}})
        assert dummy_process.node.description == "Rockin' process"

        with pytest.raises(ValueError):
            test_processes.DummyProcess(inputs={'metadata': {'description': 5}})

    def test_label(self):
        """Test setting a label."""
        dummy_process = test_processes.DummyProcess(inputs={'metadata': {'label': 'My label'}})
        assert dummy_process.node.label == 'My label'

        with pytest.raises(ValueError):
            test_processes.DummyProcess(inputs={'label': 5})

    def test_work_calc_finish(self):
        process = test_processes.DummyProcess()
        assert not process.node.is_finished_ok
        run(process)
        assert process.node.is_finished_ok

    def test_on_finish_node_updated_before_broadcast(self, monkeypatch):
        """Tests if the process state and output has been updated in the database before a broadcast is invoked.

        In plumpy.Process.on_entered the state update is broadcasted. When a process is finished this results in the
        next process being run. If the next process will access the process that just finished, it can result in not
        being able to retrieve the outputs or correct process state because this information has yet not been updated
        them in the database.
        """
        import copy

        # By monkeypatching the parent class we can check the state when the
        # parents class method is invoked and check if the state has be
        # correctly updated.
        original_on_entered = copy.deepcopy(plumpy.Process.on_entered)

        def on_entered(self, from_state):
            if self._state.LABEL.value == 'finished':
                assert (
                    self.node.is_finished_ok
                ), 'Node state should have been updated before plumpy.Process.on_entered is invoked.'
                assert (
                    self.node.outputs.result.value == 2
                ), 'Outputs should have been attached before plumpy.Process.on_entered is invoked.'
            original_on_entered(self, from_state)

        monkeypatch.setattr(plumpy.Process, 'on_entered', on_entered)
        # Ensure that process has run correctly otherwise the asserts in the
        # monkeypatched member function have been skipped
        assert run_get_node(test_processes.AddProcess, a=1, b=1).node.is_finished_ok, 'Process should not fail.'

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
        ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')  # noqa: N806

        exit_codes = ArithmeticAddCalculation.exit_codes
        assert isinstance(exit_codes, ExitCodesNamespace)
        for _, value in exit_codes.items():
            assert isinstance(value, ExitCode)

        exit_statuses = ArithmeticAddCalculation.get_exit_statuses(['ERROR_NO_RETRIEVED_FOLDER'])
        assert isinstance(exit_statuses, list)
        for entry in exit_statuses:
            assert isinstance(entry, int)

        with pytest.raises(AttributeError):
            ArithmeticAddCalculation.get_exit_statuses(['NON_EXISTING_EXIT_CODE_LABEL'])

    def test_exit_codes_invalidate_cache(self):
        """Test that returning an exit code with 'invalidates_cache' set to ``True``
        indeed means that the ProcessNode will not be cached from.
        """
        # Sanity check that caching works when the exit code is not returned.
        with enable_caching():
            _, node1 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(False))
            _, node2 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(False))
            assert node1.base.extras.get('_aiida_hash') == node2.base.extras.get('_aiida_hash')
            assert NodeCaching.CACHED_FROM_KEY in node2.base.extras

        with enable_caching():
            _, node3 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(True))
            _, node4 = run_get_node(test_processes.InvalidateCaching, return_exit_code=orm.Bool(True))
            assert node3.base.extras.get('_aiida_hash') == node4.base.extras.get('_aiida_hash')
            assert NodeCaching.CACHED_FROM_KEY not in node4.base.extras

    def test_valid_cache_hook(self):
        """Test that the is_valid_cache behavior can be specified from
        the method in the Process sub-class.
        """
        # Sanity check that caching works when the hook returns True.
        with enable_caching():
            _, node1 = run_get_node(test_processes.IsValidCacheHook)
            _, node2 = run_get_node(test_processes.IsValidCacheHook)
            assert node1.base.extras.get('_aiida_hash') == node2.base.extras.get('_aiida_hash')
            assert NodeCaching.CACHED_FROM_KEY in node2.base.extras

        with enable_caching():
            _, node3 = run_get_node(test_processes.IsValidCacheHook, not_valid_cache=orm.Bool(True))
            _, node4 = run_get_node(test_processes.IsValidCacheHook, not_valid_cache=orm.Bool(True))
            assert node3.base.extras.get('_aiida_hash') == node4.base.extras.get('_aiida_hash')
            assert NodeCaching.CACHED_FROM_KEY not in node4.base.extras

    def test_process_type_with_entry_point(self):
        """For a process with a registered entry point, the process_type will be its formatted entry point string."""
        from aiida.orm import InstalledCode

        code = InstalledCode(computer=self.computer, filepath_executable='/bin/true').store()
        parameters = orm.Dict(dict={})
        template = orm.Dict(dict={})
        options = {
            'resources': {'num_machines': 1, 'tot_num_mpiprocs': 1},
            'max_wallclock_seconds': 1,
        }

        inputs = {
            'code': code,
            'parameters': parameters,
            'template': template,
            'metadata': {
                'options': options,
            },
        }

        entry_point = 'core.templatereplacer'
        process_class = CalculationFactory(entry_point)
        process = process_class(inputs=inputs)

        expected_process_type = f'aiida.calculations:{entry_point}'
        assert process.node.process_type == expected_process_type

        # Verify that process_class on the calculation node returns the original entry point class
        recovered_process = process.node.process_class
        assert recovered_process == process_class

    def test_process_type_without_entry_point(self):
        """For a process without a registered entry point, the process_type will fall back on the fully
        qualified class name
        """
        process = test_processes.DummyProcess()
        expected_process_type = f'{process.__class__.__module__}.{process.__class__.__name__}'
        assert process.node.process_type == expected_process_type

        # Verify that process_class on the calculation node returns the original entry point class
        recovered_process = process.node.process_class
        assert recovered_process == process.__class__

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

            async def run(self):
                self.out('namespace', self.inputs.namespace)

        results, node = run_get_node(TestProcess1, namespace={'alpha': orm.Int(1), 'beta': orm.Int(2)})

        assert node.is_finished_ok
        assert results['namespace']['alpha'] == orm.Int(1)
        assert results['namespace']['beta'] == orm.Int(2)

    def test_output_validation_error(self):
        """Test that a process is marked as failed if its output namespace validation fails."""

        class TestProcess1(Process):
            """Defining a new TestProcess class for testing."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('add_outputs', valid_type=orm.Bool, default=lambda: orm.Bool(False))
                spec.output_namespace('integer.namespace', valid_type=orm.Int, dynamic=True)
                spec.output('required_string', valid_type=orm.Str, required=True)

            async def run(self):
                if self.inputs.add_outputs:
                    self.out('required_string', orm.Str('testing').store())
                    self.out('integer.namespace.two', orm.Int(2).store())

        _, node = run_get_node(TestProcess1)

        # For default inputs, no outputs will be attached, causing the validation to fail at the end so an internal
        # exit status will be set, which is a negative integer
        assert node.is_finished
        assert not node.is_finished_ok
        assert node.exit_status == TestProcess1.exit_codes.ERROR_MISSING_OUTPUT.status
        assert node.exit_message == TestProcess1.exit_codes.ERROR_MISSING_OUTPUT.message

        # When settings `add_outputs` to True, the outputs should be added and validation should pass
        _, node = run_get_node(TestProcess1, add_outputs=orm.Bool(True))
        assert node.is_finished
        assert node.is_finished_ok
        assert node.exit_status == 0

    def test_exposed_outputs(self):
        """Test the ``Process.exposed_outputs`` method."""
        from aiida.common import AttributeDict
        from aiida.common.links import LinkType
        from aiida.engine.utils import instantiate_process
        from aiida.manage import get_manager

        runner = get_manager().get_runner()

        class ChildProcess(Process):
            """Dummy process with normal output and output namespace."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super(ChildProcess, cls).define(spec)
                spec.input('input', valid_type=orm.Int)
                spec.output('output', valid_type=orm.Int)
                spec.output('name.space', valid_type=orm.Int)

        class ParentProcess(Process):
            """Dummy process that exposes the outputs of ``ChildProcess``."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super(ParentProcess, cls).define(spec)
                spec.input('input', valid_type=orm.Int)
                spec.expose_outputs(ChildProcess)

        node_child = orm.WorkflowNode().store()
        node_output = orm.Int(1).store()
        node_output.base.links.add_incoming(node_child, link_label='output', link_type=LinkType.RETURN)
        node_name_space = orm.Int(1).store()
        node_name_space.base.links.add_incoming(node_child, link_label='name__space', link_type=LinkType.RETURN)

        process = instantiate_process(runner, ParentProcess, input=orm.Int(1))
        exposed_outputs = process.exposed_outputs(node_child, ChildProcess)

        expected = AttributeDict(
            {
                'name': {
                    'space': node_name_space,
                },
                'output': node_output,
            }
        )
        assert exposed_outputs == expected

    def test_exposed_outputs_non_existing_namespace(self):
        """Test the ``Process.exposed_outputs`` method for non-existing namespace."""
        from aiida.common.links import LinkType
        from aiida.engine.utils import instantiate_process
        from aiida.manage import get_manager

        runner = get_manager().get_runner()

        class ChildProcess(Process):
            """Dummy process with normal output and output namespace."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super(ChildProcess, cls).define(spec)
                spec.input('input', valid_type=orm.Int)
                spec.output('output', valid_type=orm.Int)
                spec.output('name.space', valid_type=orm.Int)

        class ParentProcess(Process):
            """Dummy process that exposes the outputs of ``ChildProcess``."""

            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super(ParentProcess, cls).define(spec)
                spec.input('input', valid_type=orm.Int)
                spec.expose_outputs(ChildProcess, namespace='child')

        node_child = orm.WorkflowNode().store()
        node_output = orm.Int(1).store()
        node_output.base.links.add_incoming(node_child, link_label='output', link_type=LinkType.RETURN)
        node_name_space = orm.Int(1).store()
        node_name_space.base.links.add_incoming(node_child, link_label='name__space', link_type=LinkType.RETURN)

        process = instantiate_process(runner, ParentProcess, input=orm.Int(1))

        # If the ``namespace`` does not exist, for example because it is slightly misspelled, a ``KeyError`` is raised
        with pytest.raises(KeyError):
            process.exposed_outputs(node_child, ChildProcess, namespace='cildh')

    def test_build_process_label(self):
        """Test the :meth:`~aiida.engine.processes.process.Process.build_process_label` method."""
        custom_process_label = 'custom_process_label'

        class CustomLabelProcess(Process):
            """Class that provides custom process label."""

            _node_class = orm.WorkflowNode

            def _build_process_label(self):
                return custom_process_label

        _, node = run_get_node(CustomLabelProcess)
        assert node.process_label == custom_process_label


class TestValidateDynamicNamespaceProcess(Process):
    """Simple process with dynamic input namespace."""

    _node_class = orm.WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.inputs.dynamic = True


def test_input_validation_storable_nodes():
    """Test that validation catches non-storable inputs even if nested in dictionary for dynamic namespace.

    Regression test for #5128.
    """
    with pytest.raises(ValueError):
        run(TestValidateDynamicNamespaceProcess, **{'namespace': {'a': 1}})


class TestNotRequiredNoneProcess(Process):
    """Process with an optional input port that should therefore also accept ``None``."""

    _node_class = orm.WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('valid_type', valid_type=orm.Int, required=False)
        spec.input('any_type', required=False)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_not_required_accepts_none():
    """Test that a port that is not required, accepts ``None``."""
    from aiida.engine.utils import instantiate_process
    from aiida.manage import get_manager

    runner = get_manager().get_runner()

    process = instantiate_process(runner, TestNotRequiredNoneProcess, valid_type=None, any_type=None)
    assert process.inputs.valid_type is None
    assert process.inputs.any_type is None

    process = instantiate_process(runner, TestNotRequiredNoneProcess, valid_type=orm.Int(1), any_type=orm.Bool(True))
    assert process.inputs.valid_type == orm.Int(1)
    assert process.inputs.any_type == orm.Bool(True)


class TestMetadataInputsProcess(Process):
    """Process with various ports that are ``is_metadata=True``."""

    _node_class = orm.WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('metadata_port', is_metadata=True)
        spec.input('metadata_port_non_serializable', is_metadata=True)
        spec.input_namespace('metadata_portnamespace', is_metadata=True)
        spec.input('metadata_portnamespace.with_default', default='default-value', is_metadata=True)
        spec.input('metadata_portnamespace.without_default', is_metadata=True)


def test_metadata_inputs(runner):
    """Test that explicitly passed ``is_metadata`` inputs are stored in the attributes.

    This is essential to make it possible to recreate a builder for the process with the original inputs.
    """
    inputs = {
        'metadata_port': 'value',
        'metadata_port_non_serializable': orm.Data().store(),
        'metadata_portnamespace': {'without_default': 100},
    }
    process = TestMetadataInputsProcess(runner=runner, inputs=inputs)

    # The ``is_metadata`` inputs should only have stored the "raw" inputs (so not including any defaults) and any inputs
    # that are not JSON-serializable should also have been filtered out.
    assert process.node.get_metadata_inputs() == {
        'metadata_port': 'value',
        'metadata_portnamespace': {'without_default': 100},
    }


class CachableProcess(Process):
    """Dummy process that defines a storable and cachable node class."""

    _node_class = orm.CalculationNode


@pytest.mark.usefixtures('aiida_profile_clean')
def test_metadata_disable_cache(runner, entry_points):
    """Test the ``metadata.disable_cache`` input."""
    from aiida.engine.processes import ProcessState

    entry_points.add(CachableProcess, 'aiida.workflows:core.dummy')

    # Create a ``ProcessNode`` instance that is a valid cache source
    process_original = CachableProcess(runner=runner)
    process_original.node.set_process_state(ProcessState.FINISHED)
    process_original.node.seal()
    assert process_original.node.base.caching.is_valid_cache

    # Cache is disabled, so node should not be cached
    with disable_caching():
        process = CachableProcess(runner=runner)
        assert not process.node.base.caching.is_created_from_cache

    # Cache is disabled, fact that ``disable_cache`` is explicitly set to ``False`` should not change anything
    with disable_caching():
        process = CachableProcess(runner=runner, inputs={'metadata': {'disable_cache': False}})
        assert not process.node.base.caching.is_created_from_cache

    # Cache is enabled, so node should be cached
    with enable_caching():
        process = CachableProcess(runner=runner)
        assert process.node.base.caching.is_created_from_cache

    # Cache is enabled, but ``disable_cache`` is explicitly set to ``False``, so node should not be cached
    with enable_caching():
        process = CachableProcess(runner=runner, inputs={'metadata': {'disable_cache': True}})
        assert not process.node.base.caching.is_created_from_cache


def custom_serializer():
    pass


class AutoSerializeProcess(Process):
    """Check the automatic assignment of ``to_aiida_type`` serializer."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('non_metadata_input')
        spec.input('metadata_input', is_metadata=True)
        spec.input('custom_input', serializer=custom_serializer)


def test_auto_default_serializer():
    """Test that all inputs ports automatically have ``to_aiida_type`` set as the serializer.

    Exceptions are if the port is a metadata port or it defines an explicit serializer
    """
    assert AutoSerializeProcess.spec().inputs['non_metadata_input'].serializer is to_aiida_type
    assert AutoSerializeProcess.spec().inputs['metadata_input'].serializer is None
    assert AutoSerializeProcess.spec().inputs['custom_input'].serializer is custom_serializer
