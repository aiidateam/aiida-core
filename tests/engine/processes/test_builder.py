###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.builder.ProcessBuilder`."""

import textwrap
from collections.abc import Mapping, MutableMapping

import pytest
from IPython.lib.pretty import pretty

from aiida import orm
from aiida.common import LinkType
from aiida.engine import Process, WorkChain, run_get_node
from aiida.engine.processes.builder import ProcessBuilderNamespace
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
        spec.input('dict', valid_type=orm.Dict, help='A pointless dict', required=False)
        spec.input('default', valid_type=orm.Int, default=lambda: orm.Int(DEFAULT_INT).store())


class LazyProcessNamespace(Process):
    """Process with basic nested namespaces to test "pruning" of empty nested namespaces from the builder."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('namespace', non_db=True)
        spec.input_namespace('namespace.nested', non_db=True)
        spec.input('namespace.nested.bird', non_db=True)
        spec.input('namespace.a', non_db=True)
        spec.input('namespace.c', non_db=True)


class SimpleProcessNamespace(Process):
    """Process with basic nested namespaces to test "pruning" of empty nested namespaces from the builder."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('namespace.nested', dynamic=True, non_db=True)
        spec.input('namespace.a', valid_type=int, non_db=True)
        spec.input('namespace.c', valid_type=dict, non_db=True)


