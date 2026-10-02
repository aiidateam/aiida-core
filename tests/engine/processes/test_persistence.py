###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.engine.processes.persistence`."""

import logging
import pickle
import sys
import textwrap
import time
import typing as t
from collections.abc import Callable

import pytest

from aiida import orm
from aiida.common import _callables as callables
from aiida.common import loaders
from aiida.engine import calcfunction, workfunction
from aiida.engine.processes import persistence
from aiida.engine.processes.persistence import (
    META,
    META__CLASS_BYTES,
    META__CLASS_NAME,
    CheckpointSerializable,
)
from aiida.orm import CalcFunctionNode, InstalledCode, ProcessNode, WorkFunctionNode
from tests.utils.processes import NotebookWorkChain


def test_load_prefers_a_carried_class_over_the_name(
    user_serializable: type[CheckpointSerializable], unresolvable_in_main
):
    """Class bytes restore a checkpoint whose recorded name cannot resolve."""
    saved = unresolvable_in_main(user_serializable)('carried').save()

    assert CheckpointSerializable._get_class_bytes(saved) is not None

    # The name is now unresolvable, so anything that comes back came out of the process class bytes.
    saved[META][META__CLASS_NAME] = 'no.such.module:Missing'

    assert CheckpointSerializable.load(saved).value == 'carried'


def test_load_falls_back_to_the_name_when_the_carried_class_will_not_load(
    user_serializable: type[CheckpointSerializable],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    unresolvable_in_main,
):
    """A resolvable name restores the checkpoint when its class bytes are invalid."""
    carried = unresolvable_in_main(user_serializable)
    monkeypatch.setattr(sys.modules['__main__'], carried.__name__, carried, raising=False)
    out_state = carried(value='carried').save()

    assert out_state[META][META__CLASS_BYTES], 'the class was not carried, so there is no fallback to test'

    out_state[META][META__CLASS_BYTES] = b'not a pickle'

    with caplog.at_level(logging.WARNING, logger=persistence.LOGGER.name):
        loaded = CheckpointSerializable.load(out_state)

    assert isinstance(loaded, user_serializable)
    assert loaded.value == 'carried'
    assert 'recorded name is being followed instead' in caplog.text


def test_load_reports_the_carried_failure_when_the_name_is_gone_too():
    """Recovery failure includes both errors, environment checks and the deserialization cause."""
    saved: dict[str, t.Any] = {
        META: {META__CLASS_NAME: '__main__:NotebookClass', META__CLASS_BYTES: b'not a pickle at all'}
    }
    with pytest.raises(ImportError) as info:
        CheckpointSerializable.load(saved)

    message: str = str(info.value)
    assert isinstance(info.value.__cause__, ValueError)
    assert isinstance(info.value.__cause__.__cause__, pickle.UnpicklingError)
    assert 'invalid load key' in str(info.value.__cause__)
    assert message.startswith('Checkpoint class `__main__:NotebookClass` could not be recovered. ')
    assert f'Deserialization failed: {info.value.__cause__}.' in message
    assert 'Identifier loading failed: ' in message
    assert 'Install referenced modules or add their directories to `PYTHONPATH`.' in message
    assert message.endswith('Use compatible Python and `cloudpickle` versions, then run `verdi daemon restart`.')


class NestedHolder:
    """Container for a nested checkpoint class."""

    class Nested(CheckpointSerializable):
        """A class serialized through its importable qualified name."""


def class_metadata(value: type, loader: loaders.ObjectLoader | None = None) -> dict[str, t.Any]:
    state: dict[str, t.Any] = {}
    CheckpointSerializable._record_class(
        value=value, loader=loaders.get_object_loader() if loader is None else loader, out_state=state
    )
    return state[META]


def test_importable_class_records_only_its_name(user_serializable: type[CheckpointSerializable]):
    assert user_serializable().save()[META] == {META__CLASS_NAME: 'usercheckpoint:UserSerializable'}


def test_process_function_records_the_wrapped_function():
    assert class_metadata(value=notebook_add.process_class) == {META__CLASS_NAME: f'{__name__}:notebook_add'}


