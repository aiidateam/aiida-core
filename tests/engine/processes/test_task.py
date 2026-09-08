###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ``task`` decorator and the ``TaskSpec`` it declares."""

from __future__ import annotations

from typing import TypedDict

import pytest

from aiida import orm
from aiida.engine import TaskSpec, ToContext, WorkChain, run_get_node, submit, task

pytestmark = pytest.mark.requires_broker


@task
def count(items):
    """Take and return plain Python values."""
    return len(items)


@task(outputs=['total', 'product'])
def sum_product(x, y):
    """Declare two named outputs and return them positionally."""
    return x + y, x * y


class Stats(TypedDict):
    """Return annotation declaring one output socket per field."""

    minimum: int
    maximum: int


@task
def stats(items) -> Stats:
    return {'minimum': min(items), 'maximum': max(items)}


def test_plain_python_values():
    """A task takes and returns plain Python values, stored as the corresponding data nodes."""
    result, node = run_get_node(count, items=[1, 2, 3])

    assert node.is_finished_ok, node.exit_message
    assert isinstance(result, orm.Int)
    assert result == 3


def test_task_spec_declares_ports():
    """The decorator produces a declaration of the task, not just a callable."""
    spec = sum_product.task_spec

    assert spec.identifier == 'sum_product'
    assert spec.process_class is sum_product.process_class
    assert set(spec.inputs.keys()) >= {'x', 'y'}
    assert list(spec.outputs.keys()) == ['total', 'product']


def test_task_spec_round_trip():
    """The declaration is a value that can be written out and read back."""
    spec = sum_product.task_spec
    restored = TaskSpec.from_dict(spec.to_dict())

    assert restored == spec
    assert restored.process_class is sum_product.process_class
    assert list(restored.outputs.keys()) == ['total', 'product']


def test_executor_reference_resolves_process_class():
    """A process function is referenced by its importable name, and resolves back to its process class."""
    reference = sum_product.task_spec.executor

    assert reference.module == __name__
    assert reference.name == 'sum_product'
    assert reference.load() is sum_product.process_class


def test_declared_outputs_from_kwarg():
    """``outputs=`` declares named output ports, onto which a returned tuple is mapped in order."""
    results, node = run_get_node(sum_product, x=2, y=3)

    assert node.is_finished_ok, node.exit_message
    assert set(results) == {'total', 'product'}
    assert results['total'] == 5
    assert results['product'] == 6


def test_declared_outputs_from_return_annotation():
    """A ``TypedDict`` return annotation declares one output port per field."""
    assert list(stats.task_spec.outputs.keys()) == ['minimum', 'maximum']

    results, node = run_get_node(stats, items=[3, 1, 2])

    assert node.is_finished_ok, node.exit_message
    assert results['minimum'] == 1
    assert results['maximum'] == 3


@task(outputs=['first', 'second'])
def wrong_arity(x):
    """Return fewer values than the declared outputs."""
    return x


def test_returned_values_must_match_declared_outputs():
    """Returning a different number of values than declared outputs is reported, not silently dropped."""
    with pytest.raises(ValueError, match='declares 2 outputs'):
        run_get_node(wrong_arity, x=1)


def test_outputs_rejects_a_bare_string():
    """A bare string would silently declare one output port per character."""
    with pytest.raises(TypeError, match='sequence of port names'):

        @task(outputs='result')
        def bare_string(x):
            return x


def test_submit_standalone():
    """A task can be submitted on its own."""
    node = submit(count, items=[1, 2, 3])

    assert isinstance(node, orm.CalcFunctionNode)


def test_submit_from_process():
    """A running workflow dispatches a task as a called child, under the name it gives it."""

    class ParentWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.outline(cls.submit_child, cls.collect)
            spec.outputs.dynamic = True

        def submit_child(self):
            child = self.submit(sum_product, x=2, y=3, metadata={'call_link_label': 'arithmetic'})
            return ToContext(arithmetic=child)

        def collect(self):
            self.out('total', self.ctx.arithmetic.outputs.total)

    results, node = run_get_node(ParentWorkChain)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5
