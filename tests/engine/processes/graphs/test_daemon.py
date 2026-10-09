###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests running a graph of tasks on a daemon worker, end to end.

A worker is a fresh interpreter that never saw the graph being written. It reads the declaration back from the
node, loads each task from the module it names, and carries what it has run on the checkpoint, so this is where
the parts that only matter across a process boundary are actually exercised.
"""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import (
    ExitCode,
    ProcessHandlerReport,
    WorkChain,
    branch,
    each,
    graph,
    handler,
    loop,
    submit,
    task,
)

pytestmark = pytest.mark.requires_broker


@task(outputs=['total'])
def add(x, y):
    return x + y


@task(outputs=['values'])
def spread(n):
    """Produce the collection a later task is run over, whose length is only known once this has run."""
    return list(range(int(n)))


@task(outputs=['value', 'keep_going'])
def step_down(value):
    """Take one off the value, and say whether there is anything left to take off."""
    return value - 1, value - 1 > 0


class Combine(WorkChain):
    """Take two values in one namespace and return their sum in another, as a workchain declares its ports."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('pair.left', valid_type=orm.Int)
        spec.input('pair.right', valid_type=orm.Int)
        spec.outline(cls.combine)
        spec.output('sums.total', valid_type=orm.Int)

    def combine(self):
        self.out('sums.total', orm.Int(self.inputs.pair.left + self.inputs.pair.right).store())


combine = task(Combine)


@graph
def double(value):
    """A graph placed inside another, so the pipeline runs one as a task of its own."""
    return add(x=value, y=value)


@graph
def pipeline(start, by, refine_it):
    """Run every kind of task a graph has, in one go.

    A graph inside a graph, a fan-out over a collection another task produced, a branch written in place with
    both of its sides, a loop carrying its state, and a workchain wired through its namespaces.
    """
    doubled = double(value=start)
    shifted = add(x=each(spread(n=start).values), y=by)

    with branch(refine_it) as refined:
        refined.returns(total=doubled.total)

    with refined.otherwise:
        refined.returns(total=add(x=start, y=0).total)

    with loop(condition='keep_going', value=refined.total) as counting:
        stepped = step_down(value=counting.value)
        counting.returns(value=stepped.value, keep_going=stepped.keep_going)

    combined = combine(pair={'left': counting.value, 'right': doubled.total})

    return {'total': combined.sums.total, 'shifted': shifted.total}


def test_a_graph_runs_on_a_daemon_worker(submit_and_await):
    """Every kind of task survives being read back and run by a worker that never saw the graph written."""
    node = submit_and_await(submit(pipeline, start=2, by=10, refine_it=True), timeout=180)

    assert node.is_finished_ok, node.exit_message
    assert node.outputs.total == 4  # `double` gave 4, the loop counted it to 0, and `Combine` added the 4 back
    assert {key: value.value for key, value in node.outputs.shifted.items()} == {'item_0': 10, 'item_1': 11}


def test_every_task_is_a_process_of_its_own(submit_and_await):
    """Each task is a child process under the name the graph gave it, which is what the provenance records."""
    node = submit_and_await(submit(pipeline, start=2, by=10, refine_it=True), timeout=180)

    called = {
        entry.link_label
        for link_type in (LinkType.CALL_CALC, LinkType.CALL_WORK)
        for entry in node.base.links.get_outgoing(link_type=link_type).all()
    }

    assert {'double', 'spread', 'branch', 'Combine'} <= called
    assert {'add_item_0', 'add_item_1'} <= called, 'the fan-out runs one process per item'
    assert {'loop_iteration_0', 'loop_iteration_1', 'loop_iteration_2', 'loop_iteration_3'} <= called


def test_the_stored_declaration_is_still_a_template(submit_and_await):
    """Nothing a run discovered is written back, so what is stored describes every run rather than this one."""
    node = submit_and_await(submit(pipeline, start=2, by=10, refine_it=True), timeout=180)

    assert node.inputs.graph.get_dict() == pipeline.build().to_dict()


def test_a_task_is_loaded_from_the_module_it_names(submit_and_await):
    """A worker is given a name to import rather than any code, so nothing about the task is pickled."""
    node = submit_and_await(submit(pipeline, start=2, by=10, refine_it=True), timeout=180)
    stored = node.inputs.graph.get_dict()

    assert stored['tasks'][1]['spec']['executor'] == {'module': __name__, 'name': 'spread'}


@handler(exit_codes=ExitCode(410))
def push_further(node, inputs):
    """Ask for one more step than the run that gave up took."""
    inputs['steps'] = orm.Int(inputs['steps'].value + 1)
    return ProcessHandlerReport(do_break=True)


@task(outputs=['value'], handlers=[push_further])
def converge(steps):
    """Converge only once it is given enough steps, which is what the handler gives it."""
    if steps < 3:
        return ExitCode(410, 'did not converge')
    return {'value': steps * 10}


@graph
def converge_and_add(steps, by):
    return {'total': add(x=converge(steps=steps).value, y=by).total}


def test_a_handled_task_is_retried_by_the_worker(submit_and_await):
    """A worker reads the handlers off the task it imports, so a run that failed is fixed where the graph runs."""
    node = submit_and_await(submit(converge_and_add, steps=1, by=5), timeout=180)

    assert node.is_finished_ok, node.exit_message
    assert node.outputs.total == 35

    handled = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).get_node_by_label('converge')

    assert [child.exit_status for child in sorted(handled.called, key=lambda child: child.pk)] == [410, 410, 0]
