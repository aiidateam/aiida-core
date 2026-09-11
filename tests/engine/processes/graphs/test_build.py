###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for writing a graph of tasks as ordinary Python."""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.calculations.shell import ShellJob
from aiida.common.links import LinkType
from aiida.engine import (
    BranchTask,
    Endpoint,
    LoopTask,
    Many,
    MapGraphTask,
    MapTask,
    OutputNames,
    SubgraphTask,
    TaskOutput,
    TaskOutputs,
    WorkChain,
    branch,
    each,
    graph,
    loop,
    run_get_node,
    select,
    subgraph,
    submit,
    task,
)

pytestmark = pytest.mark.requires_broker


@task(outputs=['total'])
def add(x, y):
    return x + y


@task(outputs=['quotient', 'remainder'])
def divide(x, y):
    return x // y, x % y


@graph
def add_twice(x, y):
    """Take the output of one task into the next."""
    first = add(x=x, y=y)
    return add(x=first.total, y=y)


@graph
def shift_all(values, by):
    """Run one task per item of a collection, which is what `each` marks."""
    return add(x=each(values), y=by)


@task(outputs=['values'])
def spread(n):
    """Produce the collection that a later task is run over."""
    return list(range(int(n)))


@graph
def shift_spread(n, by):
    made = spread(n=n)
    return add(x=each(made.values), y=by)


@graph
def shift_and_echo(x, y):
    """Return a computed output beside one of the graph's own inputs, passed on unchanged."""
    return {'total': add(x=x, y=y).total, 'echo': x}


@graph
def add_four_times(x, y):
    """Place a graph inside a graph, taking what the first produced into the second."""
    once = add_twice(x=x, y=y)
    return add_twice(x=once.total, y=y)


@graph
def doubled(x):
    """Stand in for the branch a condition selects."""
    return add(x=x, y=x)


@graph
def negated(x):
    """Return the same output as `doubled`, so the two can be the sides of one branch."""
    return add(x=x, y=0)


@graph
def maybe_double(x, flag):
    """Run a branch that produces nothing when its condition does not hold."""
    return branch(flag, then=doubled, x=x)


@graph
def double_or_not(x, flag):
    """Run a branch that produces the same outputs whichever side is taken."""
    return branch(flag, then=doubled, otherwise=negated, x=x)


@task(outputs=['value', 'keep_going'])
def step_down(value):
    """Take one off the value, and say whether there is anything left to take off."""
    return value - 1, value - 1 > 0


@graph
def one_step_down(value):
    """Return what the loop goes round on beside the value it carries."""
    stepped = step_down(value=value)
    return {'value': stepped.value, 'keep_going': stepped.keep_going}


@graph
def count_down(start, keep_going):
    """Run a graph again and again until nothing is left to take off."""
    counted = loop(one_step_down, condition='keep_going', value=start, keep_going=keep_going)
    return {'value': counted.value}


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
def combine_a_pair(x, y):
    """Fill one entry of a namespace from a task, take the other from the graph, and read a nested output."""
    first = add(x=x, y=y)
    combined = combine(pair={'left': first.total, 'right': y})
    return {'total': combined.sums.total}


@graph
def double_or_not_in_place(x, flag):
    """Write both sides of a branch where they are used, taking `x` from the graph around them."""
    with branch(flag) as chosen:
        chosen.returns(total=add(x=x, y=x).total)

    with chosen.otherwise:
        chosen.returns(total=add(x=x, y=0).total)

    return {'total': chosen.total}


@graph
def maybe_double_in_place(x, flag):
    """Write one side of a branch in place, leaving the other with nothing to run."""
    with branch(flag) as chosen:
        chosen.returns(total=add(x=x, y=x).total)

    return {'total': chosen.total}


@graph
def count_down_in_place(start):
    """Write a loop body where it is used, carrying its state through the block."""
    with loop(condition='keep_going', value=start) as counting:
        stepped = step_down(value=counting.value)
        counting.returns(value=stepped.value, keep_going=stepped.keep_going)

    return {'value': counting.value}