@pytest.mark.parametrize('nested', [pytest.param(False, id='local'), pytest.param(True, id='nested')])
def test_local_or_nested_class_records_loadable_bytes(nested: bool):
    class Local(CheckpointSerializable):
        """A class without a module-level loader identifier."""

    cls: type[CheckpointSerializable] = NestedHolder.Nested if nested else Local
    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(obj=cls)
    metadata: dict[str, t.Any] = cls().save()[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == f'{__name__}:{cls.__qualname__}'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is cls


@pytest.mark.parametrize('bound', [pytest.param(False, id='unbound'), pytest.param(True, id='bound-in-kernel')])
def test_main_class_records_bytes_without_a_supervisor(
    user_serializable: type[CheckpointSerializable],
    unresolvable_in_main,
    monkeypatch: pytest.MonkeyPatch,
    bound: bool,
):
    carried: type[CheckpointSerializable] = unresolvable_in_main(user_serializable)
    if bound:
        monkeypatch.setattr(sys.modules['__main__'], carried.__name__, carried, raising=False)
    metadata: dict[str, t.Any] = carried().save()[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == '__main__:UserSerializable'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is carried


def test_unpicklable_capture_keeps_local_execution(caplog: pytest.LogCaptureFixture):
    node: orm.Int = orm.Int(1).store()

    class ClosesOverANode(CheckpointSerializable):
        def value(self) -> orm.Int:
            return node

    caplog.set_level(logging.DEBUG, logger='aiida.persistence')
    instance: ClosesOverANode = ClosesOverANode()
    assert instance.save()[META] == {META__CLASS_NAME: f'{__name__}:{ClosesOverANode.__qualname__}'}
    assert instance.value() is node
    assert any('pickling of AiiDA ORM instances' in message for message in caplog.messages)


def test_custom_loader_identifier_is_authoritative(
    user_serializable: type[CheckpointSerializable], monkeypatch: pytest.MonkeyPatch
):
    loader: loaders.DefaultObjectLoader = loaders.DefaultObjectLoader()

    def identify_object(obj: t.Any) -> str:
        assert obj is user_serializable
        return 'opaque-identifier'

    monkeypatch.setattr(loader, 'identify_object', identify_object)
    assert class_metadata(value=user_serializable, loader=loader) == {META__CLASS_NAME: 'opaque-identifier'}


@calcfunction
def notebook_add(x):
    """Increment an integer node."""
    return x + 1


@workfunction
def notebook_pass_through(x):
    """Return the input node."""
    return x


@pytest.mark.requires_broker
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
@pytest.mark.requires_broker
def test_process_function_defined_in_main(
    function: Callable[..., t.Any],
    node_class: type[ProcessNode],
    expected: int,
    submit_and_await: Callable[..., ProcessNode],
    monkeypatch: pytest.MonkeyPatch,
):
    """Both function decorators recover their generated process class on the worker."""
    from aiida.engine import submit

    monkeypatch.setattr(function, '__module__', '__main__')
    monkeypatch.setattr(function.process_class, '__module__', '__main__')

    assert isinstance(class_metadata(value=function.process_class).get(META__CLASS_BYTES), bytes), (
        'the daemon can resolve this function, so this test would prove nothing'
    )

    node = submit_and_await(submit(function, x=orm.Int(41)))

    assert isinstance(node, node_class), 'premise: the decorator under test is the one that ran'
    assert node.is_finished_ok, node.exception
    assert node.outputs.result.value == expected


@pytest.mark.requires_broker
def test_an_installed_plugin_still_travels_by_name(
    submit_and_await: Callable[..., ProcessNode], aiida_code_installed: Callable[..., InstalledCode]
):
    """An installed plugin runs with name-only class metadata."""
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    assert class_metadata(value=ArithmeticAddCalculation).get(META__CLASS_BYTES) is None

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add')
    builder = code.get_builder()
    builder.x = orm.Int(2)
    builder.y = orm.Int(40)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.sum.value == 42
    assert node.process_type == 'aiida.calculations:core.arithmetic.add'


@pytest.mark.requires_broker
def test_calcjob_defined_in_main(
    submit_and_await: Callable[..., ProcessNode],
    unresolvable_in_main,
    aiida_code_installed: Callable[..., InstalledCode],
):
    """The parser uses the recovered runtime class to parse a notebook-defined calculation."""
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    class MainCalcJob(ArithmeticAddCalculation):
        """Notebook-style arithmetic calculation."""

        @classmethod
        def define(cls, spec):
            super().define(spec)

    unresolvable_in_main(MainCalcJob)

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add')
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
