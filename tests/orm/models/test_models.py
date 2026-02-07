"""Tests for the ``Model`` class attribute of ``Entity`` subclasses."""

import datetime
import enum
import io

import numpy as np
import pytest
from pydantic import BaseModel

from aiida.common.datastructures import StashMode
from aiida.orm import AuthInfo, Comment, Computer, Entity, Group, Log, Node, User
from aiida.orm.nodes.data import (
    ArrayData,
    Bool,
    CifData,
    ContainerizedCode,
    Data,
    Dict,
    EnumData,
    Float,
    FolderData,
    InstalledCode,
    Int,
    JsonableData,
    List,
    PortableCode,
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
    ContainerizedCode,
    Data,
    Dict,
    EnumData,
    Float,
    FolderData,
    InstalledCode,
    Int,
    JsonableData,
    List,
    PortableCode,
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
    if request.param is ContainerizedCode:
        return ContainerizedCode, {
            'label': 'containerized_echo',
            'attributes': {
                'computer': aiida_localhost.label,
                'filepath_executable': '/bin/echo',
                'image_name': 'docker://alpine:3',
                'engine_command': 'docker run {image_name}',
            },
        }
    if request.param is Data:
        return Data, {'attributes': {'source': {'uri': 'http://127.0.0.1'}}}
    if request.param is Dict:
        return Dict, {'value': {'a': 1}}
    if request.param is EnumData:
        return EnumData, {'attributes': {'member': DummyEnum.OPTION_A}}
    if request.param is Float:
        return Float, {'attributes': {'value': 1.0}}
    if request.param is FolderData:
        (tmp_path / 'binary_file').write_bytes(b'byte content')
        (tmp_path / 'text_file').write_text('text content')
        return FolderData, {'tree': tmp_path}
    if request.param is InstalledCode:
        return InstalledCode, {
            'label': 'echo',
            'attributes': {
                'computer': aiida_localhost.label,
                'filepath_executable': '/bin/echo',
            },
        }
    if request.param is Int:
        return Int, {'attributes': {'value': 1}}
    if request.param is JsonableData:
        return JsonableData, {'attributes': {'obj': JsonableClass({'a': 1})}}
    if request.param is List:
        return List, {'attributes': {'value': [1.0]}}
    if request.param is PortableCode:
        (tmp_path / 'code.sh').write_text('#!/bin/bash\necho "$@"\n')
        return PortableCode, {
            'label': 'portable_code',
            'attributes': {
                'filepath_executable': 'code.sh',
                'filepath_files': tmp_path,
            },
        }
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
def test_model_overrides(required_arguments):
    cls: type[Entity] = required_arguments[0]
    name = cls.__name__

    assert cls.Model.__qualname__ == f'{name}.Model'
    assert cls.Model.model_config.get('title') == f'{name}Model'

    assert cls.CreateModel.__qualname__ == f'{name}.CreateModel'
    assert cls.CreateModel.model_config.get('title') == f'{name}CreateModel'


@pytest.mark.parametrize(
    'required_arguments',
    [orm_class for orm_class in orms_to_test if issubclass(orm_class, Node)],
    indirect=True,
)
def test_attributes_model_overrides(required_arguments):
    cls: type[Node] = required_arguments[0]

    name = cls.__name__

    AttributesModel = cls.Model.model_fields['attributes'].annotation  # noqa: N806
    assert AttributesModel is cls.AttributesModel
    assert AttributesModel.__qualname__ == f'{name}.AttributesModel'
    assert AttributesModel.model_config.get('title') == f'{name}AttributesModel'

    AttributesCreateModel = cls.CreateModel.model_fields['attributes'].annotation  # noqa: N806
    assert AttributesCreateModel is cls.AttributesModel._as_create_model()
    assert AttributesCreateModel.__qualname__ == f'{name}.AttributesCreateModel'
    assert AttributesCreateModel.model_config.get('title') == f'{name}AttributesCreateModel'


@pytest.mark.parametrize(
    'required_arguments',
    orms_to_test,
    indirect=True,
)
def test_roundtrip(required_arguments, tmp_path):
    cls: type[Entity] = required_arguments[0]
    kwargs: dict = required_arguments[1]

    # Construct instance of the entity class
    entity: Entity = cls(**kwargs)
    assert isinstance(entity, cls)

    # Get the model instance from the entity instance
    context = {'repository_path': tmp_path} if issubclass(cls, Node) else None
    model = entity.to_model(context=context)
    assert isinstance(model, BaseModel)

    # Reconstruct the entity instance from the model instance
    roundtrip = cls.from_model(model)
    assert isinstance(roundtrip, cls)

    # Get the model instance again from the reconstructed entity and check that the fields that would be passed to the
    # ORM entity constructor are identical of the original model.
    context = {'repository_path': tmp_path} if issubclass(cls, Node) else None
    roundtrip_model = roundtrip.to_model(context=context)
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
    cls: type[Entity] = required_arguments[0]
    kwargs: dict = required_arguments[1]

    # Construct instance of the entity class
    entity = cls(**kwargs)
    assert isinstance(entity, cls)

    try:
        entity.store()
    except Exception:
        pass

    def _generate_files_dict_from_tree(tree_path):
        import os

        files_dict = {}
        for root, _, files in os.walk(tree_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, tree_path)
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                files_dict[relative_path] = io.BytesIO(file_content)
        return files_dict

    # Get the model instance from the entity instance
    if isinstance(entity, Node):
        context = {'repository_path': tmp_path}
        serialized_entity = entity.serialize(context=context, mode='python', dump_repo=True)
        files_dict = _generate_files_dict_from_tree(tmp_path)
        entity.from_serialized(serialized_entity, files=files_dict)
    else:
        serialized_entity = entity.serialize(mode='python')
        entity.from_serialized(serialized_entity)
