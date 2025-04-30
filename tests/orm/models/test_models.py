"""Tests for the ``Model`` class attribute of ``Entity`` subclasses."""

import datetime
import enum
import io

import numpy as np
import pytest
from pydantic import BaseModel

from aiida.orm import AuthInfo, Comment, Computer, Group, Log, User
from aiida.orm.nodes.data import (
    ArrayData,
    Bool,
    CifData,
    Data,
    Dict,
    EnumData,
    Float,
    FolderData,
    Int,
    JsonableData,
    List,
    SinglefileData,
    Str,
    StructureData,
)


class DummyEnum(enum.Enum):
    """Dummy enum for testing."""

    OPTION_A = 'a'
    OPTION_B = 'b'


class JsonableClass:
    """Dummy class that implements the required interface."""

    def __init__(self, data):
        """Construct a new object."""
        self._data = data

    @property
    def data(self):
        """Return the data of this instance."""
        return self._data

    def as_dict(self):
        """Represent the object as a JSON-serializable dictionary."""
        return {
            'data': self._data,
        }

    @classmethod
    def from_dict(cls, dictionary):
        """Reconstruct an instance from a serialized version."""
        return cls(dictionary['data'])


@pytest.fixture
def required_arguments(request, default_user, aiida_localhost, tmp_path):
    if request.param is AuthInfo:
        return AuthInfo, {'user': default_user, 'computer': aiida_localhost}
    if request.param is Comment:
        return Comment, {'user': default_user, 'node': Data().store(), 'content': ''}
    if request.param is Computer:
        return Computer, {'label': 'localhost'}
    if request.param is Group:
        return Group, {'label': 'group'}
    if request.param is Log:
        return Log, {
            'time': datetime.datetime.now(),
            'loggername': 'logger',
            'levelname': 'REPORT',
            'message': 'message',
            'dbnode_id': Data().store().pk,
        }
    if request.param is User:
        return User, {'email': 'test@localhost'}
    if request.param is ArrayData:
        return ArrayData, {'arrays': np.array([1, 0, 0])}
    if request.param is Bool:
        return Bool, {'value': True}
    if request.param is CifData:
        return CifData, {'content': io.BytesIO(b'some-content')}
    if request.param is Data:
        return Data, {'source': {'uri': 'http://127.0.0.1'}}
    if request.param is Dict:
        return Dict, {'value': {'a': 1}}
    if request.param is EnumData:
        return EnumData, {'member': DummyEnum.OPTION_A}
    if request.param is Float:
        return Float, {'value': 1.0}
    if request.param is FolderData:
        dirpath = tmp_path / 'folder_data'
        dirpath.mkdir()
        (dirpath / 'binary_file').write_bytes(b'byte content')
        (dirpath / 'text_file').write_text('text content')
        return FolderData, {'tree': dirpath}
    if request.param is Int:
        return Int, {'value': 1}
    if request.param is JsonableData:
        return JsonableData, {'obj': JsonableClass({'a': 1})}
    if request.param is List:
        return List, {'value': [1.0]}
    if request.param is SinglefileData:
        return SinglefileData, {'content': io.BytesIO(b'some-content')}
    if request.param is Str:
        return Str, {'value': 'string'}
    if request.param is StructureData:
        return StructureData, {'cell': [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}

    raise NotImplementedError()


@pytest.mark.parametrize(
    'required_arguments',
    (
        AuthInfo,
        Comment,
        Computer,
        Group,
        Log,
        User,
        SinglefileData,
        ArrayData,
        Bool,
        CifData,
        Data,
        Dict,
        EnumData,
        Float,
        FolderData,
        Int,
        JsonableData,
        List,
        SinglefileData,
        Str,
        StructureData,
    ),
    indirect=True,
)
def test_roundtrip(required_arguments):
    cls, kwargs = required_arguments

    # Construct instance of the entity class
    entity = cls(**kwargs)
    assert isinstance(entity, cls)

    # Get the model instance from the entity instance
    model = entity.to_model()
    assert isinstance(model, BaseModel)

    # Reconstruct the entity instance from the model instance
    roundtrip = cls.from_model(model)
    assert isinstance(roundtrip, cls)

    # Get the model instance again from the reconstructed entity and check that the fields that would be passed to the
    # ORM entity constructor are identical of the original model. The ``model_to_orm_field_values`` excludes values of
    # fields that define ``exclude_to_orm=True`` because these can change during roundtrips. This because these
    # typically correspond to entity fields that have defaults set on the database level, e.g., UUIDs.
    roundtrip_model = roundtrip.to_model()
    original_field_values = cls.model_to_orm_field_values(model)

    for key, value in cls.model_to_orm_field_values(roundtrip_model).items():
        if isinstance(value, io.BytesIO):
            assert value.read() == original_field_values[key].read()
        elif cls is ArrayData and key == 'arrays':
            for array_name, array in value.items():
                assert np.array_equal(array, original_field_values[key][array_name])
        else:
            assert value == original_field_values[key]
