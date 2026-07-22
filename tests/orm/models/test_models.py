"""Tests for the ``Model`` class attribute of ``orm.Entity`` subclasses."""

import datetime
import enum
import io
import typing as t

import numpy as np
import pytest
from plumpy import get_object_loader
from typing_extensions import NotRequired

from aiida import orm
from aiida.common.datastructures import StashMode
from aiida.common.exceptions import UnsupportedSchemaError

orm_to_test = (
    orm.AuthInfo,
    orm.Comment,
    orm.Computer,
    orm.Group,
    orm.Log,
    orm.User,
    orm.ArrayData,
    orm.Bool,
    orm.CifData,
    orm.ContainerizedCode,
    orm.Data,
    orm.Dict,
    orm.EnumData,
    orm.Float,
    orm.FolderData,
    orm.InstalledCode,
    orm.Int,
    orm.JsonableData,
    orm.List,
    orm.PortableCode,
    orm.SinglefileData,
    orm.Str,
    orm.StructureData,
    orm.RemoteData,
    orm.RemoteStashCompressedData,
    orm.XyData,
)

entities_to_test = tuple(orm_class for orm_class in orm_to_test if not issubclass(orm_class, orm.Node))

nodes_to_test = tuple(orm_class for orm_class in orm_to_test if issubclass(orm_class, orm.Node))


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


class RequiredEntityArguments(t.TypedDict):
    cls: type[orm.Entity]
    kwargs: dict


class RequiredNodeArguments(t.TypedDict):
    cls: type[orm.Node]
    write_model_payload: dict
    constructor_model_payload: NotRequired[dict]


