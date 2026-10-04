###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Explicit process registration uses the original specs and executors."""

import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.links import LinkType
from aiida.engine import (
    CalcJob,
    GraphProcess,
    WorkChain,
    graph_execution,
    graph_source,
    run_get_node,
    task_execution,
    task_from_calcjob,
    task_from_workchain,
)
from tests.engine.processes.graphs.registration_tasks import (
    RegisteredCalculation,
    RegisteredWorkChain,
    calculation,
    combined,
)
from tests.engine.processes.graphs.registration_tasks import combined as imported_workchain
from tests.engine.processes.graphs.test_ast_parser import sum_two as imported_add

local_alias = combined


@graph_source
def source_workflow(pair):
    result = local_alias(pair=pair)
    return {'total': result.sums.total}


@graph_execution
def execution_workflow(pair):
    result = combined(pair=pair)
    return {'total': result.sums.total}


@graph_source
def source_calculation(code, x, y):
    result = calculation(code=code, x=x, y=y)
    return {'total': result.sum}


@graph_execution
def execution_calculation(code, x, y):
    result = calculation(code=code, x=x, y=y)
    return {'total': result.sum}


@graph_source
def imported_alias_workflow(x, y):
    return imported_add(x=x, y=y)


@graph_source
def imported_process_workflow(pair):
    result = imported_workchain(pair=pair)
    return {'total': result.sums.total}


@pytest.mark.parametrize(
    'register,process',
    [(task_from_calcjob, ArithmeticAddCalculation), (task_from_workchain, RegisteredWorkChain)],
)
def test_original_process_spec(register, process):
    handle = register(process)
    assert handle.process_class is process
    assert handle.task_spec.inputs is process.spec().inputs
    assert handle.task_spec.outputs is process.spec().outputs
    assert handle.task_spec == task_execution(process).task_spec
    assert handle.task_spec.executor.load() is process


def test_nested_port_semantics():
    ports = combined.task_spec.inputs
    assert ports['pair']['left'].valid_type is orm.Int
    assert ports['pair']['left'].required
    assert ports['pair']['right'].default().value == 3
    assert not ports['pair']['optional'].required
    assert ports['pair']['optional'].help == 'Optional label'
    assert ports['extra'].dynamic
    assert ports['extra'].valid_type is orm.Int
    assert combined.task_spec.outputs['sums']['total'].valid_type is orm.Int


@pytest.mark.parametrize('register', [task_from_calcjob, task_from_workchain])
@pytest.mark.parametrize('invalid', [None, 1, lambda: None, str, GraphProcess])
def test_reject_invalid_classes(register, invalid):
    with pytest.raises(TypeError, match=r'Expected a .* subclass'):
        register(invalid)


@pytest.mark.parametrize('register,invalid', [(task_from_calcjob, WorkChain), (task_from_workchain, CalcJob)])
def test_reject_wrong_process_kind(register, invalid):
    with pytest.raises(TypeError, match=r'Expected a .* subclass'):
        register(invalid)


@pytest.mark.parametrize('handle', [source_workflow, execution_workflow, source_calculation, execution_calculation])
def test_build_without_execution(handle, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Process implementation or source must not be accessed during registration/building')

    monkeypatch.setattr(RegisteredWorkChain, 'combine', forbidden)
    monkeypatch.setattr(ArithmeticAddCalculation, 'prepare_for_submission', forbidden)
    monkeypatch.setattr('inspect.getsourcelines', forbidden)
    assert task_from_workchain(RegisteredWorkChain).process_class is RegisteredWorkChain
    assert task_from_calcjob(ArithmeticAddCalculation).process_class is ArithmeticAddCalculation
    spec = handle.build()
    expected = combined if 'workflow' in handle.__name__ else calculation
    assert len(spec.tasks) == 1
    assert spec.tasks[0].spec == expected.task_spec


@pytest.mark.parametrize(
    'handle,name,task',
    [
        (imported_alias_workflow, 'imported_add', imported_add),
        (imported_process_workflow, 'imported_workchain', combined),
    ],
)
def test_imported_alias_resolution(handle, name, task):
    spec = handle.build()
    assert spec.tasks[0].name == name
    assert spec.tasks[0].spec == task.task_spec


@pytest.mark.requires_broker
@pytest.mark.parametrize('handle', [source_workflow, execution_workflow, imported_process_workflow])
def test_workchain_child_execution(handle):
    left = orm.Int(2)
    results, node = run_get_node(handle, pair={'left': left})
    assert node.is_finished_ok, node.exit_message
    assert results['total'].value == 5
    (child,) = node.called
    assert child.process_type == RegisteredWorkChain.build_process_type()
    assert child.inputs.pair.left.uuid == left.uuid
    assert child.inputs.pair.right.value == 3
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).one().node == child
    assert child.outputs.sums.total == results['total']


@pytest.mark.requires_broker
@pytest.mark.parametrize('handle', [source_calculation, execution_calculation])
def test_calcjob_child_execution(handle, aiida_code_installed):
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    results, node = run_get_node(handle, code=code, x=orm.Int(2), y=orm.Int(3))
    assert node.is_finished_ok, node.exit_message
    assert results['total'].value == 5
    (child,) = node.called
    assert isinstance(child, orm.CalcJobNode)
    assert child.process_type == RegisteredCalculation.build_process_type()
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).one().node == child
    assert results['total'].base.links.get_incoming(link_type=LinkType.CREATE).one().node == child
