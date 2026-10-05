###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Prepared inputs remain launch values, rather than calculation outputs."""

import json

import pytest

from aiida import orm
from aiida.engine import (
    GraphProcess,
    WorkChain,
    graph_execution,
    graph_source,
    run_get_node,
    task_from_builder,
    task_from_workchain,
)
from aiida.engine.processes.graphs.build_source import UnsupportedSyntax
from aiida.engine.processes.graphs.inputs import MissingRequiredInputsError
from aiida.engine.processes.graphs.spec import GraphSpec
from tests.engine.processes.graphs.registration_tasks import RegisteredCalculation


class PreparedWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('pw.structure', valid_type=orm.Int, help='The structure surrogate')
        spec.input('pw.parent', valid_type=orm.Int, required=False)
        spec.input('pw.parent_folder', valid_type=orm.RemoteData, required=False)
        spec.input('remote_input', valid_type=orm.RemoteData, required=False)
        spec.input('pw.parameters', valid_type=orm.Dict)
        spec.input('pw.optional', valid_type=orm.Str, required=False)
        spec.input('pw.defaulted', valid_type=orm.Int, default=lambda: orm.Int(7))
        spec.input_namespace('pw.pseudos', dynamic=True, valid_type=orm.Int)
        spec.output('result', valid_type=orm.Int)
        spec.output('remote_folder', valid_type=orm.RemoteData, required=False)
        spec.outline(cls.finish)

    def finish(self):
        self.out('result', self.inputs.pw.structure)
        if 'remote_input' in self.inputs:
            self.out('remote_folder', self.inputs.remote_input)