@pytest.fixture
def required_arguments(request, default_user, aiida_localhost, tmp_path):
    if request.param is orm.AuthInfo:
        random_email = f'user{orm.User.collection.count() + 1}@aiida'
        return {
            'cls': orm.AuthInfo,
            'kwargs': {
                'user': orm.User(email=random_email).store(),
                'computer': aiida_localhost,
            },
        }
    if request.param is orm.Comment:
        return {
            'cls': orm.Comment,
            'kwargs': {
                'user': default_user,
                'node': orm.Data().store(),
                'content': '',
            },
        }
    if request.param is orm.Computer:
        return {
            'cls': orm.Computer,
            'kwargs': {
                'label': 'test_localhost',
                'hostname': 'test_localhost',
                'transport_type': 'core.local',
                'scheduler_type': 'core.direct',
            },
        }
    if request.param is orm.Group:
        return {
            'cls': orm.Group,
            'kwargs': {
                'label': 'group',
            },
        }
    if request.param is orm.Log:
        return {
            'cls': orm.Log,
            'kwargs': {
                'time': datetime.datetime.now(),
                'loggername': 'logger',
                'levelname': 'REPORT',
                'message': 'message',
                'node': orm.Data().store(),
            },
        }
    if request.param is orm.User:
        return {
            'cls': orm.User,
            'kwargs': {'email': 'user42@aiida'},
        }
    if request.param is orm.ArrayData:
        buffered_array = io.BytesIO()
        np.save(buffered_array, np.array([1, 0, 0]), allow_pickle=False)
        buffered_array.seek(0)

        def assert_derived_array_properties(node: orm.ArrayData):
            assert node.base.attributes.all == {'array|test_array': [3]}
            assert node.get_array('test_array').tolist() == [1, 0, 0]

        return {
            'cls': orm.ArrayData,
            'write_model_payload': {
                'attributes': {'array|test_array': [3]},
                'files': {'test_array.npy': lambda: buffered_array},
                'assert_derived': assert_derived_array_properties,
            },
            'constructor_model_payload': {
                'args': {'arrays': {'test_array': [1, 0, 0]}},
            },
        }
    if request.param is orm.Bool:
        return {
            'cls': orm.Bool,
            'write_model_payload': {
                'attributes': {'value': True},
            },
            'constructor_model_payload': {
                'args': {'value': True},
            },
        }
    if request.param is orm.CifData:

        def assert_derived_cif_properties(node: orm.CifData):
            assert node.filename == 'structure.cif'
            assert node.md5 == '771ee48ec137aba8a57328a1df42fcf4'
            assert node.get_content(mode='r') == 'data_test\nloop_\n_atom_site_label\nH1\n'

        return {
            'cls': orm.CifData,
            'write_model_payload': {
                'attributes': {
                    'scan_type': 'standard',
                    'parse_policy': 'eager',
                },
                'files': {'structure.cif': lambda: io.StringIO('data_test\nloop_\n_atom_site_label\nH1\n')},
                'assert_derived': assert_derived_cif_properties,
            },
            'constructor_model_payload': {
                'args': {
                    'filename': 'structure.cif',
                    'content': 'data_test\nloop_\n_atom_site_label\nH1\n',
                },
            },
        }
    if request.param is orm.ContainerizedCode:
        return {
            'cls': orm.ContainerizedCode,
            'write_model_payload': {
                'label': 'containerized_echo',
                'computer': aiida_localhost.pk,
                'attributes': {
                    'filepath_executable': '/bin/echo',
                    'image_name': 'docker://alpine:3',
                    'engine_command': 'docker run {image_name}',
                },
            },
            'constructor_model_payload': {
                'label': 'containerized_echo',
                'args': {
                    'computer': aiida_localhost.label,
                    'filepath_executable': '/bin/echo',
                    'image_name': 'docker://alpine:3',
                    'engine_command': 'docker run {image_name}',
                },
            },
        }
    if request.param is orm.Data:
        return {
            'cls': orm.Data,
            'write_model_payload': {
                'attributes': {
                    'source': {'uri': 'http://127.0.0.1'},
                },
            },
            'constructor_model_payload': {
                'args': {'source': {'uri': 'http://127.0.0.1'}},
            },
        }
    if request.param is orm.Dict:
        return {
            'cls': orm.Dict,
            'write_model_payload': {
                'attributes': {'a': 1, 'b': 2},
            },
            'constructor_model_payload': {
                'args': {'value': {'a': 1, 'b': 2}},
            },
        }
    if request.param is orm.EnumData:
        return {
            'cls': orm.EnumData,
            'write_model_payload': {
                'attributes': {
                    'name': 'OPTION_A',
                    'value': 'a',
                    'identifier': get_object_loader().identify_object(DummyEnum),
                },
            },
            'constructor_model_payload': {
                'args': {'member': DummyEnum.OPTION_A},
            },
        }
    if request.param is orm.Float:
        return {
            'cls': orm.Float,
            'write_model_payload': {
                'attributes': {'value': 1.0},
            },
            'constructor_model_payload': {
                'args': {'value': 1.0},
            },
        }
    if request.param is orm.FolderData:
        (tmp_path / 'binary_file').write_bytes(b'byte content')
        (tmp_path / 'text_file').write_text('text content')

        def assert_derived_folder_properties(node: orm.FolderData):
            assert node.get_object_content('binary_file', mode='rb') == b'byte content'
            assert node.get_object_content('text_file', mode='r') == 'text content'

        return {
            'cls': orm.FolderData,
            'write_model_payload': {
                'attributes': {},
                'files': {
                    'binary_file': lambda: io.BytesIO(b'byte content'),
                    'text_file': lambda: io.StringIO('text content'),
                },
                'assert_derived': assert_derived_folder_properties,
            },
            'constructor_model_payload': {
                'args': {'tree': str(tmp_path)},
            },
        }
    if request.param is orm.InstalledCode:
        return {
            'cls': orm.InstalledCode,
            'write_model_payload': {
                'label': 'echo',
                'computer': aiida_localhost.pk,
                'attributes': {
                    'default_calc_job_plugin': 'core.arithmetic.add',
                    'filepath_executable': '/bin/echo',
                },
            },
            'constructor_model_payload': {
                'label': 'echo',
                'args': {
                    'computer': aiida_localhost.label,
                    'filepath_executable': '/bin/echo',
                },
            },
        }
    if request.param is orm.Int:
        return {
            'cls': orm.Int,
            'write_model_payload': {
                'attributes': {'value': 1},
            },
            'constructor_model_payload': {
                'args': {'value': 1},
            },
        }
    if request.param is orm.JsonableData:
        return {
            'cls': orm.JsonableData,
            'write_model_payload': {
                'attributes': {
                    'data': 1,
                    '@class': 'JsonableClass',
                    '@module': 'tests.orm.models.test_models',
                },
            },
            'constructor_model_payload': {
                'args': {
                    'obj': JsonableClass(1),
                }
            },
        }
    if request.param is orm.List:
        return {
            'cls': orm.List,
            'write_model_payload': {
                'attributes': {'list': [1, 2, 3]},
            },
            'constructor_model_payload': {
                'args': {'list': [1, 2, 3]},
            },
        }
    if request.param is orm.PortableCode:
        (tmp_path / 'code.sh').write_text('#!/bin/bash\necho "$@"\n')
        return {
            'cls': orm.PortableCode,
            'write_model_payload': {
                'attributes': {
                    'filepath_executable': 'code.sh',
                },
            },
            'constructor_model_payload': {
                'label': 'portable_echo',
                'args': {
                    'filepath_executable': 'code.sh',
                    'filepath_files': str(tmp_path),
                },
            },
        }
    if request.param is orm.SinglefileData:

        def assert_derived_singlefile_properties(node: orm.SinglefileData):
            assert node.filename == 'file.txt'
            assert node.get_content(mode='r') == 'singlefile-content'

        return {
            'cls': orm.SinglefileData,
            'write_model_payload': {
                'attributes': {},
                'files': {'file.txt': lambda: io.StringIO('singlefile-content')},
                'assert_derived': assert_derived_singlefile_properties,
            },
            'constructor_model_payload': {
                'args': {
                    'filename': 'file.txt',
                    'content': 'some-content',
                },
            },
        }
    if request.param is orm.Str:
        return {
            'cls': orm.Str,
            'write_model_payload': {
                'attributes': {'value': 'string'},
            },
            'constructor_model_payload': {
                'args': {
                    'value': 'string',
                },
            },
        }
    if request.param is orm.StructureData:
        return {
            'cls': orm.StructureData,
            'write_model_payload': {
                'attributes': {
                    'cell': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    'pbc1': True,
                    'pbc2': True,
                    'pbc3': True,
                    'sites': [{'kind_name': 'H', 'position': (0.0, 0.0, 0.0)}],
                    'kinds': [{'name': 'H', 'mass': 1.0, 'symbols': ('H',), 'weights': (1.0,)}],
                }
            },
            'constructor_model_payload': {
                'args': {
                    'cell': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    'pbc1': True,
                    'pbc2': True,
                    'pbc3': True,
                    'sites': [{'kind_name': 'H', 'position': (0.0, 0.0, 0.0)}],
                    'kinds': [{'name': 'H', 'mass': 1.0, 'symbols': ('H',), 'weights': (1.0,)}],
                }
            },
        }
    if request.param is orm.RemoteData:
        return {
            'cls': orm.RemoteData,
            'write_model_payload': {
                'computer': aiida_localhost.pk,
                'attributes': {
                    'remote_path': '/some/path',
                },
            },
            'constructor_model_payload': {
                'args': {
                    'computer': aiida_localhost,
                    'remote_path': '/some/path',
                },
            },
        }
    if request.param is orm.RemoteStashCompressedData:
        return {
            'cls': orm.RemoteStashCompressedData,
            'write_model_payload': {
                'attributes': {
                    'stash_mode': StashMode.COMPRESS_TAR,
                    'target_basepath': '/some/path',
                    'source_list': ['/some/file'],
                    'dereference': True,
                }
            },
            'constructor_model_payload': {
                'args': {
                    'stash_mode': StashMode.COMPRESS_TAR,
                    'target_basepath': '/some/path',
                    'source_list': ['/some/file'],
                    'dereference': True,
                }
            },
        }
    if request.param is orm.XyData:
        buffered_x_array = io.BytesIO()
        np.save(buffered_x_array, np.array([1, 2, 3]), allow_pickle=False)
        buffered_x_array.seek(0)

        buffered_y_array0 = io.BytesIO()
        np.save(buffered_y_array0, np.array([4, 5, 6]), allow_pickle=False)
        buffered_y_array0.seek(0)

        buffered_y_array1 = io.BytesIO()
        np.save(buffered_y_array1, np.array([7, 8, 9]), allow_pickle=False)
        buffered_y_array1.seek(0)

        def assert_derived_array_properties(node: orm.ArrayData):
            assert node.base.attributes.all == {
                'x_name': 'test_x',
                'x_units': 'm',
                'y_names': ['test_1', 'test_2'],
                'y_units': ['m', 'm'],
                'array|x_array': [3],
                'array|y_array_0': [3],
                'array|y_array_1': [3],
            }
            assert node.get_array('x_array').tolist() == [1, 2, 3]
            assert node.get_array('y_array_0').tolist() == [4, 5, 6]
            assert node.get_array('y_array_1').tolist() == [7, 8, 9]

        return {
            'cls': orm.XyData,
            'write_model_payload': {
                'attributes': {
                    'x_name': 'test_x',
                    'x_units': 'm',
                    'y_names': ['test_1', 'test_2'],
                    'y_units': ['m', 'm'],
                    'array|x_array': [3],
                    'array|y_array_0': [3],
                    'array|y_array_1': [3],
                },
                'files': {
                    'x_array.npy': lambda: buffered_x_array,
                    'y_array_0.npy': lambda: buffered_y_array0,
                    'y_array_1.npy': lambda: buffered_y_array1,
                },
                'assert_derived': assert_derived_array_properties,
            },
            'constructor_model_payload': {
                'args': {
                    'x_name': 'test_x',
                    'x_units': 'm',
                    'y_names': ['test_1', 'test_2'],
                    'y_units': ['m', 'm'],
                    'x_array': [1, 2, 3],
                    'y_arrays': [[4, 5, 6], [7, 8, 9]],
                }
            },
        }
    raise NotImplementedError()


