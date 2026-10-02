###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Checkpoint class metadata without worker-environment inspection."""

import logging
import sys
import typing as t

import pytest

from aiida import orm
from aiida.common import _callables as callables
from aiida.common import loaders
from aiida.engine import calcfunction
from aiida.engine.processes.persistence import (
    META,
    META__CLASS_BYTES,
    META__CLASS_NAME,
    CheckpointSerializable,
)


class ImportableSerializable(CheckpointSerializable):
    """An importable checkpoint class."""


class NestedHolder:
    """A qualified class name outside the default loader's identifier format."""

    class Nested(CheckpointSerializable):
        """A class serialized through its importable qualified name."""


@calcfunction
def module_level_calcfunction(value: t.Any):
    """A wrapped function that identifies its generated process class."""
    return value


def class_metadata(value: type, loader: loaders.ObjectLoader | None = None) -> dict[str, t.Any]:
    state: dict[str, t.Any] = {}
    CheckpointSerializable._record_class(
        value=value, loader=loaders.get_object_loader() if loader is None else loader, out_state=state
    )
    return state[META]


def test_importable_class_records_only_its_name():
    state: t.MutableMapping[str, t.Any] = ImportableSerializable().save()
    assert state[META] == {META__CLASS_NAME: f'{__name__}:ImportableSerializable'}


def test_process_function_records_the_wrapped_function():
    assert class_metadata(value=module_level_calcfunction.process_class) == {
        META__CLASS_NAME: f'{__name__}:module_level_calcfunction'
    }


def test_local_class_records_loadable_bytes():
    class Local(CheckpointSerializable):
        """A class without a module-level loader identifier."""

    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(obj=Local)
    metadata: dict[str, t.Any] = Local().save()[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == f'{__name__}:{Local.__qualname__}'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is Local


def test_nested_class_records_loadable_bytes():
    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(obj=NestedHolder.Nested)
    metadata: dict[str, t.Any] = NestedHolder.Nested().save()[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == f'{__name__}:NestedHolder.Nested'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is NestedHolder.Nested


@pytest.mark.parametrize('bound', [pytest.param(False, id='unbound'), pytest.param(True, id='bound-in-kernel')])
def test_main_class_records_bytes_without_a_supervisor(monkeypatch: pytest.MonkeyPatch, bound: bool):
    class NotebookClass(CheckpointSerializable):
        """A class compiled in a notebook's interpreter."""

    NotebookClass.__module__ = '__main__'
    NotebookClass.__qualname__ = 'NotebookClass'
    if bound:
        monkeypatch.setattr(sys.modules['__main__'], 'NotebookClass', NotebookClass, raising=False)
    metadata: dict[str, t.Any] = NotebookClass().save()[META]
    assert set(metadata) == {META__CLASS_NAME, META__CLASS_BYTES}
    assert metadata[META__CLASS_NAME] == '__main__:NotebookClass'
    assert callables.loads(payload=metadata[META__CLASS_BYTES]) is NotebookClass


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


def test_custom_loader_identifier_is_authoritative():
    class OpaqueLoader(loaders.ObjectLoader):
        def identify_object(self, obj: t.Any) -> str:
            assert obj is ImportableSerializable
            return 'opaque-identifier'

        def load_object(self, identifier: str) -> type:
            assert identifier == 'opaque-identifier'
            return ImportableSerializable

    assert class_metadata(value=ImportableSerializable, loader=OpaqueLoader()) == {
        META__CLASS_NAME: 'opaque-identifier'
    }
