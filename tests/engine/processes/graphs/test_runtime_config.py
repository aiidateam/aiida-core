###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Runtime configuration binding, process provenance and checkpoint persistence."""

import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.exceptions import GraphLanguageError, GraphValidationError
from aiida.engine import PortModel, WorkChain, graph, par_map, run_get_node, submit, task
from aiida.engine.processes.graphs.ir import TaskIR
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.persistence import CheckpointPayload
from aiida.orm import Code, DataList, Dict, InstalledCode, Int, PortableCode, RemoteData

pytestmark = pytest.mark.presto


class ConfiguredChain(WorkChain):
    """Record an executable while returning an existing scientific input."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('executable', valid_type=InstalledCode)
        spec.output('result', valid_type=Int)
        spec.outline(cls.finish)

    def finish(self):
        self.out('result', self.inputs.x)


class StrictCalculation(ArithmeticAddCalculation):
    """Require an executable to exercise preflight requiredness."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('code', valid_type=Code)


class ExposedChain(WorkChain):
    """Expose calculation inputs without launching a calculation."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(
            StrictCalculation, namespace='calc', namespace_options={'dynamic': False, 'valid_type': None}
        )
        spec.output('result', valid_type=Int)
        spec.outline(cls.finish)

    def finish(self):
        self.out('result', self.inputs.calc.x)


class NestedExposure(WorkChain):
    """Preserve roles across multiple exposure boundaries."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(ExposedChain, namespace='base', namespace_options={'dynamic': False, 'valid_type': None})