def test_minimal_model_idempotency():
    DynamicModel = orm.Int.ReadModel._as_minimal_model()  # noqa: N806
    RepeatedDynamicModel = DynamicModel._as_minimal_model()  # noqa: N806
    assert RepeatedDynamicModel is DynamicModel


@pytest.mark.parametrize(
    'required_arguments',
    orm_to_test,
    indirect=True,
)
def test_model_overrides(required_arguments: RequiredEntityArguments):
    cls = required_arguments['cls']
    name = cls.__name__

    assert cls.ReadModel.__qualname__ == f'{name}.ReadModel'
    assert cls.ReadModel.model_config.get('title') == f'{name}ReadModel'

    assert cls.WriteModel.__qualname__ == f'{name}.WriteModel'
    assert cls.WriteModel.model_config.get('title') == f'{name}WriteModel'


def _clean_and_sort(dictionary: dict) -> dict:
    return {
        key: _clean_and_sort(value) if isinstance(value, dict) else value
        for key, value in sorted(dictionary.items())
        if value is not None
        and key != '_aiida_hash'  # the hash is derived from the node uuid, which is expected to be different
    }


def _check(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        left = _clean_and_sort(left)
        right = _clean_and_sort(right)
    assert left == right, f'{left!r}\n{right!r}'


def _check_all(serialized: dict, entity: orm.Entity):
    for key, value in serialized.items():
        field = getattr(entity, key)
        if isinstance(field, datetime.datetime):
            field = field.isoformat()
        elif field is not None and key in {'user', 'computer', 'node'}:
            field = field.pk
        _check(value, field)


@pytest.mark.parametrize(
    'required_arguments',
    entities_to_test,
    indirect=True,
)
def test_stored_entity_serialization(required_arguments: RequiredEntityArguments):
    cls = required_arguments['cls']
    kwargs = required_arguments['kwargs']
    entity = cls(**kwargs)
    entity.store()
    serialized = entity.serialize(mode='json')
    _check_all(serialized, entity)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_stored_node_serialization(required_arguments: RequiredNodeArguments):
    cls = required_arguments['cls']
    kwargs = required_arguments['constructor_model_payload']
    kwargs.update(kwargs.pop('args', {}))
    node = cls(**kwargs)
    node.store()
    serialized = node.serialize(mode='json')
    _check_all(serialized, node)


@pytest.mark.parametrize(
    'process_generator',
    [
        pytest.param('generate_calculation_node_add', id='CalcJobNode'),
        pytest.param('generate_workchain_multiply_add', id='WorkChainNode'),
    ],
)
def test_process_node_serialization(request, process_generator):
    generator = request.getfixturevalue(process_generator)
    node = generator()
    node.store()
    serialized = node.serialize(mode='json')
    _check_all(serialized, node)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_node_attributes_model_overrides(required_arguments: RequiredNodeArguments):
    cls = required_arguments['cls']

    name = cls.__name__

    AttributesModel = cls.ReadModel.model_fields['attributes'].annotation  # noqa: N806
    assert AttributesModel is cls.AttributesModel
    assert AttributesModel.__qualname__ == f'{name}.AttributesModel'
    assert AttributesModel.model_config.get('title') == f'{name}AttributesModel'

    AttributesWriteModel = cls.WriteModel.model_fields['attributes'].annotation  # noqa: N806
    assert AttributesWriteModel.__qualname__ == f'{name}.AttributesWriteModel'
    assert AttributesWriteModel.model_config.get('title') == f'{name}AttributesWriteModel'


def _validate_value(value):
    if isinstance(value, dict):
        return {k: _validate_value(v) for k, v in value.items()}
    if isinstance(value, io.BytesIO):
        value.seek(0)
        return value.read()
    return value


# NOTE: Logs are automatically stored, so `to_model` would default to `ReadModel`,
# blocking the roundtrip (read-only fields not accepted by write models). Hence,
# in the entity tests, we must explicitly specify the `WriteModel` schema.


@pytest.mark.parametrize(
    'required_arguments',
    entities_to_test,
    indirect=True,
)
def test_roundtrip_entity_from_model(required_arguments: RequiredEntityArguments):
    cls = required_arguments['cls']
    kwargs = required_arguments['kwargs']
    entity = cls(**kwargs)
    model = entity.to_model(schema='write')
    assert isinstance(model, cls.WriteModel)
    new = cls.from_model(model)
    assert isinstance(new, cls)
    new_model = new.to_model(schema='write')
    assert isinstance(new_model, cls.WriteModel)
    assert _validate_value(new_model) == _validate_value(model)


@pytest.mark.parametrize(
    'required_arguments',
    entities_to_test,
    indirect=True,
)
def test_roundtrip_entity_from_serialized(required_arguments: RequiredEntityArguments):
    cls = required_arguments['cls']
    kwargs = required_arguments['kwargs']
    entity = cls(**kwargs)
    serialized_entity = entity.serialize(schema='write')
    assert set(serialized_entity.keys()) == set(cls.WriteModel.model_fields.keys())
    new = cls.from_serialized(serialized_entity)
    assert isinstance(new, cls)
    serialized_new = new.serialize(schema='write')
    assert serialized_new == serialized_entity


def _assert_roundtrip_field_values_equal(
    cls: type[orm.Node],
    original_model: orm.Node.BaseNodeModel,
    new_entity: orm.Node,
    schema: str,
    tmp_path,
):
    context = {'repository_dump_path': tmp_path}
    new_model = new_entity.to_model(context=context, schema=schema)
    assert new_model.node_type == original_model.node_type
    if isinstance(original_model, cls.WriteModel):
        assert _validate_value(new_model.attributes) == _validate_value(original_model.attributes)
    elif isinstance(original_model, cls.ConstructorModel):
        assert _validate_value(new_model.args) == _validate_value(original_model.args)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_roundtrip_node_from_model_attributes(required_arguments: RequiredNodeArguments, tmp_path):
    cls = required_arguments['cls']
    payload = required_arguments['write_model_payload']
    files = payload.pop('files', {})
    assert_derived = payload.pop('assert_derived', lambda _: None)
    model = cls.WriteModel(node_type=cls.class_node_type, **payload)
    new = cls.from_model(model, files=files)
    assert isinstance(new, cls)
    assert_derived(new)
    _assert_roundtrip_field_values_equal(cls, model, new, 'write', tmp_path)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_roundtrip_node_from_model_constructor(required_arguments: RequiredNodeArguments, tmp_path):
    cls = required_arguments['cls']

    if not cls.supports_constructor_model:
        with pytest.raises(UnsupportedSchemaError):
            cls.ConstructorModel
        return

    payload = required_arguments['constructor_model_payload']
    model = cls.ConstructorModel(node_type=cls.class_node_type, **payload)
    new = cls.from_model(model)
    assert isinstance(new, cls)
    _assert_roundtrip_field_values_equal(cls, model, new, 'constructor', tmp_path)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_roundtrip_node_from_serialized_attributes(required_arguments: RequiredNodeArguments, tmp_path):
    cls = required_arguments['cls']
    payload = required_arguments['write_model_payload']
    files = payload.pop('files', {})
    assert_derived = payload.pop('assert_derived', lambda _: None)
    model = cls.WriteModel(node_type=cls.class_node_type, **payload)
    serialized = model.model_dump(exclude_none=True)
    new = cls.from_serialized(serialized, files=files)
    assert isinstance(new, cls)
    assert_derived(new)
    _assert_roundtrip_field_values_equal(cls, model, new, 'write', tmp_path)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_roundtrip_node_from_serialized_constructor(required_arguments: RequiredNodeArguments, tmp_path):
    cls = required_arguments['cls']

    if not cls.supports_constructor_model:
        with pytest.raises(UnsupportedSchemaError):
            cls.ConstructorModel
        return

    payload = required_arguments['constructor_model_payload']
    model = cls.ConstructorModel(node_type=cls.class_node_type, **payload)
    serialized = model.model_dump(exclude_none=True)
    new = cls.from_serialized(serialized)
    assert isinstance(new, cls)
    _assert_roundtrip_field_values_equal(cls, model, new, 'constructor', tmp_path)