@graph
def count_down_from_a_task(x, y):
    """Take a value from a task outside the loop, which the body reaches by capturing it."""
    start = add(x=x, y=y)

    with loop(condition='keep_going', value=start.total) as counting:
        stepped = step_down(value=counting.value)
        counting.returns(value=stepped.value, keep_going=stepped.keep_going)

    return {'value': counting.value}


@task(outputs=['total'])
def total_of(parts: Many[int]) -> int:
    """Reduce what a fan-out produced, which arrives as one namespace keyed by item.

    A parameter holds one value, so taking many needs `Many`, which declares a namespace instead of a port.
    """
    return sum(part.value for part in parts.values())


@graph
def shift_and_double(value, by):
    """A whole graph to run per item, rather than a single task."""
    shifted = add(x=value, y=by)
    return {'total': add(x=shifted.total, y=shifted.total).total}


@graph
def shift_and_double_all(values, by):
    """Run a graph once per item, and reduce what every run produced."""
    each_of_them = shift_and_double(value=each(values), by=by)
    return {'total': total_of(parts=each_of_them.total).total}


@graph
def sum_of_shifted(values, by):
    """Reduce what a fan-out over a single task produced."""
    shifted = add(x=each(values), y=by)
    return {'total': total_of(parts=shifted.total).total}


@graph
def group_two_steps(x, y):
    """Group two tasks into a graph of their own, written where it is used."""
    with subgraph() as grouped:
        first = add(x=x, y=y)
        grouped.returns(total=add(x=first.total, y=y).total)

    return {'total': add(x=grouped.total, y=100).total}


@graph
def reaches_for_an_outer_task(x, y):
    """Write an inner graph that takes a value from a task in the graph around it."""
    first = add(x=x, y=y)

    @graph
    def inner(z):
        return add(x=z, y=first.total)

    return inner(z=x)


@graph
def reaches_for_an_outer_input(x, y):
    """Write an inner graph that takes an input of the graph around it."""

    @graph
    def inner(z):
        return add(x=z, y=y)

    return inner(z=x)


def test_records_tasks_links_and_inputs():
    """The body is not executed: it declares the tasks, what feeds them, and what the graph returns."""
    declaration = add_twice.build()

    assert [node.name for node in declaration.tasks] == ['add', 'add_2']
    assert [(link.source, link.source_port, link.target, link.target_port) for link in declaration.dependencies] == [
        ('add', 'total', 'add_2', 'x')
    ]
    assert declaration.outputs == {'total': Endpoint(task='add_2', port='total')}


def test_the_declaration_holds_no_values():
    """The graph names its inputs and records where each goes, so one declaration describes every run."""
    declaration = add_twice.build()

    assert [node.inputs for node in declaration.tasks] == [{}, {}]
    assert declaration.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}


def test_the_same_declaration_serves_every_run():
    """Two runs with different values store the same declaration, which is what makes it a template."""
    first, first_node = run_get_node(add_twice, x=1, y=2)
    second, second_node = run_get_node(add_twice, x=10, y=20)

    assert first['total'] == 5
    assert second['total'] == 50
    assert first_node.inputs.graph.get_dict() == second_node.inputs.graph.get_dict()
    assert first_node.inputs.graph_inputs.x != second_node.inputs.graph_inputs.x