class NestedNamespaceProcess(Process):
    """Process with nested required ports to check the update and merge functionality."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('nested.namespace.int', valid_type=int, required=True, non_db=True)
        spec.input('nested.namespace.float', valid_type=float, required=True, non_db=True)
        spec.input('nested.namespace.str', valid_type=str, required=False, non_db=True)
        spec.input_namespace('opt', required=False, dynamic=True)


class MappingData(Mapping, orm.Data):  # type: ignore[misc]
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


@pytest.fixture()
def example_inputs():
    return {
        'dynamic': {'namespace': {'alp': orm.Int(1).store()}},
        'name': {
            'spaced': orm.Int(1).store(),
        },
        'name_spaced': orm.Str('underscored').store(),
        'dict': orm.Dict({'a': 1, 'b': {'c': 2}}),
        'boolean': orm.Bool(True).store(),
        'metadata': {},
    }


def test_builder_inputs():
    """Test the `ProcessBuilder._inputs` method to get the inputs with and without `prune` set to True."""
    builder = LazyProcessNamespace.get_builder()

    # When no inputs are specified specifically, `prune=True` should get rid of completely empty namespaces
    assert builder._inputs(prune=False) == {'namespace': {'nested': {}}, 'metadata': {}}
    assert not builder._inputs(prune=True)

    # With a specific input in `namespace` the case of `prune=True` should now only remove `metadata`
    integer = orm.Int(DEFAULT_INT)
    builder = LazyProcessNamespace.get_builder()
    builder.namespace.a = integer
    assert builder._inputs(prune=False) == {'namespace': {'a': integer, 'nested': {}}, 'metadata': {}}
    assert builder._inputs(prune=True) == {'namespace': {'a': integer}}

    # A value that is a `Node` instance but also happens to be an "empty mapping" should not be pruned
    empty_node = MappingData()
    builder = LazyProcessNamespace.get_builder()
    builder.namespace.a = empty_node
    assert builder._inputs(prune=False) == {'namespace': {'a': empty_node, 'nested': {}}, 'metadata': {}}
    assert builder._inputs(prune=True) == {'namespace': {'a': empty_node}}

    # Verify that empty lists are considered as a "value" and are not pruned
    builder = LazyProcessNamespace.get_builder()
    builder.namespace.c = []
    assert builder._inputs(prune=False) == {'namespace': {'c': [], 'nested': {}}, 'metadata': {}}
    assert builder._inputs(prune=True) == {'namespace': {'c': []}}

    # Verify that empty lists, even in doubly nested namespace are considered as a "value" and are not pruned
    builder = LazyProcessNamespace.get_builder()
    builder.namespace.nested.bird = []
    assert builder._inputs(prune=False) == {'namespace': {'nested': {'bird': []}}, 'metadata': {}}
    assert builder._inputs(prune=True) == {'namespace': {'nested': {'bird': []}}}


@pytest.mark.parametrize(
    'process_class',
    [
        ExampleWorkChain,
        LazyProcessNamespace,
        SimpleProcessNamespace,
        NestedNamespaceProcess,
        CalculationFactory('core.templatereplacer'),
        CalculationFactory('core.arithmetic.add'),
        CalculationFactory('core.transfer'),
    ],
)
def test_process_builder_attributes(process_class):
    """Check that the builder has all the input ports of the process class as attributes."""
    builder = process_class.get_builder()
    for name, _ in process_class.spec().inputs.items():
        assert hasattr(builder, name)


def test_process_builder_set_attributes():
    """Verify that setting attributes in builder works."""
    builder = ExampleWorkChain.get_builder()
    label = 'Test label'
    description = 'Test description'

    builder.metadata.label = label
    builder.metadata.description = description

    assert builder.metadata.label == label
    assert builder.metadata.description == description


def test_dynamic_setters(example_inputs):
    """Verify that the attributes of the ExampleWorkChain can be set but defaults are not there."""
    builder = ExampleWorkChain.get_builder()
    builder.dynamic.namespace = example_inputs['dynamic']['namespace']
    builder.name.spaced = example_inputs['name']['spaced']
    builder.name_spaced = example_inputs['name_spaced']
    builder.boolean = example_inputs['boolean']
    builder.dict = example_inputs['dict']
    assert builder == example_inputs


def test_dynamic_getters_value(example_inputs):
    """Verify that getters will return the actual value."""
    builder = ExampleWorkChain.get_builder()
    builder.dynamic.namespace = example_inputs['dynamic']['namespace']
    builder.name.spaced = example_inputs['name']['spaced']
    builder.name_spaced = example_inputs['name_spaced']
    builder.boolean = example_inputs['boolean']

    # Verify that the correct type is returned by the getter
    assert isinstance(builder.dynamic.namespace, ProcessBuilderNamespace)
    assert isinstance(builder.name.spaced, orm.Int)
    assert isinstance(builder.name_spaced, orm.Str)
    assert isinstance(builder.boolean, orm.Bool)

    # Verify that the correct value is returned by the getter
    assert builder.dynamic.namespace == example_inputs['dynamic']['namespace']
    assert builder.name.spaced == example_inputs['name']['spaced']
    assert builder.name_spaced == example_inputs['name_spaced']
    assert builder.boolean == example_inputs['boolean']


def test_dynamic_getters_doc_string():
    """Verify that getters have the correct docstring."""
    builder = ExampleWorkChain.get_builder()
    assert builder.__class__.name_spaced.__doc__ == str(ExampleWorkChain.spec().inputs['name_spaced'])
    assert builder.__class__.boolean.__doc__ == str(ExampleWorkChain.spec().inputs['boolean'])


def test_builder_restart_work_chain(example_inputs):
    """Verify that nested namespaces imploded into flat link labels can be reconstructed into nested namespaces."""
    caller = orm.WorkChainNode().store()

    node = orm.WorkChainNode(process_type=ExampleWorkChain.build_process_type())
    node.base.links.add_incoming(
        example_inputs['dynamic']['namespace']['alp'], LinkType.INPUT_WORK, 'dynamic__namespace__alp'
    )
    node.base.links.add_incoming(example_inputs['name']['spaced'], LinkType.INPUT_WORK, 'name__spaced')
    node.base.links.add_incoming(example_inputs['name_spaced'], LinkType.INPUT_WORK, 'name_spaced')
    node.base.links.add_incoming(example_inputs['boolean'], LinkType.INPUT_WORK, 'boolean')
    node.base.links.add_incoming(orm.Int(DEFAULT_INT).store(), LinkType.INPUT_WORK, 'default')
    node.base.links.add_incoming(caller, link_type=LinkType.CALL_WORK, link_label='CALL_WORK')
    node.store()

    builder = node.get_builder_restart()
    assert 'dynamic' in builder
    assert 'namespace' in builder.dynamic
    assert 'alp' in builder.dynamic.namespace
    assert 'name' in builder
    assert 'spaced' in builder.name
    assert 'name_spaced' in builder
    assert 'boolean' in builder
    assert 'default' in builder
    assert builder.dynamic.namespace['alp'] == example_inputs['dynamic']['namespace']['alp']
    assert builder.name.spaced == example_inputs['name']['spaced']
    assert builder.name_spaced == example_inputs['name_spaced']
    assert builder.boolean == example_inputs['boolean']
    assert builder.default == orm.Int(DEFAULT_INT)


def test_port_names_overlapping_mutable_mapping_methods():
    """Check that port names take precedence over `collections.MutableMapping` methods.

    The `ProcessBuilderNamespace` is a `collections.MutableMapping` but since the port names are made accessible
    as attributes, they can overlap with some of the mappings builtin methods, e.g. `values()`, `items()` etc.
    The port names should take precendence in this case and if one wants to access the mapping methods one needs to
    cast the builder to a dictionary first.
    """
    builder = ExampleWorkChain.get_builder()

    # The `values` method is obscured by a port that also happens to be called `values`, so calling it should raise
    with pytest.raises(TypeError):
        builder.values()

    # However, we can assign a node to it
    builder.values = orm.Int(2)

    # Calling the attribute `values` will then actually try to call the node, which should raise
    with pytest.raises(TypeError):
        builder.values()

    # Casting the builder to a dict, *should* then make `values` callable again
    assert orm.Int(2) in dict(builder).values()

    # The mapping methods should not be auto-completed, i.e. not in the values returned by calling `dir`
    for method in [method for method in dir(MutableMapping) if method != 'values']:
        assert method not in dir(builder)

    # On the other hand, all the port names *should* be present
    for port_name in ExampleWorkChain.spec().inputs.keys():
        assert port_name in dir(builder)

    # The `update` method is implemented, but prefixed with an underscore to not block the name for a port
    builder.update({'boolean': orm.Bool(False)})
    assert builder.boolean == orm.Bool(False)


def test_calc_job_node_get_builder_restart(aiida_code_installed):
    """Test the `CalcJobNode.get_builder_restart` method."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    inputs = {
        'metadata': {
            'label': 'some-label',
            'description': 'some-description',
            'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}, 'max_wallclock_seconds': 1800},
        },
        'x': orm.Int(1),
        'y': orm.Int(2),
        'code': code,
    }

    _, node = run_get_node(CalculationFactory('core.arithmetic.add'), **inputs)
    builder = node.get_builder_restart()

    assert builder.x == orm.Int(1)
    assert builder.y == orm.Int(2)
    assert builder._inputs(prune=True)['metadata'] == inputs['metadata']


