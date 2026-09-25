###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run processes the daemon cannot import, end to end through a real worker.

A daemon worker imports from the ``sys.path`` the daemon froze when it started. These tests put code where that
path does not reach, which is what a Jupyter notebook and a scratch directory both amount to, and check that the
worker runs it anyway.

The unit tests elsewhere pin each decision on its own. These pin that the decisions add up to a process that runs.
"""

import textwrap
import time
import typing as t
from collections.abc import Callable

import pytest

from aiida import orm
from aiida.engine import WorkChain, calcfunction, workfunction
from aiida.engine.processes.persistence import META, META__CLASS_BYTES, CheckpointSerializable
from aiida.orm import CalcFunctionNode, InstalledCode, ProcessNode, WorkFunctionNode

pytestmark = [pytest.mark.requires_broker, pytest.mark.usefixtures('started_daemon_client')]


def class_metadata(cls: type) -> dict[str, t.Any]:
    """Return checkpoint class metadata to establish the transport used by the worker."""
    from aiida.common import loaders

    state: dict[str, t.Any] = {}
    CheckpointSerializable._record_class(value=cls, loader=loaders.get_object_loader(), out_state=state)
    return state[META]


class NotebookWorkChain(WorkChain):
    """Stands in for a class defined in a notebook cell, once ``unresolvable_in_main`` has relabelled it."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int)
        spec.outline(cls.compute)
        spec.output('total', valid_type=orm.Int)

    def compute(self):
        self.out('total', orm.Int(self.inputs.x.value + 1).store())


@calcfunction
def notebook_add(x):
    """Stands in for a calculation function defined in a notebook cell."""
    return x + 1


@workfunction
def notebook_pass_through(x):
    """Stands in for a work function defined in a notebook cell, which returns a node rather than creating one."""
    return x


def test_workchain_defined_in_main(submit_and_await: Callable[..., ProcessNode], unresolvable_in_main):
    node = submit_and_await(unresolvable_in_main(NotebookWorkChain), x=orm.Int(41))

    assert node.is_finished_ok, node.exception
    assert node.outputs.total.value == 42


@pytest.mark.parametrize(
    ('function', 'node_class', 'expected'),
    (
        pytest.param(notebook_add, CalcFunctionNode, 42, id='calcfunction'),
        pytest.param(notebook_pass_through, WorkFunctionNode, 41, id='workfunction'),
    ),
)
def test_process_function_defined_in_main(
    function: Callable[..., t.Any],
    node_class: type[ProcessNode],
    expected: int,
    submit_and_await: Callable[..., ProcessNode],
    monkeypatch: pytest.MonkeyPatch,
):
    """A process function is identified by the function rather than by the class built for it, so the function is
    what has to reach the worker. Both decorators build that class the same way, so both have to arrive.
    """
    from aiida.engine import submit

    monkeypatch.setattr(function, '__module__', '__main__')
    monkeypatch.setattr(function.process_class, '__module__', '__main__')

    assert isinstance(class_metadata(cls=function.process_class).get(META__CLASS_BYTES), bytes), (
        'the daemon can resolve this function, so this test would prove nothing'
    )

    node = submit_and_await(submit(function, x=orm.Int(41)))

    assert isinstance(node, node_class), 'premise: the decorator under test is the one that ran'
    assert node.is_finished_ok, node.exception
    assert node.outputs.result.value == expected


def test_an_installed_plugin_still_travels_by_name(
    submit_and_await: Callable[..., ProcessNode], aiida_code_installed: Callable[..., InstalledCode]
):
    """Test that a registered plugin carries no process class bytes, which keeps an ordinary checkpoint small."""
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    assert class_metadata(cls=ArithmeticAddCalculation).get(META__CLASS_BYTES) is None

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = orm.Int(2)
    builder.y = orm.Int(40)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.sum.value == 42
    assert node.process_type == 'aiida.calculations:core.arithmetic.add'


def test_calcjob_defined_in_main(
    submit_and_await: Callable[..., ProcessNode],
    unresolvable_in_main,
    aiida_code_installed: Callable[..., InstalledCode],
):
    """Carrying the class is not enough on its own here: the parser reads the output spec from the process class, and
    takes it from the running process rather than the node, which carries only the name it was recorded under.
    """
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    class MainCalcJob(ArithmeticAddCalculation):
        """Stands in for a calculation job defined in a notebook cell."""

        @classmethod
        def define(cls, spec):
            super().define(spec)

    unresolvable_in_main(MainCalcJob)

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = MainCalcJob.get_builder()
    builder.code = code
    builder.x = orm.Int(2)
    builder.y = orm.Int(40)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.sum.value == 42

    # The record of what ran outlives the checkpoint that carried it. The source is read from the file the
    # class's own methods were compiled from, since `__main__` has none to offer.
    #
    # Sealing is what deletes the checkpoint, and it lands just after the state that `submit_and_await` waits for.
    for _ in range(100):
        node = orm.load_node(node.pk)
        if node.is_sealed:
            break
        time.sleep(0.1)

    assert node.is_sealed
    assert node.checkpoint is None
    source = textwrap.dedent(node.class_source)
    assert source.startswith('class MainCalcJob(ArithmeticAddCalculation):')
    assert 'super().define(spec)' in source