def test_runs_what_was_written():
    """Running the graph gives the result the same code would give if the tasks had simply been called."""
    results, node = run_get_node(add_twice, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5  # (1 + 2) + 2

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    assert sorted(entry.link_label for entry in called) == ['add', 'add_2']


def test_each_places_a_task_that_fans_out():
    """Marking an input with `each` declares a task run once per item, over that input."""
    declaration = shift_all.build()
    (node,) = declaration.tasks

    assert isinstance(node, MapTask)
    assert node.item_port == 'x'
    assert declaration.inputs == {'values': (('add', 'x'),), 'by': (('add', 'y'),)}


def test_a_fan_out_runs_once_per_item():
    """Every item gets a process of its own, and the results come back under the key of the item."""
    results, node = run_get_node(shift_all, values=[1, 2, 3], by=10)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == {
        'item_0': 11,
        'item_1': 12,
        'item_2': 13,
    }


def test_a_fan_out_can_take_its_collection_from_a_task():
    """How many items there are can depend on what another task produced, so it is only known while running."""
    declaration = shift_spread.build()

    assert isinstance(declaration.task('add'), MapTask)
    assert [(link.source, link.source_port, link.target, link.target_port) for link in declaration.dependencies] == [
        ('spread', 'values', 'add', 'x')
    ]

    results, node = run_get_node(shift_spread, n=3, by=100)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == {
        'item_0': 100,
        'item_1': 101,
        'item_2': 102,
    }


def test_a_fan_out_result_passed_to_a_task_is_refused_where_it_is_written():
    """A result per item handed to a task that takes one value fails at the call that wrote it.

    What a fan-out returns carries that it is per item, so this is caught while the graph is being written
    rather than when the finished declaration is validated.
    """

    @graph
    def reduce_it(values):
        mapped = add(x=each(values), y=1)
        return add(x=mapped.total, y=2)

    with pytest.raises(ValueError, match='runs once per item'):
        reduce_it.build()


def test_an_output_inside_a_namespace_is_named_the_way_it_is_written():
    """A namespace among the outputs is walked into, and what comes out is a reference to the one port."""
    names = OutputNames(names={'sums': OutputNames.named(['total']), 'flag': None})
    outputs = TaskOutputs(task='combined', ports=names)

    assert outputs.sums.total == TaskOutput(task='combined', port='sums.total')
    assert outputs.flag == TaskOutput(task='combined', port='flag')

    with pytest.raises(AttributeError, match=r'has no output `sums\.nope`'):
        outputs.sums.nope


def test_an_output_a_task_only_declares_once_it_runs_can_still_be_named():
    """A namespace taking whatever it is given has outputs nobody declared, so naming one is allowed."""
    outputs = TaskOutputs(task='shell', ports=OutputNames(names={'retrieved': None}, dynamic=True))

    assert outputs.retrieved == TaskOutput(task='shell', port='retrieved')
    assert outputs.stdout == TaskOutput(task='shell', port='stdout'), 'a parser decides this one, not the spec'


def test_a_shell_job_is_placed_like_any_other_process():
    """`ShellJob` is a process in core, so a graph runs one with no shell-specific code of its own."""
    shell = task(ShellJob)

    @graph
    def run_a_command(code, arguments):
        return {'out': shell(code=code, arguments=arguments).stdout}

    declaration = run_a_command.build()

    assert [node.name for node in declaration.tasks] == ['ShellJob']
    assert declaration.outputs == {'out': Endpoint(task='ShellJob', port='stdout')}


def test_a_process_class_is_placed_by_the_ports_it_declares():
    """A workchain is a task like any other, wired through the namespaces it declares rather than a signature."""
    declaration = combine_a_pair.build()

    assert [node.name for node in declaration.tasks] == ['add', 'Combine']
    assert [(link.source, link.source_port, link.target, link.target_port) for link in declaration.dependencies] == [
        ('add', 'total', 'Combine', 'pair.left')
    ]
    assert declaration.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('Combine', 'pair.right'))}
    assert declaration.outputs == {'total': Endpoint(task='Combine', port='sums.total')}