class PortTypes(WorkChain):
    """Distinguish Code-only ports from mixed and opaque scientific inputs."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('nested.executable', valid_type=(InstalledCode, PortableCode, type(None)))
        spec.input('optional_code', valid_type=Code, required=False)
        spec.input('mixed', valid_type=(Code, Int))
        spec.input('settings', valid_type=Dict)
        spec.input('folder', valid_type=RemoteData, required=False)
        spec.input('anything', required=False)


configured_chain = task(ConfiguredChain)
strict_calc = task(StrictCalculation)
exposed_chain = task(ExposedChain)


@graph
def configured(x: int) -> int:
    result = configured_chain(x=x)
    return result.result


@graph
def wired(x: int, code: InstalledCode) -> int:
    result = configured_chain(x=x, executable=code)
    return result.result


@graph
def calculation(x: int, y: int) -> int | float:
    result = strict_calc(x=x, y=y)
    return result.sum


@graph
def exposed(x: int, y: int) -> int:
    result = exposed_chain(calc={'x': x, 'y': y})
    return result.result


class CalculationInputs(PortModel):
    x: int
    y: int
    code: Code


@graph
def exposed_whole(calc: CalculationInputs) -> int:
    result = exposed_chain(calc=calc)
    return result.result


@graph
def missing_science(y: int) -> int:
    result = exposed_chain(calc={'y': y})
    return result.result


@graph
def nested(x: int) -> int:
    first = configured(x=x).alias('first')
    return configured(x=first).alias('second')


@graph
def branch(x: int, flag: bool) -> int:
    if flag:
        result = configured_chain(x=x)
    else:
        result = configured_chain(x=x)
    return result.result


@graph
def loop(x: int, count: int) -> int:
    index = 0
    while index < count:
        result = configured_chain(x=x)
        x = result.result
        index = index + 1
    return x


@graph
def mapped(values: DataList) -> DataList:
    return par_map(configured, values)


@pytest.fixture
def executable(aiida_code_installed):
    return aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')


def test_inference(aiida_profile):
    assert TaskIR.from_process(PortTypes).runtime_input_paths() == frozenset(
        {'metadata', 'nested.executable', 'optional_code'}
    )
    assert TaskIR.from_process(StrictCalculation).runtime_input_paths() == frozenset(
        {'metadata', 'code', 'monitors', 'remote_folder'}
    )
    assert TaskIR.from_process(NestedExposure).runtime_input_paths() == frozenset(
        {
            'metadata',
            'base.metadata',
            'base.calc.metadata',
            'base.calc.code',
            'base.calc.monitors',
            'base.calc.remote_folder',
        }
    )


def test_build_partition(aiida_profile):
    assert configured.build() is None
    assert calculation.build() is None
    assert exposed.build() is None
    with pytest.raises(GraphLanguageError, match=r"missing required inputs: \['calc.x'\]"):
        missing_science.build()


@pytest.mark.parametrize('workflow', [configured, calculation, exposed])
def test_required_config_preflight(workflow, aiida_profile):
    inputs = {'x': 1} if workflow is configured else {'x': 1, 'y': 2}
    with pytest.raises(GraphValidationError, match=r'executable|code'):
        workflow.get_launch_inputs(**inputs)


@pytest.mark.parametrize(
    'config,match',
    [
        ({'unknown': {}}, 'unknown placement'),
        ({'configured_chain': {'x': 4}}, 'not an inferred execution input'),
        ({'configured_chain': {'metadata': {'call_link_label': 'override'}}}, 'owned by the graph'),
        ({'configured_chain': {'metadata': {'store_provenance': False}}}, 'provenance cannot'),
        ({'configured_chain': 1}, 'expected a mapping'),
        ([], 'must be a mapping'),
    ],
)
def test_invalid_config(config, match, aiida_profile):
    with pytest.raises(GraphValidationError, match=match):
        configured.get_launch_inputs(x=1, runtime_config=config)


def test_wiring_conflict(executable):
    with pytest.raises(GraphValidationError, match='already explicitly wired'):
        wired.get_launch_inputs(x=1, code=executable, runtime_config={'configured_chain': {'executable': executable}})
    with pytest.raises(GraphValidationError, match='already explicitly wired'):
        exposed_whole.get_launch_inputs(
            calc={'x': 1, 'y': 2, 'code': executable}, runtime_config={'exposed_chain': {'calc': {'code': executable}}}
        )


def test_configured_calcjob_run(executable):
    outputs, node = run_get_node(
        calculation,
        inputs={'x': 2, 'y': 3},
        runtime_config={
            'strict_calc': {'code': executable, 'metadata': {'options': {'custom_scheduler_commands': '# config'}}}
        },
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    assert set(node.inputs) == {'x', 'y'}
    (child,) = node.called
    assert child.inputs.code.uuid == executable.uuid
    assert child.get_option('custom_scheduler_commands') == '# config'


def test_exposed_config_run(executable):
    outputs, node = run_get_node(
        exposed,
        x=3,
        y=4,
        runtime_config={
            'exposed_chain': {'calc': {'code': executable, 'metadata': {'options': {'resources': {'num_machines': 1}}}}}
        },
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    assert node.called[0].inputs.calc.code.uuid == executable.uuid
    assert set(node.inputs) == {'x', 'y'}


def test_run_and_restart_snapshot(executable):
    config = {'configured_chain': {'executable': executable, 'metadata': {'label': 'configured child'}}}
    launch = configured.get_launch_inputs(inputs={'x': 3}, runtime_config=config)
    config['configured_chain']['metadata']['label'] = 'mutated'
    outputs, node = run_get_node(GraphProcess, **launch)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    (child,) = node.called
    assert child.inputs.executable.uuid == executable.uuid
    assert child.label == 'configured child'
    assert set(node.inputs) == {'x'}
    restarted = node.get_builder_restart()
    assert restarted.runtime_config['configured_chain']['executable'].uuid == executable.uuid
    outputs, again = run_get_node(restarted)
    assert again.is_finished_ok
    assert outputs['result'].value == 3
    assert again.called[0].label == 'configured child'


def test_nested_scoped_config(executable, aiida_code_installed):
    other = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/true')
    outputs, node = run_get_node(
        nested,
        x=7,
        runtime_config={
            'first': {'configured_chain': {'executable': executable}},
            'second': {'configured_chain': {'executable': other}},
        },
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    assert [child.inputs.executable.uuid for child in node.called] == [executable.uuid, other.uuid]


@pytest.mark.parametrize('flag', [False, True])
def test_branch_config(executable, flag):
    outputs, node = run_get_node(
        branch, x=7, flag=flag, runtime_config={'configured_chain': {'executable': executable}}
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    assert node.called[0].inputs.executable.uuid == executable.uuid


@pytest.mark.parametrize('count', [0, 2])
def test_loop_config(executable, count):
    outputs, node = run_get_node(
        loop, x=7, count=count, runtime_config={'configured_chain': {'executable': executable}}
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    assert len(node.called) == count
    assert all(child.inputs.executable.uuid == executable.uuid for child in node.called)


@pytest.mark.parametrize('values', [[], [1, 2]])
def test_map_config(executable, values):
    outputs, node = run_get_node(
        mapped,
        values=DataList([Int(value) for value in values]),
        runtime_config={'configured_chain': {'executable': executable}},
    )
    assert node.is_finished_ok
    assert [value.value for value in outputs['result']] == values
    children = [child for child in node.called if child.process_class is ConfiguredChain]
    assert len(children) == len(values)
    assert all(child.inputs.executable.uuid == executable.uuid for child in children)


def test_checkpoint_config(executable):
    process = GraphProcess(
        inputs=nested.get_launch_inputs(
            x=7,
            runtime_config={
                'first': {'configured_chain': {'executable': executable}},
                'second': {'configured_chain': {'executable': executable}},
            },
        )
    )
    restored = None
    try:
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert restored.inputs.runtime_config['first']['configured_chain']['executable'].uuid == executable.uuid
        restored.execute()
        assert restored.node.is_finished_ok
        assert restored.outputs['result'].value == 7
        assert len(restored.node.called) == 2
        assert all(child.inputs.executable.uuid == executable.uuid for child in restored.node.called)
    finally:
        if restored is not None:
            restored.close()
        process.close()


@pytest.mark.requires_broker
def test_submit_config(executable, submit_and_await):
    """The public separated launch channels survive a daemon checkpoint."""
    node = submit(
        configured,
        inputs={'x': 5},
        runtime_config={'configured_chain': {'executable': executable, 'metadata': {'label': 'daemon child'}}},
        metadata={'label': 'daemon graph'},
    )
    submit_and_await(node)
    assert node.is_finished_ok
    assert node.outputs.result.value == 5
    assert node.label == 'daemon graph'
    (child,) = node.called
    assert child.inputs.executable.uuid == executable.uuid
    assert child.label == 'daemon child'
    assert set(node.inputs) == {'x'}


@pytest.mark.parametrize('workflow,inputs', [(branch, {'x': 1, 'flag': False}), (loop, {'x': 1, 'count': 0})])
def test_required_config_in_control_bodies(workflow, inputs, aiida_profile):
    """Configuration is required even when a control body may not execute."""
    with pytest.raises(GraphValidationError, match='executable'):
        workflow.get_launch_inputs(**inputs)


def test_namespace_validator_preserved(executable):
    """Inference must retain the original nested process validators."""
    with pytest.raises(GraphValidationError, match=r'stash\.target_base'):
        calculation.get_launch_inputs(
            x=1,
            y=2,
            runtime_config={
                'strict_calc': {
                    'code': executable,
                    'metadata': {
                        'options': {
                            'stash': {'target_base': 'relative', 'source_list': ['output'], 'stash_mode': 'copy'}
                        }
                    },
                }
            },
        )


def test_legacy_launch_rejected(aiida_profile):
    with pytest.raises(GraphValidationError, match='was replaced by `runtime_config`'):
        configured.get_launch_inputs(x=1, task_metadata={})