class SingleNamespace(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('namespace.value', valid_type=orm.Int)
        spec.output('result', valid_type=orm.Int)
        spec.outline(cls.finish)

    def finish(self):
        self.out('result', self.inputs.namespace.value)


single = task_from_workchain(SingleNamespace)
step = task_from_workchain(PreparedWorkChain)


@graph_source
def prepared_source():
    return step().result


@graph_source
def explicit_none_source():
    return step(pw={'optional': None}).result


@graph_source
def prepared_chain():
    first = step()
    second = step(pw={'parent_folder': first.remote_folder})
    return second.result


@graph_source
def reference_only_namespace():
    first = step()
    second = single(namespace={'value': first.result})
    return second.result


def prepared(value=2):
    builder = PreparedWorkChain.get_builder()
    builder.pw.structure = orm.Int(value).store()
    builder.pw.parameters = orm.Dict({'old': {'a': 1}})
    builder.pw.pseudos = {'X': orm.Int(10).store()}
    builder.metadata.label = 'prepared label'
    return builder


def test_source_rejects_global_run_specific_handle(monkeypatch):
    monkeypatch.setitem(globals(), 'step', task_from_builder(prepared()))
    with pytest.raises(UnsupportedSyntax, match='bind_tasks'):
        prepared_source.build()


def test_snapshot_and_roundtrip():
    builder = prepared()
    handle = task_from_builder(builder)
    builder.metadata.label = 'changed'
    builder.pw.pseudos['Y'] = orm.Int(20)
    bound = prepared_source.bind_tasks(step=handle)
    launch = bound.get_launch_inputs()
    body = bound.build()
    assert GraphSpec.from_dict(json.loads(json.dumps(body.to_dict()))).to_dict() == body.to_dict()
    assert builder.pw.structure.uuid not in json.dumps(body.to_dict())
    assert 'changed' not in launch['graph_bindings'].values()
    assert 'prepared label' in launch['graph_bindings'].values()
    captured = handle.bound_inputs
    captured['pw']['pseudos']['Z'] = orm.Int(30)
    assert set(handle.bound_inputs['pw']['pseudos']) == {'X'}
    assert handle.bound_inputs['pw']['structure'] is builder.pw.structure


@pytest.mark.requires_broker
def test_launch_preserves_nodes_metadata_and_defaults():
    builder = prepared()
    handle = prepared_source.bind_tasks(step=task_from_builder(builder))
    results, node = run_get_node(handle)
    assert node.is_finished_ok, node.exit_message
    (child,) = node.called
    assert child.label == 'prepared label'
    assert child.inputs.pw.structure.uuid == builder.pw.structure.uuid
    assert child.inputs.pw.pseudos.X.uuid == builder.pw.pseudos['X'].uuid
    assert child.inputs.pw.parameters.uuid == builder.pw.parameters.uuid
    assert child.inputs.pw.defaulted.value == 7
    assert 'optional' not in child.inputs.pw
    assert results['result'].uuid == builder.pw.structure.uuid
    assert 'graph_bindings' not in node.inputs


@pytest.mark.requires_broker
def test_execution_placement_merges_namespace_and_replaces_leaf():
    builder = prepared()
    adapted = task_from_builder(builder)
    replacement = orm.Dict({'new': {'b': 2}})

    @graph_execution
    def execution_refs(parent, parameters):
        return adapted(pw={'parent': parent, 'parameters': parameters}).result

    results, node = run_get_node(execution_refs, parent=orm.Int(3), parameters=replacement)
    assert node.is_finished_ok, node.exit_message
    (child,) = node.called
    assert child.inputs.pw.parent.value == 3
    assert child.inputs.pw.parameters.get_dict() == {'new': {'b': 2}}
    assert child.inputs.pw.pseudos.X.uuid == builder.pw.pseudos['X'].uuid
    assert results['result'].value == 2

    @graph_execution
    def concrete_override():
        return adapted(pw={'parameters': replacement}).result

    assert replacement.uuid not in json.dumps(concrete_override.build().to_dict())
    _, node = run_get_node(concrete_override)
    (child,) = node.called
    assert child.inputs.pw.parameters.uuid == replacement.uuid


def test_incomplete_builder_and_invalid_placement():
    empty = prepared_source.bind_tasks(step=task_from_builder(PreparedWorkChain.get_builder()))
    with pytest.raises(MissingRequiredInputsError, match='structure') as exception:
        empty.get_launch_inputs()
    missing = next(item for item in exception.value.missing if item.socket_path == 'pw.structure')
    assert missing.help == 'The structure surrogate'
    with pytest.raises(MissingRequiredInputsError, match='structure'):
        GraphProcess.launch_inputs(GraphSpec.from_dict(empty.build().to_dict()), {})
    with pytest.raises(MissingRequiredInputsError, match='structure'):
        run_get_node(GraphProcess, graph=orm.Dict(empty.build().to_dict()))
    builder = prepared()
    del builder.pw.structure
    adapted = task_from_builder(builder)
    with pytest.raises(MissingRequiredInputsError, match='structure'):
        prepared_source.bind_tasks(step=adapted).get_launch_inputs()

    @graph_execution
    def complete(structure):
        return adapted(pw={'structure': structure}).result

    assert complete.get_launch_inputs(structure=orm.Int(4))
    with pytest.raises(ValueError, match='type'):
        complete.get_launch_inputs(structure=orm.Str('wrong'))

    @graph_execution
    def unknown():
        return adapted(pw={'unknown': 1}).result

    with pytest.raises((TypeError, ValueError), match='unknown'):
        unknown.get_launch_inputs()


@pytest.mark.requires_broker
def test_calculation_builder_scheduler_options(aiida_code_installed):
    builder = RegisteredCalculation.get_builder()
    builder.code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder.x = orm.Int(2)
    builder.y = orm.Int(3)
    builder.metadata.label = 'prepared calculation'
    builder.metadata.options.resources = {'num_machines': 1}
    builder.metadata.options.max_wallclock_seconds = 120
    adapted = task_from_builder(builder)
    builder.metadata.options.resources['num_machines'] = 2

    @graph_execution
    def calculation_graph():
        return adapted().sum

    results, node = run_get_node(calculation_graph)
    assert node.is_finished_ok, node.exit_message
    (child,) = node.called
    assert child.inputs.code.uuid == builder.code.uuid
    assert child.inputs.x.uuid == builder.x.uuid
    assert child.label == 'prepared calculation'
    assert child.base.attributes.get('resources')['num_machines'] == 1
    assert child.base.attributes.get('max_wallclock_seconds') == 120
    assert results['sum'].value == 5


@pytest.mark.requires_broker
def test_upstream_stored_default_is_not_cloned(monkeypatch):
    default = orm.Int(91).store()
    port = PreparedWorkChain.spec().inputs['pw']['defaulted']
    monkeypatch.setattr(port, 'default', default)

    def forbidden():
        pytest.fail('Validation must not clone an upstream default node')

    monkeypatch.setattr(default, 'clone', forbidden)
    _, node = run_get_node(prepared_source.bind_tasks(step=task_from_builder(prepared())))
    assert node.is_finished_ok, node.exit_message
    (child,) = node.called
    assert child.inputs.pw.defaulted.uuid == default.uuid


def test_independent_bindings():
    one = prepared_source.bind_tasks(step=task_from_builder(prepared(1)))
    two = prepared_source.bind_tasks(step=task_from_builder(prepared(2)))
    assert one.build().to_dict() == two.build().to_dict()
    name = next(name for name, targets in one.build().inputs.items() if targets == (('step', 'pw.structure'),))
    assert one.get_launch_inputs()['graph_inputs'][name].value == 1
    assert two.get_launch_inputs()['graph_inputs'][name].value == 2


@pytest.mark.parametrize('invalid', [None, {}, PreparedWorkChain])
def test_adapter_rejects_non_builder(invalid):
    with pytest.raises(TypeError, match='ProcessBuilder'):
        task_from_builder(invalid)


@pytest.mark.requires_broker
def test_fresh_daemon_roundtrip(submit_and_await):
    from aiida.engine import submit

    builder = prepared()
    bound = prepared_source.bind_tasks(step=task_from_builder(builder))
    launch = bound.get_launch_inputs()
    launch['graph'] = orm.Dict(GraphSpec.from_dict(bound.build().to_dict()).to_dict())
    node = submit_and_await(submit(GraphProcess, **launch), timeout=120)
    assert node.is_finished_ok, node.exit_message
    (child,) = node.called
    assert child.inputs.pw.pseudos.X.uuid == builder.pw.pseudos['X'].uuid
    assert child.label == 'prepared label'


@pytest.mark.requires_broker
def test_remote_folder_edge_preserves_prepared_namespace(aiida_computer_local):
    scf = prepared(1)
    scf.remote_input = orm.RemoteData(computer=aiida_computer_local(), remote_path='/prepared/scf').store()
    nscf = prepared(2)
    graph = prepared_chain.bind_tasks(step=task_from_builder(scf), step_2=task_from_builder(nscf))
    results, node = run_get_node(graph)
    assert node.is_finished_ok, node.exit_message
    first, second = node.called
    assert second.inputs.pw.parent_folder.uuid == first.outputs.remote_folder.uuid
    assert second.inputs.pw.pseudos.X.uuid == nscf.pw.pseudos['X'].uuid
    assert second.inputs.pw.parameters.uuid == nscf.pw.parameters.uuid
    assert results['result'].uuid == nscf.pw.structure.uuid


@pytest.mark.requires_broker
def test_reference_satisfies_entire_required_namespace():
    graph = reference_only_namespace.bind_tasks(
        step=task_from_builder(prepared()), single=task_from_builder(SingleNamespace.get_builder())
    )
    results, node = run_get_node(graph)
    assert node.is_finished_ok, node.exit_message
    assert results['result'].value == 2


@pytest.mark.requires_broker
@pytest.mark.parametrize('placement_none', [False, True])
def test_explicit_none_remains_a_supplied_value(placement_none):
    from aiida.engine.processes.graphs.run import GraphRun

    builder = prepared()
    if not placement_none:
        builder.pw.optional = None
    template = explicit_none_source if placement_none else prepared_source
    bound = template.bind_tasks(step=task_from_builder(builder))
    launch = bound.get_launch_inputs()
    given = {**launch['graph_inputs'], **launch.get('graph_bindings', {})}
    (start,) = GraphRun(graph=bound.build(), given=given).step().starts
    assert 'optional' in start.inputs['pw'] and start.inputs['pw']['optional'] is None
    _, node = run_get_node(bound)
    assert node.is_finished_ok, node.exit_message


def test_standalone_merge_replaces_dictionary_leaves():
    builder = prepared()
    handle = task_from_builder(builder)
    replacement = orm.Dict({'new': 3})
    inputs = handle.get_launch_inputs(pw={'parameters': replacement, 'optional': None})
    assert inputs['pw']['parameters'] is replacement
    assert inputs['pw']['pseudos']['X'] is builder.pw.pseudos['X']
    assert inputs['pw']['optional'] is None
    assert 'optional' not in handle.bound_inputs['pw']


@pytest.mark.requires_broker
def test_concurrent_bound_submissions(submit_and_await):
    from aiida.engine import submit

    first = prepared(11)
    second = prepared(22)
    first.metadata.label = 'first child'
    second.metadata.label = 'second child'
    one = submit(prepared_source.bind_tasks(step=task_from_builder(first)))
    two = submit(prepared_source.bind_tasks(step=task_from_builder(second)))
    one = submit_and_await(one, timeout=120)
    two = submit_and_await(two, timeout=120)
    assert one.is_finished_ok and two.is_finished_ok
    assert one.outputs.result.uuid == first.pw.structure.uuid
    assert two.outputs.result.uuid == second.pw.structure.uuid
    assert one.called[0].label == 'first child'
    assert two.called[0].label == 'second child'
