"""Tests for the ``Model`` class attribute of ``orm.Entity`` subclasses."""

import datetime
import enum
import io

import numpy as np
import pytest
from plumpy import get_object_loader

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
    orm.RemoteStashData,
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


@pytest.fixture
def required_arguments(request, default_user, aiida_localhost, tmp_path):
    if request.param is orm.AuthInfo:
        return orm.AuthInfo, {'user': default_user, 'computer': aiida_localhost}
    if request.param is orm.Comment:
        return orm.Comment, {'user': default_user, 'node': orm.Data().store(), 'content': ''}
    if request.param is orm.Computer:
        return orm.Computer, {'label': 'localhost'}
    if request.param is orm.Group:
        return orm.Group, {'label': 'group'}
    if request.param is orm.Log:
        return orm.Log, {
            'time': datetime.datetime.now(),
            'loggername': 'logger',
            'levelname': 'REPORT',
            'message': 'message',
            'dbnode_id': orm.Data().store().pk,
        }
    if request.param is orm.User:
        return orm.User, {'email': 'test@localhost'}
    if request.param is orm.ArrayData:
        buffered_array = io.BytesIO()
        np.save(buffered_array, np.array([1, 0, 0]), allow_pickle=False)
        buffered_array.seek(0)

        def assert_derived_array_properties(node: orm.ArrayData):
            assert node.base.attributes.all == {'array|test_array': [3]}
            assert node.get_array('test_array').tolist() == [1, 0, 0]

        return orm.ArrayData, {
            'attributes-based': {
                'attributes': {'array|test_array': [3]},
                'files': {'test_array.npy': lambda: buffered_array},
                'assert_derived': assert_derived_array_properties,
            },
            'constructor-based': {
                'args': {'arrays': {'test_array': [1, 0, 0]}},
            },
        }
    if request.param is orm.Bool:
        return orm.Bool, {
            'attributes-based': {
                'attributes': {'value': True},
            },
        }
    if request.param is orm.CifData:

        def assert_derived_cif_properties(node: orm.CifData):
            assert node.filename == 'structure.cif'
            assert node.md5 == '771ee48ec137aba8a57328a1df42fcf4'
            assert node.get_content(mode='r') == 'data_test\nloop_\n_atom_site_label\nH1\n'

        return orm.CifData, {
            'attributes-based': {
                'attributes': {},
                'files': {'structure.cif': lambda: io.StringIO('data_test\nloop_\n_atom_site_label\nH1\n')},
                'assert_derived': assert_derived_cif_properties,
            },
            'constructor-based': {
                'args': {'filename': 'structure.cif', 'content': 'data_test\nloop_\n_atom_site_label\nH1\n'},
            },
        }
    if request.param is orm.ContainerizedCode:
        return orm.ContainerizedCode, {
            'attributes-based': {
                'label': 'containerized_echo',
                'computer': aiida_localhost.pk,
                'attributes': {
                    'filepath_executable': '/bin/echo',
                    'image_name': 'docker://alpine:3',
                    'engine_command': 'docker run {image_name}',
                },
            },
            'constructor-based': {
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
        return orm.Data, {
            'attributes-based': {
                'attributes': {
                    'source': {'uri': 'http://127.0.0.1'},
                },
            }
        }
    if request.param is orm.Dict:
        return orm.Dict, {
            'attributes-based': {
                'attributes': {'a': 1, 'b': 2},
            },
            'constructor-based': {
                'args': {'value': {'a': 1, 'b': 2}},
            },
        }
    if request.param is orm.EnumData:
        return orm.EnumData, {
            'attributes-based': {
                'attributes': {
                    'name': 'OPTION_A',
                    'value': 'a',
                    'identifier': get_object_loader().identify_object(DummyEnum),
                },
            },
            'constructor-based': {
                'args': {'member': DummyEnum.OPTION_A},
            },
        }
    if request.param is orm.Float:
        return orm.Float, {
            'attributes-based': {
                'attributes': {'value': 1.0},
            }
        }
    if request.param is orm.FolderData:
        (tmp_path / 'binary_file').write_bytes(b'byte content')
        (tmp_path / 'text_file').write_text('text content')

        def assert_derived_folder_properties(node: orm.FolderData):
            assert node.get_object_content('binary_file', mode='rb') == b'byte content'
            assert node.get_object_content('text_file', mode='r') == 'text content'

        return orm.FolderData, {
            'attributes-based': {
                'attributes': {},
                'files': {
                    'binary_file': lambda: io.BytesIO(b'byte content'),
                    'text_file': lambda: io.StringIO('text content'),
                },
                'assert_derived': assert_derived_folder_properties,
            },
            'constructor-based': {
                'args': {'tree': str(tmp_path)},
            },
        }
    if request.param is orm.InstalledCode:
        return orm.InstalledCode, {
            'attributes-based': {
                'label': 'echo',
                'computer': aiida_localhost.pk,
                'attributes': {
                    'default_calc_job_plugin': 'core.arithmetic.add',
                    'filepath_executable': '/bin/echo',
                },
            },
            'constructor-based': {
                'label': 'echo',
                'args': {
                    'computer': aiida_localhost.label,
                    'filepath_executable': '/bin/echo',
                },
            },
        }
    if request.param is orm.Int:
        return orm.Int, {
            'attributes-based': {
                'attributes': {'value': 1},
            },
        }
    if request.param is orm.JsonableData:
        return orm.JsonableData, {
            'attributes-based': {
                'attributes': {
                    'data': 1,
                    '@class': 'JsonableClass',
                    '@module': 'tests.orm.models.test_models',
                },
            },
            'constructor-based': {
                'args': {
                    'obj': JsonableClass(1),
                }
            },
        }
    if request.param is orm.List:
        return orm.List, {
            'attributes-based': {
                'attributes': {
                    'list': [1, 2, 3],
                },
            }
        }
    if request.param is orm.PortableCode:
        (tmp_path / 'code.sh').write_text('#!/bin/bash\necho "$@"\n')
        return orm.PortableCode, {
            'attributes-based': {
                'label': 'portable_code',
                'attributes': {
                    'filepath_executable': 'code.sh',
                },
            },
            'constructor-based': {
                'label': 'portable_code',
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

        return orm.SinglefileData, {
            'attributes-based': {
                'attributes': {},
                'files': {'file.txt': lambda: io.StringIO('singlefile-content')},
                'assert_derived': assert_derived_singlefile_properties,
            },
            'constructor-based': {
                'args': {
                    'filename': 'file.txt',
                    'content': 'some-content',
                },
            },
        }
    if request.param is orm.Str:
        return orm.Str, {
            'attributes-based': {
                'attributes': {'value': 'string'},
            }
        }
    if request.param is orm.StructureData:
        return orm.StructureData, {
            'attributes-based': {
                'attributes': {
                    'cell': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                    'pbc1': True,
                    'pbc2': True,
                    'pbc3': True,
                    'sites': [{'kind_name': 'H', 'position': (0.0, 0.0, 0.0)}],
                    'kinds': [{'name': 'H', 'mass': 1.0, 'symbols': ('H',), 'weights': (1.0,)}],
                }
            }
        }
    if request.param is orm.RemoteData:
        return orm.RemoteData, {
            'attributes-based': {
                'computer': aiida_localhost.pk,
                'attributes': {
                    'remote_path': '/some/path',
                },
            },
        }
    if request.param is orm.RemoteStashData:
        return orm.RemoteStashData, {
            'attributes-based': {
                'attributes': {
                    'stash_mode': StashMode.COMPRESS_TAR,
                },
            }
        }
    if request.param is orm.RemoteStashCompressedData:
        return orm.RemoteStashCompressedData, {
            'attributes-based': {
                'attributes': {
                    'stash_mode': StashMode.COMPRESS_TAR,
                    'target_basepath': '/some/path',
                    'source_list': ['/some/file'],
                    'dereference': True,
                }
            }
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

        return orm.XyData, {
            'attributes-based': {
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
            'constructor-based': {
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
def test_model_overrides(required_arguments):
    cls: type[orm.Entity] = required_arguments[0]
    name = cls.__name__

    assert cls.ReadModel.__qualname__ == f'{name}.ReadModel'
    assert cls.ReadModel.model_config.get('title') == f'{name}ReadModel'

    assert cls.WriteModel.__qualname__ == f'{name}.WriteModel'
    assert cls.WriteModel.model_config.get('title') == f'{name}WriteModel'


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_node_attributes_model_overrides(required_arguments):
    cls: type[orm.Node] = required_arguments[0]

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
def test_roundtrip_entity_from_model(required_arguments):
    cls: type[orm.Entity] = required_arguments[0]
    kwargs: dict = required_arguments[1]

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
def test_roundtrip_entity_from_serialized(required_arguments):
    cls: type[orm.Entity] = required_arguments[0]
    kwargs: dict = required_arguments[1]

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
def test_roundtrip_node_from_model_attributes(required_arguments, tmp_path):
    cls: type[orm.Node] = required_arguments[0]
    payload: dict = required_arguments[1]
    attributes_payload: dict = payload['attributes-based']
    files = attributes_payload.pop('files', {})
    assert_derived = attributes_payload.pop('assert_derived', lambda _: None)

    model = cls.WriteModel(node_type=cls.class_node_type, **attributes_payload)
    new = cls.from_model(model, files=files)
    assert isinstance(new, cls)
    assert_derived(new)
    _assert_roundtrip_field_values_equal(cls, model, new, 'write', tmp_path)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_roundtrip_node_from_model_constructor(required_arguments, tmp_path):
    cls: type[orm.Node] = required_arguments[0]
    payload: dict = required_arguments[1]
    constructor_payload: dict | None = payload.get('constructor-based')

    if constructor_payload is None:
        with pytest.raises(UnsupportedSchemaError):
            cls.ConstructorModel
        return

    model = cls.ConstructorModel(node_type=cls.class_node_type, **constructor_payload)
    new = cls.from_model(model)
    assert isinstance(new, cls)
    _assert_roundtrip_field_values_equal(cls, model, new, 'constructor', tmp_path)


@pytest.mark.parametrize(
    'required_arguments',
    nodes_to_test,
    indirect=True,
)
def test_roundtrip_node_from_serialized_attributes(required_arguments, tmp_path):
    cls: type[orm.Node] = required_arguments[0]
    attributes_payload: dict = required_arguments[1]['attributes-based']
    files = attributes_payload.pop('files', {})
    assert_derived = attributes_payload.pop('assert_derived', lambda _: None)

    model = cls.WriteModel(node_type=cls.class_node_type, **attributes_payload)
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
def test_roundtrip_node_from_serialized_constructor(required_arguments, tmp_path):
    cls: type[orm.Node] = required_arguments[0]
    payload: dict = required_arguments[1]
    constructor_payload: dict | None = payload.get('constructor-based')

    if constructor_payload is None:
        with pytest.raises(UnsupportedSchemaError):
            cls.ConstructorModel
        return

    model = cls.ConstructorModel(node_type=cls.class_node_type, **constructor_payload)
    serialized = model.model_dump(exclude_none=True)
    new = cls.from_serialized(serialized)
    assert isinstance(new, cls)
    _assert_roundtrip_field_values_equal(cls, model, new, 'constructor', tmp_path)
