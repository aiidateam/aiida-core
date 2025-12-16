"""Tests for the ``Model`` class attribute of ``Entity`` subclasses."""

import datetime
import enum
import io

import numpy as np
import pytest
from pydantic import BaseModel

from aiida.common.datastructures import StashMode
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
    RemoteData,
    RemoteStashCompressedData,
    RemoteStashData,
    SinglefileData,
    Str,
    StructureData,
)

orms_to_test = (
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
    RemoteData,
    RemoteStashData,
    RemoteStashCompressedData,
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
        return ArrayData, {'attributes': {'arrays': np.array([1, 0, 0])}}
    if request.param is Bool:
        return Bool, {'attributes': {'value': True}}
    if request.param is CifData:
        return CifData, {'content': io.BytesIO(b'some-content')}
    if request.param is Data:
        return Data, {'attributes': {'source': {'uri': 'http://127.0.0.1'}}}
    if request.param is Dict:
        return Dict, {'value': {'a': 1}}
    if request.param is EnumData:
        return EnumData, {'attributes': {'member': DummyEnum.OPTION_A}}
    if request.param is Float:
        return Float, {'attributes': {'value': 1.0}}
    if request.param is FolderData:
        dirpath = tmp_path / 'folder_data'
        dirpath.mkdir()
        (dirpath / 'binary_file').write_bytes(b'byte content')
        (dirpath / 'text_file').write_text('text content')
        return FolderData, {'tree': dirpath}
    if request.param is Int:
        return Int, {'attributes': {'value': 1}}
    if request.param is JsonableData:
        return JsonableData, {'attributes': {'obj': JsonableClass({'a': 1})}}
    if request.param is List:
        return List, {'attributes': {'value': [1.0]}}
    if request.param is SinglefileData:
        return SinglefileData, {'attributes': {'content': io.BytesIO(b'some-content')}}
    if request.param is Str:
        return Str, {'attributes': {'value': 'string'}}
    if request.param is StructureData:
        return StructureData, {
            'attributes': {
                'cell': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                'pbc1': True,
                'pbc2': True,
                'pbc3': True,
                'sites': [{'kind_name': 'H', 'position': (0.0, 0.0, 0.0)}],
                'kinds': [{'name': 'H', 'mass': 1.0, 'symbols': ('H',), 'weights': (1.0,)}],
            }
        }
    if request.param is RemoteData:
        return RemoteData, {'attributes': {'remote_path': '/some/path'}}
    if request.param is RemoteStashData:
        return RemoteStashData, {'attributes': {'stash_mode': StashMode.COMPRESS_TAR}}
    if request.param is RemoteStashCompressedData:
        return RemoteStashCompressedData, {
            'attributes': {
                'stash_mode': StashMode.COMPRESS_TAR,
                'target_basepath': '/some/path',
                'source_list': ['/some/file'],
                'dereference': True,
            }
        }
    raise NotImplementedError()


@pytest.mark.parametrize(
    'required_arguments',
    orms_to_test,
    indirect=True,
)
def test_roundtrip(required_arguments, tmp_path):
    cls, kwargs = required_arguments

    # Construct instance of the entity class
    entity = cls(**kwargs)
    assert isinstance(entity, cls)

    # Get the model instance from the entity instance
    model = entity.to_model(repository_path=tmp_path)
    assert isinstance(model, BaseModel)

    # Reconstruct the entity instance from the model instance
    roundtrip = cls.from_model(model)
    assert isinstance(roundtrip, cls)

    # Get the model instance again from the reconstructed entity and check that the fields that would be passed to the
    # ORM entity constructor are identical of the original model.
    roundtrip_model = roundtrip.to_model(repository_path=tmp_path)
    original_field_values = cls.model_to_orm_field_values(model)

    def _validate_value(value):
        if isinstance(value, dict):
            return {k: _validate_value(v) for k, v in value.items()}
        if isinstance(value, io.BytesIO):
            value.seek(0)
            return value.read()
        return value

    for key, value in cls.model_to_orm_field_values(roundtrip_model).items():
        assert _validate_value(value) == _validate_value(original_field_values[key])


@pytest.mark.parametrize(
    'required_arguments',
    orms_to_test,
    indirect=True,
)
def test_roundtrip_serialization(required_arguments, tmp_path):
    cls, kwargs = required_arguments

    # Construct instance of the entity class
    entity = cls(**kwargs)
    assert isinstance(entity, cls)

    # Get the model instance from the entity instance
    serialized_entity = entity.serialize(repository_path=tmp_path, mode='python')
    entity.from_serialized(serialized_entity)