def test_a_graph_wired_through_namespaces_runs():
    """What was wired one name at a time arrives as one namespace, and the nested output is read back out."""
    results, node = run_get_node(combine_a_pair, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5  # (1 + 2) as `pair.left`, plus the 2 the graph passed as `pair.right`


def test_a_process_is_launched_rather_than_called_outside_a_graph():
    """A process placed in a graph is still a process, so on its own it says how to run it."""
    with pytest.raises(TypeError, match='launched rather than called'):
        combine(pair={'left': orm.Int(1), 'right': orm.Int(2)})


@pytest.mark.parametrize(
    'subject, kwargs, expected',
    [
        pytest.param(dict, {}, 'only a process class can be a task', id='not-a-process'),
        pytest.param(Combine, {'outputs': ['total']}, 'declares its own output ports', id='outputs-given'),
    ],
)
def test_declaring_a_class_a_task_is_refused_when_it_cannot_be_one(subject, kwargs, expected):
    """A class that is not a process, or one told what to output, is refused where it is declared."""
    with pytest.raises(TypeError, match=expected):
        task(subject, **kwargs)


def test_a_graph_can_be_run_once_per_item():
    """Marking an input of a graph with `each` fans out the whole body, not just one task."""
    declaration = shift_and_double_all.build()

    assert isinstance(declaration.task('shift_and_double'), MapGraphTask)
    assert declaration.task('shift_and_double').item_port == 'value'
    assert [node.name for node in declaration.task('shift_and_double').body.tasks] == ['add', 'add_2']


@pytest.mark.parametrize(
    'declaration, expected',
    [
        pytest.param(sum_of_shifted, 36, id='over-a-task'),
        pytest.param(shift_and_double_all, 72, id='over-a-graph'),
    ],
)
def test_what_a_fan_out_produced_can_be_reduced(declaration, expected):
    """Every run produces a result, and they arrive at the next task as one namespace keyed by item."""
    results, node = run_get_node(declaration, values=[1, 2, 3], by=10)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == expected  # (11 + 12 + 13), doubled where the whole graph ran


def test_reducing_into_something_that_holds_one_value_is_refused():
    """A result per item cannot go into a port that holds one, and the graph says so when it is declared."""

    @graph
    def reduce_into_a_port(values, by):
        shifted = add(x=each(values), y=by)
        return add(x=shifted.total, y=1)

    with pytest.raises(ValueError, match='has to be a namespace'):
        reduce_into_a_port.build()


def test_a_calcfunction_may_not_return_one_of_its_inputs():
    """Why `select` is a workfunction: a calcfunction creates what it returns, and an input already exists."""
    from aiida.engine import calcfunction

    @calcfunction
    def pick(flag, a, b):
        return a if flag else b

    with pytest.raises(ValueError, match='would generate a cycle in the graph'):
        run_get_node(pick, flag=orm.Bool(True), a=orm.Int(1), b=orm.Int(2))


def test_a_fan_out_written_in_place_runs_the_whole_block_per_item():
    """Opening `each` as a block fans out everything written inside it, not just one call."""

    @graph
    def shift_and_double_in_place(values, by):
        with each(values) as item:
            shifted = add(x=item.value, y=by)
            item.returns(total=add(x=shifted.total, y=shifted.total).total)

        return {'total': total_of(parts=item.total).total}

    declaration = shift_and_double_in_place.build()

    assert isinstance(declaration.task('each'), MapGraphTask)
    assert [node.name for node in declaration.task('each').body.tasks] == ['add', 'add_2']

    results, node = run_get_node(shift_and_double_in_place, values=[1, 2, 3], by=10)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 72  # (11 + 12 + 13), each doubled


def test_select_picks_one_of_two_values():
    """A conditional over values costs one task, where a branch over graphs costs a process for each side."""

    @graph
    def best_of(first, second, prefer_first):
        return {'chosen': select(condition=prefer_first, then=first, otherwise=second).value}

    for prefer, expected in ((True, 1), (False, 2)):
        results, node = run_get_node(best_of, first=1, second=2, prefer_first=prefer)

        assert node.is_finished_ok, node.exit_message
        assert results['chosen'] == expected


def test_select_returns_the_node_it_was_given():
    """It picks between values that already exist, so it returns one rather than making a new one."""

    @graph
    def pick(first, second, prefer_first):
        return {'chosen': select(condition=prefer_first, then=first, otherwise=second).value}

    results, node = run_get_node(pick, first=1, second=2, prefer_first=True)
    chosen = results['chosen']

    assert chosen.uuid == node.inputs.graph_inputs.first.uuid, 'the very node it was handed, not a copy'


def test_a_graph_written_in_place_is_placed_as_one_task():
    """What the block groups becomes one task, so the graph around it waits on the whole of it."""
    declaration = group_two_steps.build()

    assert [node.name for node in declaration.tasks] == ['subgraph', 'add']
    assert isinstance(declaration.task('subgraph'), SubgraphTask)
    assert [node.name for node in declaration.task('subgraph').body.tasks] == ['add', 'add_2']
    assert sorted(declaration.task('subgraph').body.inputs) == ['x', 'y']


def test_a_graph_written_in_place_runs():
    """It runs as a child process of its own, and what it returns feeds the task after it."""
    results, node = run_get_node(group_two_steps, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 105  # ((1 + 2) + 2) grouped, then + 100

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()
    assert [entry.link_label for entry in called] == ['subgraph']


@pytest.mark.parametrize(
    'region, word',
    [
        pytest.param(lambda: each([1, 2]), 'each', id='each'),
        pytest.param(subgraph, 'subgraph', id='subgraph'),
    ],
)
def test_a_region_says_the_word_it_was_written_with(region, word):
    """A region names itself by what the reader typed, which for `each` is not the name of its class."""
    with pytest.raises(TypeError, match=f'`{word}` writes part of a graph'):
        with region():
            pass


def test_a_task_function_can_reduce_a_fan_out():
    """`Many` is what lets a function take the results of a fan-out, which arrive one per item."""
    spec = total_of.process_class.spec()

    assert spec.inputs['parts'].dynamic, 'a namespace rather than a port, so it takes them all'

    results, node = run_get_node(sum_of_shifted, values=[1, 2, 3], by=10)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 36  # 11 + 12 + 13


def test_an_output_inside_a_container_is_refused():
    """An output buried in a container would be stored as a value, leaving the task it comes from unwaited for."""

    @graph
    def buried(x, y):
        first = divide(x=x, y=y)
        return add(x=each([first.quotient, first.remainder]), y=100)

    with pytest.raises(ValueError, match='inside a list'):
        buried.build()


def test_only_one_input_can_be_mapped_over():
    """A task runs over one of its inputs, so marking two says which choice has to be made."""

    @graph
    def two_at_once(values, others):
        return add(x=each(values), y=each(others))

    with pytest.raises(ValueError, match='runs once per item of'):
        two_at_once.build()


def test_a_task_used_twice_keeps_the_uses_apart():
    """The second use of a task gets its own name, so both are addressable."""
    declaration = add_twice.build()

    assert [node.name for node in declaration.tasks] == ['add', 'add_2']


def test_independent_tasks_join_again():
    """Two tasks that only depend on the first are both recorded, and their outputs meet in the last."""

    @graph
    def diamond(x):
        start = add(x=x, y=1)
        left = add(x=start.total, y=10)
        right = add(x=start.total, y=100)
        return add(x=left.total, y=right.total)

    results, node = run_get_node(diamond, x=1)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 114  # (2 + 10) + (2 + 100)


def test_a_single_output_can_be_passed_without_naming_it():
    """A task with one output can be handed straight to the next, since there is nothing to choose."""

    @graph
    def chained(x, y):
        return add(x=add(x=x, y=y), y=y)

    declaration = chained.build()

    assert [(link.source, link.source_port, link.target_port) for link in declaration.dependencies] == [
        ('add', 'total', 'x')
    ]


def test_several_outputs_have_to_be_named():
    """With more than one output there is nothing to pick, so the graph says so instead of guessing."""

    @graph
    def ambiguous(x, y):
        return add(x=divide(x=x, y=y), y=1)

    with pytest.raises(ValueError, match='declares 2 outputs'):
        ambiguous.build()


def test_returning_a_dictionary_names_the_graph_outputs():
    """A graph can return several outputs, under the names it gives them."""

    @graph
    def both(x, y):
        result = divide(x=x, y=y)
        return {'whole': result.quotient, 'rest': result.remainder}

    results, node = run_get_node(both, x=7, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['whole'] == 3
    assert results['rest'] == 1


def test_returning_something_that_is_not_an_output_is_refused():
    """A graph returns the outputs of its tasks or its own inputs, so a plain value cannot be one of them."""

    @graph
    def returns_a_value(x, y):
        add(x=x, y=y)
        return 42

    with pytest.raises(ValueError, match='has to return one of those'):
        returns_a_value.build()


def test_a_graph_can_pass_one_of_its_inputs_on():
    """An input can be an output of the graph, which nothing produces and which is recorded as such."""
    declaration = shift_and_echo.build()

    assert declaration.outputs == {
        'total': Endpoint(task='add', port='total'),
        'echo': Endpoint(task=None, port='x'),
    }

    results, node = run_get_node(shift_and_echo, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 3
    assert results['echo'] == 1


def test_a_graph_inside_a_graph_is_placed_as_one_task():
    """The inner graph is one task carrying its own declaration, so the two graphs stay separate."""
    declaration = add_four_times.build()

    assert [node.name for node in declaration.tasks] == ['add_twice', 'add_twice_2']
    assert all(isinstance(node, SubgraphTask) for node in declaration.tasks)
    assert [node.name for node in declaration.task('add_twice').body.tasks] == ['add', 'add_2']
    assert declaration.outputs == {'total': Endpoint(task='add_twice_2', port='total')}


def test_runs_a_graph_written_inside_a_graph():
    """The inner graph runs as a child process of its own, and what it returns feeds the task after it."""
    results, node = run_get_node(add_four_times, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 9  # ((1 + 2) + 2) + 2 + 2

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()
    assert sorted(entry.link_label for entry in called) == ['add_twice', 'add_twice_2']


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(reaches_for_an_outer_task, id='task-output'),
        pytest.param(reaches_for_an_outer_input, id='graph-input'),
    ],
)
def test_a_graph_inside_another_reaches_nothing_outside_it(declaration):
    """A value from the graph around it would never be passed in, so it is refused where the graph is written."""
    with pytest.raises(ValueError, match='not part of this graph'):
        declaration.build()


def test_a_branch_is_placed_as_one_task_carrying_both_sides():
    """Both branches are declared, so the only thing a run decides is which of the two it takes."""
    declaration = double_or_not.build()
    (branch,) = declaration.tasks

    assert isinstance(branch, BranchTask)
    assert branch.name == 'branch_doubled'
    assert [node.name for node in branch.body.tasks] == ['add']
    assert [node.name for node in branch.otherwise.tasks] == ['add']
    assert declaration.inputs == {'x': (('branch_doubled', 'x'),), 'flag': (('branch_doubled', 'condition'),)}


@pytest.mark.parametrize('flag, expected', [pytest.param(True, 6, id='taken'), pytest.param(False, 3, id='not-taken')])
def test_a_branch_runs_the_side_its_condition_selects(flag, expected):
    """Which side runs is decided while the graph runs, and the branch produces what that side produced."""
    results, node = run_get_node(double_or_not, x=3, flag=flag)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == expected


@pytest.mark.parametrize(
    'flag, expected',
    [pytest.param(True, {'total': 6}, id='taken'), pytest.param(False, {}, id='not-taken')],
)
def test_a_branch_without_an_otherwise_produces_nothing_when_it_is_not_taken(flag, expected):
    """A condition that does not hold leaves the branch with nothing to return, so the output stays off."""
    results, node = run_get_node(maybe_double, x=3, flag=flag)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results.items()} == expected


def test_a_branch_that_did_not_run_leaves_out_what_takes_its_outputs():
    """A task after a branch that produced nothing has nothing to run on, so it is left out of the run too."""

    @graph
    def add_after_a_branch(x, flag):
        return add(x=branch(flag, then=doubled, x=x).total, y=1)

    results, node = run_get_node(add_after_a_branch, x=3, flag=False)

    assert node.is_finished_ok, node.exit_message
    assert dict(results) == {}
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all() == []


def test_a_branch_written_in_place_places_the_same_task():
    """The block form is the same declaration as handing over two graphs, so it reads back as one branch task."""
    declaration = double_or_not_in_place.build()
    (chosen,) = declaration.tasks

    assert isinstance(chosen, BranchTask)
    assert chosen.name == 'branch'
    assert sorted(chosen.body.outputs) == ['total']
    assert chosen.otherwise is not None
    assert sorted(chosen.otherwise.outputs) == ['total']


def test_a_body_written_in_place_takes_what_it_reaches_for_as_an_input():
    """A value from the graph around it cannot be reached at run time, so the body takes it as an input."""
    declaration = double_or_not_in_place.build()
    (chosen,) = declaration.tasks

    assert sorted(chosen.body.inputs) == ['x']
    assert declaration.inputs == {'x': (('branch', 'x'),), 'flag': (('branch', 'condition'),)}


@pytest.mark.parametrize(
    'declaration, flag, expected',
    [
        pytest.param(double_or_not_in_place, True, 6, id='taken'),
        pytest.param(double_or_not_in_place, False, 3, id='not-taken'),
        pytest.param(maybe_double_in_place, True, 6, id='one-sided-taken'),
    ],
)
def test_a_branch_written_in_place_runs(declaration, flag, expected):
    """What was written in the block runs as the branch the condition selects."""
    results, node = run_get_node(declaration, x=3, flag=flag)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == expected


def test_a_one_sided_branch_written_in_place_produces_nothing_when_it_is_not_taken():
    """Without a second block there is nothing to run, so the graph returns none of what the branch would."""
    results, node = run_get_node(maybe_double_in_place, x=3, flag=False)

    assert node.is_finished_ok, node.exit_message
    assert dict(results) == {}


@pytest.mark.parametrize(
    'declaration, inputs',
    [
        pytest.param(count_down_in_place, {'start': 3}, id='from-a-graph-input'),
        pytest.param(count_down_from_a_task, {'x': 1, 'y': 2}, id='from-a-task'),
    ],
)
def test_a_loop_written_in_place_runs(declaration, inputs):
    """The state the block carries goes round with it, and what the loop stopped on is what it returns."""
    results, node = run_get_node(declaration, **inputs)

    assert node.is_finished_ok, node.exit_message
    assert results['value'] == 0  # both count 3 down to nothing, one from an input and one from a task


def test_the_state_a_loop_carries_is_what_the_block_names():
    """Inside the block the region carries its state, and anything else says what it does carry."""
    with pytest.raises(AttributeError, match="carries \\['value'\\]"):

        @graph
        def reaches_for_nothing(start):
            with loop(condition='keep_going', value=start) as counting:
                counting.returns(value=counting.nope, keep_going=True)

        reaches_for_nothing.build()


def test_an_output_of_a_region_is_there_once_its_block_is_closed():
    """Before the block closes there is no task yet, so what it will produce is not there to take."""
    with pytest.raises(AttributeError, match='there once the block is closed'):

        @graph
        def takes_it_too_early(x, flag):
            with branch(flag) as chosen:
                chosen.returns(total=add(x=x, y=x).total)
                add(x=chosen.total, y=1)

        takes_it_too_early.build()


def test_otherwise_without_a_first_block_is_refused():
    """The second side of a branch follows the first, so asking for it first says so."""
    with pytest.raises(ValueError, match='follows the block writing the first'):

        @graph
        def other_side_first(x, flag):
            chosen = branch(flag)

            with chosen.otherwise:
                chosen.returns(total=add(x=x, y=0).total)

        other_side_first.build()


def test_calling_branch_outside_a_graph_is_refused():
    """A branch is part of a graph, so writing one anywhere else says what to do instead."""
    with pytest.raises(TypeError, match='written in the body of a `@graph`'):
        branch(True, then=doubled, x=1)


def test_a_loop_is_placed_as_one_task_carrying_its_body():
    """The body is declared once, and how many times it runs is left to the run."""
    declaration = count_down.build()
    (task_,) = declaration.tasks

    assert isinstance(task_, LoopTask)
    assert task_.name == 'loop_one_step_down'
    assert task_.condition_port == 'keep_going'
    assert [node.name for node in task_.body.tasks] == ['step_down']
    assert declaration.inputs == {
        'start': (('loop_one_step_down', 'value'),),
        'keep_going': (('loop_one_step_down', 'keep_going'),),
    }


def test_a_loop_runs_its_body_until_the_condition_turns():
    """Each run starts from what the one before it returned, so the loop reaches the value it counted down to."""
    results, node = run_get_node(count_down, start=3, keep_going=True)

    assert node.is_finished_ok, node.exit_message
    assert results['value'] == 0

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()

    assert sorted(entry.link_label for entry in called) == [
        'loop_one_step_down_iteration_0',
        'loop_one_step_down_iteration_1',
        'loop_one_step_down_iteration_2',
    ]


def test_a_loop_whose_condition_is_false_to_begin_with_runs_nothing():
    """A loop checks before it runs, so one that never had reason to go round produces nothing."""
    results, node = run_get_node(count_down, start=3, keep_going=False)

    assert node.is_finished_ok, node.exit_message
    assert dict(results) == {}
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all() == []


def test_a_loop_stops_at_the_iterations_it_is_allowed():
    """A condition that never turns would go round for ever, so the loop gives up and says it did."""

    @graph
    def count_down_briefly(start, keep_going):
        counted = loop(one_step_down, condition='keep_going', max_iterations=2, value=start, keep_going=keep_going)
        return {'value': counted.value}

    results, node = run_get_node(count_down_briefly, start=10, keep_going=True)

    assert node.is_finished_ok, node.exit_message
    assert results['value'] == 8  # 10, less one per run, of which it was allowed two
    assert len(node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()) == 2


def test_a_task_after_a_loop_waits_for_the_last_run():
    """A loop is only done once its condition turns, so what comes after it takes the value it stopped on."""

    @graph
    def count_down_then_add(start, keep_going):
        counted = loop(one_step_down, condition='keep_going', value=start, keep_going=keep_going)
        return add(x=counted.value, y=100)

    results, node = run_get_node(count_down_then_add, start=3, keep_going=True)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 100  # the loop counted 3 down to 0, and only then was `add` given it


def test_calling_loop_outside_a_graph_is_refused():
    """A loop is part of a graph, so writing one anywhere else says what to do instead."""
    with pytest.raises(TypeError, match='written in the body of a `@graph`'):
        loop(one_step_down, condition='keep_going', value=1, keep_going=True)


def test_calling_a_graph_is_refused():
    """A graph is launched rather than called, and says so."""
    with pytest.raises(TypeError, match='launched rather than called'):
        add_twice(1, 2)


def test_a_graph_can_be_submitted():
    """A graph is handed to the launchers like any other process."""
    node = submit(add_twice, x=1, y=2)

    assert isinstance(node, orm.WorkChainNode)


def test_a_task_outside_a_graph_still_runs():
    """Recording a task only happens while a graph is being built."""
    result, node = add.run_get_node(x=orm.Int(1), y=orm.Int(2))

    assert node.is_finished_ok
    assert result['total'] == 3


def test_outputs_rejects_a_bare_string():
    """A bare string would silently declare one output port per character."""
    with pytest.raises(TypeError, match='sequence of port names'):

        @task(outputs='result')
        def bare_string(x):
            return x


def test_a_graph_and_the_bodies_inside_it_carry_the_names_they_are_written_under():
    """A run is labelled with the name of its graph, which the declaration is what carries."""

    @graph
    def refine(value):
        with branch(value) as refined:
            refined.returns(total=add(x=value, y=1).total)

        with refined.otherwise:
            refined.returns(total=value)

        with subgraph() as grouped:
            grouped.returns(total=add(x=refined.total, y=2).total)

        return {'total': grouped.total}

    declaration = refine.build()

    assert declaration.identifier == 'refine'
    assert declaration.task('branch').body.identifier == 'branch'
    assert declaration.task('subgraph').body.identifier == 'subgraph'