def test_code_get_builder(aiida_localhost):
    """Test that the `Code.get_builder` method returns a builder where the code is already set."""
    code = orm.InstalledCode(
        label='test_code',
        computer=aiida_localhost,
        filepath_executable='/bin/true',
        default_calc_job_plugin='core.templatereplacer',
    )
    code.store()

    # Check that I can get a builder
    builder = code.get_builder()
    assert builder.code.pk == code.pk

    # Check that I can set the parameters
    builder.parameters = orm.Dict(dict={})

    # Check that it complains for an unknown input
    with pytest.raises(AttributeError):
        builder.unknown_parameter = 3

    # Check that it complains if the type is not the correct one (for the templatereplacer, it should be a Dict)
    with pytest.raises(ValueError):
        builder.parameters = orm.Int(3)


def test_set_attr():
    """Test that ``__setattr__`` keeps sub portnamespaces as ``ProcessBuilderNamespace`` instances."""
    builder = LazyProcessNamespace.get_builder()
    assert isinstance(builder.namespace, ProcessBuilderNamespace)
    assert isinstance(builder.namespace.nested, ProcessBuilderNamespace)

    builder.namespace = {'a': 'a', 'c': 'c', 'nested': {'bird': 'mus'}}
    assert isinstance(builder.namespace, ProcessBuilderNamespace)
    assert isinstance(builder.namespace.nested, ProcessBuilderNamespace)


