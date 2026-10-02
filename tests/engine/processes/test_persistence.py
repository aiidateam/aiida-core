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
from aiida.orm import CalcFunctionNode, ProcessNode, WorkFunctionNode
from tests.utils.processes import NotebookWorkChain


def make_unresolvable_in_worker(monkeypatch: pytest.MonkeyPatch, cls: type) -> type:
    """Claim `__main__` origin for `cls`, making it unresolvable in a worker."""
    monkeypatch.setattr(target=cls, name='__module__', value='__main__')
    return cls


def test_load_prefers_a_carried_class_over_the_name(
    user_process_class: type[CheckpointSerializable], monkeypatch: pytest.MonkeyPatch
):
    """Class bytes restore a checkpoint whose recorded name cannot resolve."""
    carried_class = make_unresolvable_in_worker(monkeypatch, user_process_class)
    saved = carried_class('carried').save()

    assert CheckpointSerializable._get_class_bytes(saved) is not None

    # The name is now unresolvable, so anything that comes back came out of the process class bytes.
    saved[META][META__CLASS_NAME] = 'no.such.module:Missing'

    assert CheckpointSerializable.load(saved).value == 'carried'


def test_load_falls_back_to_the_name_when_carried_bytes_fail_to_load(
    user_process_class: type[CheckpointSerializable],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
):
    """A resolvable name restores the checkpoint when its class bytes are invalid."""
    carried = make_unresolvable_in_worker(monkeypatch, user_process_class)
    # Install the name in this interpreter's `__main__`, as the kernel that defined it would hold it.
    monkeypatch.setattr(target=sys.modules['__main__'], name=carried.__name__, value=carried, raising=False)
    out_state = carried(value='carried').save()

    assert out_state[META][META__CLASS_BYTES], 'the class was not carried, so there is no fallback to test'

    out_state[META][META__CLASS_BYTES] = b'not a pickle'

    with caplog.at_level(logging.WARNING, logger=persistence.LOGGER.name):
        loaded = CheckpointSerializable.load(out_state)

    assert isinstance(loaded, user_process_class)
    assert loaded.value == 'carried'
    assert 'recorded name is being followed instead' in caplog.text


def test_load_reports_both_recovery_failures():
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


def test_importable_class_records_only_its_name(user_process_class: type[CheckpointSerializable]):
    """An importable class restores from its loader identifier alone, without bytes."""
    saved = user_process_class().save()
    assert saved[META] == {META__CLASS_NAME: 'userprocess:UserProcess'}


def test_process_function_records_the_wrapped_function():
    """A process function records its wrapped function by name, without class bytes."""
    assert class_metadata(value=notebook_add.process_class) == {META__CLASS_NAME: f'{__name__}:notebook_add'}


@pytest.mark.parametrize('nested', [False, True])
def test_local_or_nested_class_records_loadable_bytes(nested: bool):
    """A class no loader identifies still round-trips through bytes under its qualname."""

    class Local(CheckpointSerializable):
        """A class without a module-level loader identifier."""

    cls: type[CheckpointSerializable] = NestedHolder.Nested if nested else Local
    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(obj=cls)
    saved = cls().save()
    metadata: dict[str, t.Any] = saved[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == f'{__name__}:{cls.__qualname__}'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is cls


@pytest.mark.parametrize('bound', [pytest.param(False, id='unbound'), pytest.param(True, id='bound-in-kernel')])
def test_main_class_records_bytes_without_a_daemon(
    user_process_class: type[CheckpointSerializable],
    monkeypatch: pytest.MonkeyPatch,
    bound: bool,
):
    """Recording needs no daemon and no resolvable name; the bytes land regardless."""
    carried: type[CheckpointSerializable] = make_unresolvable_in_worker(monkeypatch, user_process_class)
    if bound:
        monkeypatch.setattr(target=sys.modules['__main__'], name=carried.__name__, value=carried, raising=False)
    saved = carried().save()
    metadata: dict[str, t.Any] = saved[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == '__main__:UserProcess'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is carried


def test_unpicklable_capture_keeps_local_execution(caplog: pytest.LogCaptureFixture):
    """An unserializable capture warns once and falls back to name-only metadata, keeping local execution alive."""
    node: orm.Int = orm.Int(1).store()

    class ClosesOverANode(CheckpointSerializable):
        def value(self) -> orm.Int:
            return node

    caplog.set_level(logging.DEBUG, logger='aiida.persistence')
    instance: ClosesOverANode = ClosesOverANode()
    saved = instance.save()
    assert saved[META] == {META__CLASS_NAME: f'{__name__}:{ClosesOverANode.__qualname__}'}
    assert instance.value() is node
    assert any('pickling of AiiDA ORM instances' in message for message in caplog.messages)


def test_custom_loader_identifier_is_authoritative(
    user_process_class: type[CheckpointSerializable], monkeypatch: pytest.MonkeyPatch
):
    """A caller-supplied loader identifier wins over the default naming."""
    loader: loaders.DefaultObjectLoader = loaders.DefaultObjectLoader()

    def identify_object(obj: t.Any) -> str:
        assert obj is user_process_class
        return 'opaque-identifier'

    monkeypatch.setattr(target=loader, name='identify_object', value=identify_object)
    assert class_metadata(value=user_process_class, loader=loader) == {META__CLASS_NAME: 'opaque-identifier'}


@calcfunction
def notebook_add(x):
    """Increment an integer node."""
    return x + 1


@workfunction
def notebook_pass_through(x):
    """Return the input node."""
    return x


def test_installed_plugin_keeps_name_only_metadata():
    """An installed plugin records only its loader identifier, without class bytes."""
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    assert class_metadata(value=ArithmeticAddCalculation).get(META__CLASS_BYTES) is None


@pytest.mark.requires_broker
def test_workchain_defined_in_main(submit_and_await: Callable[..., ProcessNode], monkeypatch: pytest.MonkeyPatch):
    """A `__main__` workchain finishes on the daemon from carried bytes alone."""
    node = submit_and_await(make_unresolvable_in_worker(monkeypatch, NotebookWorkChain), x=orm.Int(41))

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

    monkeypatch.setattr(target=function, name='__module__', value='__main__')
    monkeypatch.setattr(target=function.process_class, name='__module__', value='__main__')

    class_bytes = class_metadata(value=function.process_class).get(META__CLASS_BYTES)
    assert isinstance(class_bytes, bytes), 'the daemon can resolve this function, so this test would prove nothing'

    node = submit_and_await(submit(function, x=orm.Int(41)))

    assert isinstance(node, node_class), 'premise: the decorator under test is the one that ran'
    assert node.is_finished_ok, node.exception
    assert node.outputs.result.value == expected