def test_update():
    """Test the ``_update`` method to update an existing builder with a dictionary."""
    builder = NestedNamespaceProcess.get_builder()
    builder.nested.namespace = {'int': 1, 'float': 2.0}
    assert builder._inputs(prune=True) == {'nested': {'namespace': {'int': 1, 'float': 2.0}}}

    # Since ``_update`` will replace nested namespaces and not recursively merge them, if we don't specify all
    # required inputs, the validation should fail.
    with pytest.raises(ValueError):
        builder._update({'nested': {'namespace': {'int': 5, 'str': 'x'}}})

    update_dict = {'nested': {'namespace': {'int': 5, 'float': 3.0, 'str': 'x'}}}
    # Now we specify all required inputs and an additional optional one and since it is a nested namespace
    builder._update(update_dict)
    assert builder._inputs(prune=True) == update_dict

    # Pass the dictionary as keyword arguments
    builder._update(**update_dict)
    assert builder._inputs(prune=True) == update_dict


def test_merge():
    """Test the ``_merge`` method to merge a dictionary into an existing builder."""
    builder = NestedNamespaceProcess.get_builder()
    builder.nested.namespace = {'int': 1, 'float': 2.0}
    assert builder._inputs(prune=True) == {'nested': {'namespace': {'int': 1, 'float': 2.0}}}

    # Define only one of the required ports of `nested.namespace`. This should leave the `float` input untouched and
    # even though not specified explicitly again, since the merged dictionary still contains it, the
    # `nested.namespace` port should still be valid.
    builder._merge({'nested': {'namespace': {'int': 5}}, 'opt': {'m': {'a': 1}}})
    assert builder._inputs(prune=True) == {'nested': {'namespace': {'int': 5, 'float': 2.0}}, 'opt': {'m': {'a': 1}}}

    # Perform same test but passing the dictionary in as keyword arguments
    builder._merge(**{'nested': {'namespace': {'int': 5}}})
    assert builder._inputs(prune=True) == {'nested': {'namespace': {'int': 5, 'float': 2.0}}, 'opt': {'m': {'a': 1}}}


def test_instance_interference():
    """Test that two builder instances do not interact through the class.

    This is a regression test for #4420.
    """

    class ProcessOne(Process):
        """Process with nested required ports to check the update functionality."""

        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('port', valid_type=int, default=1, non_db=True)

    class ProcessTwo(Process):
        """Process with nested required ports to check the update functionality."""

        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('port', valid_type=int, default=2, non_db=True)

    builder_one = ProcessOne.get_builder()
    assert builder_one.port == 1
    assert isinstance(builder_one, ProcessBuilderNamespace)

    # Create a second builder and check its only port has the correct default, but also that the original builder
    # still has its original port default and hasn't been affected by the second builder because the share a port
    # name.
    builder_two = ProcessTwo.get_builder()
    assert isinstance(builder_two, ProcessBuilderNamespace)
    assert builder_two.port == 2
    assert builder_one.port == 1


def test_pretty_repr(example_inputs):
    """Test the pretty representation of the ``ProcessBuilder`` class."""
    builder = ExampleWorkChain.get_builder()
    builder._update(example_inputs)

    pretty_repr = """
    Process class: ExampleWorkChain
    Inputs:
    boolean: true
    dict:
      a: 1
      b:
        c: 2
    dynamic:
      namespace:
        alp: 1
    metadata: {}
    name:
      spaced: 1
    name_spaced: underscored
    """
    assert pretty(builder) == textwrap.dedent(pretty_repr.lstrip('\n'))
