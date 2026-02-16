"""Tests for the :mod:`aiida.repository.repository` module."""

import contextlib
import io
import pathlib
import typing as t

import pytest

from aiida.repository import File, FileType, Repository
from aiida.repository.backend import DiskObjectStoreRepositoryBackend, SandboxRepositoryBackend


@contextlib.contextmanager
def get_sandbox_backend(*_) -> SandboxRepositoryBackend:
    """Return an instance of the sandbox repository backend."""
    yield SandboxRepositoryBackend()


@contextlib.contextmanager
def get_disk_object_store_backend(tmp_path) -> DiskObjectStoreRepositoryBackend:
    """Return an instance of the disk object store repository backend."""
    from disk_objectstore import Container

    yield DiskObjectStoreRepositoryBackend(container=Container(tmp_path))


@pytest.fixture(scope='function', params=[get_sandbox_backend, get_disk_object_store_backend])
def repository(request, tmp_path_factory) -> Repository:
    """Return an instance of ``aiida.repository.Repository`` with one of the available repository backends.

    By parametrizing this fixture over the available ``AbstractRepositoryBackend`` implementations, all tests below that
    act on a repository instance, will automatically get tested for all available backends.

    .. note:: Need to use the ``tmp_path_factory`` instead of simply ``tmp_path`` since the base path is already used
        for creating the entire configuration directory, so we create a subdirectory for the container.

    """
    with request.param(tmp_path_factory.mktemp('container')) as backend:
        backend.initialise()
        repository = Repository(backend=backend)
        yield repository


@pytest.fixture(scope='function', params=[get_sandbox_backend, get_disk_object_store_backend])
def repository_uninitialised(request, tmp_path_factory) -> Repository:
    """Return uninitialised instance of ``aiida.repository.Repository`` with one of the available repository backends.

    By parametrizing this fixture over the available ``AbstractRepositoryBackend`` implementations, all tests below that
    act on a repository instance, will automatically get tested for all available backends.

    .. note:: Need to use the ``tmp_path_factory`` instead of simply ``tmp_path`` since the base path is already used
        for creating the entire configuration directory, so we create a subdirectory for the container.

    """
    with request.param(tmp_path_factory.mktemp('container')) as backend:
        repository = Repository(backend=backend)
        yield repository


@pytest.fixture(scope='function', params=[True, False])
def tmp_path_parametrized(request, tmp_path_factory) -> t.Union[str, pathlib.Path]:
    """Indirect parametrized fixture that returns temporary path both as ``str`` and as ``pathlib.Path``.

    This is a useful fixture to automatically parametrize a test for a method that accepts both types.
    """
    tmp_path = tmp_path_factory.mktemp('target')

    if request.param:
        tmp_path = str(tmp_path)

    yield tmp_path


def test_uuid(repository_uninitialised):
    """Test the ``uuid`` property."""
    repository = repository_uninitialised

    if isinstance(repository.backend, SandboxRepositoryBackend):
        assert repository.uuid is None
        repository.backend.initialise()
        assert repository.uuid is None

    if isinstance(repository.backend, DiskObjectStoreRepositoryBackend):
        assert repository.uuid is None
        repository.backend.initialise()
        assert isinstance(repository.uuid, str)


def test_initialise(repository_uninitialised):
    """Test the ``initialise`` method and the ``is_initialised`` property."""
    repository = repository_uninitialised

    assert not repository.is_initialised
    repository.backend.initialise()
    assert repository.is_initialised


def test_pre_process_path():
    """Test the ``Repository.pre_process_path`` classmethod."""
    with pytest.raises(TypeError, match=r'path is not of type `str` nor `pathlib.PurePath`.'):
        Repository._pre_process_path(path=1)

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        Repository._pre_process_path(path=pathlib.Path('/absolute/path'))

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        Repository._pre_process_path(path='/absolute/path')

    assert Repository._pre_process_path(None) == pathlib.Path()
    assert Repository._pre_process_path('relative') == pathlib.Path('relative')
    assert Repository._pre_process_path('relative/nested') == pathlib.Path('relative/nested')
    assert Repository._pre_process_path(pathlib.Path('relative')) == pathlib.Path('relative')
    assert Repository._pre_process_path(pathlib.Path('relative/nested')) == pathlib.Path('relative/nested')

    # reject windows absolute paths
    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        Repository._pre_process_path(path=pathlib.PureWindowsPath('C:/absolute/path'))


def test_create_directory_raises(repository):
    """Test the ``Repository.create_directory`` method when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'path cannot be `None`.'):
        repository.create_directory(None)

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        repository.create_directory('/absolute/path')


def test_create_directory(repository):
    """Test the ``Repository.create_directory`` method."""
    repository.create_directory('path')
    assert repository.list_object_names() == ['path']

    # Creating subfolder in existing directory
    repository.create_directory('path/sub')
    assert repository.list_object_names() == ['path']
    assert repository.list_object_names('path') == ['sub']

    # Creating nested folder in one shot
    repository.create_directory('nested/dir')
    assert repository.list_object_names() == ['nested', 'path']
    assert repository.list_object_names('nested') == ['dir']


def test_get_file_keys(repository, generate_directory):
    """Test the ``Repository.get_file_keys`` method."""
    directory = generate_directory({'file_a': b'content_a', 'relative': {'file_b': b'content_b'}})

    assert repository.get_file_keys() == []

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    file_keys = [repository.get_object('file_a').key, repository.get_object('relative/file_b').key]

    assert sorted(repository.get_file_keys()) == sorted(file_keys)


def test_get_object_raises(repository):
    """Test the ``Repository.get_object`` method when it is supposed to raise."""
    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        repository.get_object('/absolute/path')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.get_object('non_existing_folder/file_a')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.get_object('non_existant')


def test_get_object(repository, generate_directory):
    """Test the ``Repository.get_object`` method."""
    directory = generate_directory({'relative': {'file_b': None}})

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    file_object = repository.get_object(None)
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.DIRECTORY

    file_object = repository.get_object('relative')
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.DIRECTORY
    assert file_object.name == 'relative'

    file_object = repository.get_object('relative/file_b')
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.FILE
    assert file_object.name == 'file_b'


def test_get_directory_raises(repository, generate_directory):
    """Test the ``Repository.get_directory`` method when it is supposed to raise."""
    directory = generate_directory({'relative': {'file_b': None}})

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        repository.get_object('/absolute/path')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.get_object('non_existing_folder/file_a')

    with pytest.raises(NotADirectoryError, match=r'object with path `.*` is not a directory.'):
        repository.get_directory('relative/file_b')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.get_object('non_existant')


def test_get_directory(repository, generate_directory):
    """Test the ``Repository.get_directory`` method."""
    directory = generate_directory({'relative': {'file_b': None}})

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    file_object = repository.get_object(None)
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.DIRECTORY

    file_object = repository.get_object('relative')
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.DIRECTORY
    assert file_object.name == 'relative'


def test_get_file_raises(repository, generate_directory):
    """Test the ``Repository.get_file`` method when it is supposed to raise."""
    directory = generate_directory({'relative': {'file_b': None}})

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        repository.get_file('/absolute/path')

    with pytest.raises(TypeError, match=r'path cannot be `None`.'):
        repository.get_file(None)

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.get_file('non_existing_folder/file_a')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.get_file('non_existant')

    with pytest.raises(IsADirectoryError, match=r'object with path `.*` is not a file.'):
        repository.get_file('relative')


def test_get_file(repository, generate_directory):
    """Test the ``Repository.get_file`` method."""
    directory = generate_directory({'relative': {'file_b': None}})

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    file_object = repository.get_file('relative/file_b')
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.FILE
    assert file_object.name == 'file_b'


def test_list_objects_raises(repository, generate_directory):
    """Test the ``Repository.list_objects`` method when it is supposed to raise."""
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        repository.list_objects('/absolute/path')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.list_objects('non_existant')

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    with pytest.raises(NotADirectoryError, match=r'object with path `.*` is not a directory.'):
        repository.list_objects('file_a')


def test_list_objects(repository, generate_directory):
    """Test the ``Repository.list_objects`` method."""
    directory = generate_directory({'file_a': None, 'relative': {'file_b': None}})

    repository.create_directory('path/sub')

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    objects = repository.list_objects()
    assert len(objects) == 3
    assert all(isinstance(obj, File) for obj in objects)
    assert [obj.name for obj in objects] == ['file_a', 'path', 'relative']

    objects = repository.list_objects('path')
    assert len(objects) == 1
    assert all(isinstance(obj, File) for obj in objects)
    assert [obj.name for obj in objects] == ['sub']

    objects = repository.list_objects('relative')
    assert len(objects) == 1
    assert all(isinstance(obj, File) for obj in objects)
    assert [obj.name for obj in objects] == ['file_b']


def test_list_object_names_raises(repository, generate_directory):
    """Test the ``Repository.list_object_names`` method when it is supposed to raise."""
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        repository.list_object_names('/absolute/path')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        repository.list_object_names('non_existant')

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    with pytest.raises(NotADirectoryError, match=r'object with path `.*` is not a directory.'):
        repository.list_objects('file_a')


def test_list_object_names(repository, generate_directory):
    """Test the ``Repository.list_object_names`` method."""
    directory = generate_directory({'file_a': None, 'relative': {'file_b': None}})

    repository.create_directory('path/sub')

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    assert repository.list_object_names() == ['file_a', 'path', 'relative']
    assert repository.list_object_names('path') == ['sub']
    assert repository.list_object_names('relative') == ['file_b']


def test_put_object_from_filelike_raises(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method when it should raise."""
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError):
        repository.put_object_from_filelike('file_a', directory / 'file_a')  # Path-like object

    with pytest.raises(TypeError):
        repository.put_object_from_filelike('file_a', directory / 'file_a')  # String

    with pytest.raises(TypeError):
        with open(directory / 'file_a', encoding='utf8') as handle:
            repository.put_object_from_filelike(handle, 'file_a')  # Not in binary mode


def test_put_object_from_filelike(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method."""
    directory = generate_directory({'file_a': None, 'relative': {'file_b': None}})

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    assert repository.has_object('file_a')

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    assert repository.has_object('relative/file_b')

    with io.BytesIO(b'content_stream') as stream:
        repository.put_object_from_filelike(stream, 'stream')


def test_put_object_from_tree_raises(repository):
    """Test the ``Repository.put_object_from_tree`` method when it should raise."""
    with pytest.raises(TypeError, match=r'filepath `.*` is not of type `str` nor `pathlib.PurePath`.'):
        repository.put_object_from_tree(None)

    with pytest.raises(TypeError, match=r'filepath `.*` is not an absolute path.'):
        repository.put_object_from_tree('relative/path')


def test_put_object_from_tree(repository, generate_directory):
    """Test the ``Repository.put_object_from_tree`` method."""
    directory = generate_directory(
        {'file_a': b'content_a', 'relative': {'file_b': b'content_b', 'sub': {'file_c': b'content_c'}}}
    )

    repository.put_object_from_tree(str(directory))

    assert repository.get_object_content('file_a') == b'content_a'
    assert repository.get_object_content('relative/file_b') == b'content_b'
    assert repository.get_object_content('relative/sub/file_c') == b'content_c'


def test_put_object_from_tree_path(repository, generate_directory):
    """Test the ``Repository.put_object_from_tree`` method."""
    directory = generate_directory({'empty': {'folder': {}}})
    repository.put_object_from_tree(str(directory), path='base/path')

    assert repository.list_object_names() == ['base']
    assert repository.list_object_names('base') == ['path']
    assert repository.list_object_names('base/path') == ['empty']
    assert repository.list_object_names('base/path/empty') == ['folder']


def test_put_object_from_tree_empty_folder(repository, generate_directory):
    """Test the ``Repository.put_object_from_tree`` method."""
    directory = generate_directory({'empty': {'folder': {}}})
    repository.put_object_from_tree(str(directory))

    assert repository.list_object_names() == ['empty']
    assert repository.list_object_names('empty') == ['folder']
    assert repository.get_directory('empty')
    assert repository.get_directory('empty/folder')


def test_put_object_from_tree_empty_folder_path(repository, tmp_path):
    """Test the ``Repository.put_object_from_tree`` method."""
    repository.put_object_from_tree(str(tmp_path), 'empty/folder')

    assert repository.list_object_names() == ['empty']
    assert repository.list_object_names('empty') == ['folder']
    assert repository.get_directory('empty')
    assert repository.get_directory('empty/folder')


def test_has_object(repository, generate_directory):
    """Test the ``Repository.has_object`` method."""
    directory = generate_directory({'file_a': None})

    assert not repository.has_object('non_existant')

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle, 'file_a')

    assert repository.has_object(key)


def test_open_raise(repository):
    """Test the ``Repository.open`` method when it should raise."""
    with pytest.raises(FileNotFoundError):
        with repository.open('non_existant'):
            pass


def test_open(repository, generate_directory):
    """Test the ``Repository.open`` method."""
    directory = generate_directory({'file_a': b'content_a', 'relative': {'file_b': b'content_b'}})

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    with open(directory / 'relative/file_b', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'relative/file_b')

    with repository.open('file_a') as handle:
        assert isinstance(handle, io.BufferedReader)

    with repository.open('file_a') as handle:
        assert handle.read() == b'content_a'

    with repository.open('relative/file_b') as handle:
        assert handle.read() == b'content_b'


def test_delete_object(repository, generate_directory):
    """Test the ``Repository.delete_object`` method."""
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    assert repository.has_object('file_a')

    key = repository.get_object('file_a').key
    repository.delete_object('file_a')

    assert not repository.has_object('file_a')
    assert repository.backend.has_object(key)


def test_delete_object_hard(repository, generate_directory):
    """Test the ``Repository.delete_object`` method with ``hard_delete=True``."""
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    assert repository.has_object('file_a')

    key = repository.get_object('file_a').key
    repository.delete_object('file_a', hard_delete=True)

    assert not repository.has_object('file_a')
    assert not repository.backend.has_object(key)


def test_erase(repository, generate_directory):
    """Test the ``Repository.erase`` method."""
    directory = generate_directory(
        {
            'file_a': b'content_a',
            'relative': {
                'file_b': b'content_b',
            },
        }
    )

    repository.put_object_from_tree(str(directory))

    assert repository.has_object('file_a')
    assert repository.has_object('relative/file_b')

    repository.erase()

    assert repository.is_empty()


def test_is_empty(repository, generate_directory):
    """Test the ``Repository.is_empty`` method."""
    directory = generate_directory({'file_a': None})

    assert repository.is_empty()

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle, 'file_a')

    assert not repository.is_empty()

    repository.delete_object('file_a')

    assert repository.is_empty()


def test_walk(repository, generate_directory):
    """Test the ``Repository.walk`` method."""
    directory = generate_directory({'empty': {}, 'file_a': None, 'relative': {'file_b': None, 'sub': {'file_c': None}}})

    repository.put_object_from_tree(str(directory))

    results = []
    for root, dirnames, filenames in repository.walk():
        results.append((root, sorted(dirnames), sorted(filenames)))

    assert sorted(results) == [
        (pathlib.Path('.'), ['empty', 'relative'], ['file_a']),
        (pathlib.Path('empty'), [], []),
        (pathlib.Path('relative'), ['sub'], ['file_b']),
        (pathlib.Path('relative/sub'), [], ['file_c']),
    ]


@pytest.mark.parametrize(
    ('path', 'expected_hierarchy'),
    (
        (None, {'file_a': b'a', 'relative': {'file_b': b'b', 'sub': {'file_c': b'c'}}}),
        ('.', {'file_a': b'a', 'relative': {'file_b': b'b', 'sub': {'file_c': b'c'}}}),
        ('relative', {'file_b': b'b', 'sub': {'file_c': b'c'}}),
        ('relative/sub', {'file_c': b'c'}),
    ),
)
def test_copy_tree(
    repository, generate_directory, tmp_path_parametrized, path, expected_hierarchy, serialize_file_hierarchy
):
    """Test the ``Repository.copy_tree`` method."""
    directory = generate_directory({'file_a': b'a', 'relative': {'file_b': b'b', 'sub': {'file_c': b'c'}}})
    repository.put_object_from_tree(str(directory))
    repository.copy_tree(tmp_path_parametrized, path=path)
    assert serialize_file_hierarchy(tmp_path_parametrized) == expected_hierarchy


@pytest.mark.parametrize(
    ('argument', 'value', 'exception', 'match'),
    (
        ('target', None, TypeError, r'path .* is not of type `str` nor `pathlib.Path`.'),
        ('target', 'relative/path', TypeError, r'provided target `.*` is not an absolute path.'),
        ('target', pathlib.Path('.'), TypeError, r'provided target `.*` is not an absolute path.'),
        ('path', pathlib.Path('file_a'), NotADirectoryError, r'object with path `.*` is not a directory.'),
    ),
)
def test_copy_tree_invalid(tmp_path, repository, generate_directory, argument, value, exception, match):
    """Test the ``Repository.copy_tree`` method for invalid input."""
    directory = generate_directory({'file_a': None})
    repository.put_object_from_tree(str(directory))

    if argument == 'target':
        with pytest.raises(exception, match=match):
            repository.copy_tree(target=value)
    else:
        with pytest.raises(exception, match=match):
            repository.copy_tree(target=tmp_path, path=value)


def test_clone(repository, generate_directory):
    """Test the ``Repository.clone`` method."""
    directory = generate_directory({'file_a': None, 'relative': {'file_b': None, 'sub': {'file_c': None}}})

    source = Repository(backend=SandboxRepositoryBackend())
    source.put_object_from_tree(str(directory))

    assert not source.is_empty()
    assert repository.is_empty()

    repository.clone(source)

    assert repository.list_object_names() == source.list_object_names()
    assert repository.list_object_names('relative') == source.list_object_names('relative')
    assert repository.list_object_names('relative/sub') == source.list_object_names('relative/sub')


def test_clone_empty_folder(repository, generate_directory):
    """Test the ``Repository.clone`` method for repository only containing empty folders."""
    directory = generate_directory({'empty': {'folder': {}}})

    source = Repository(backend=SandboxRepositoryBackend())
    source.put_object_from_tree(str(directory))

    assert not source.is_empty()
    assert repository.is_empty()

    repository.clone(source)
    assert repository.list_object_names() == ['empty']
    assert repository.list_object_names('empty') == ['folder']


def test_serialize(repository, generate_directory):
    """Test the ``Repository.serialize`` method."""
    directory = generate_directory({'empty': {}, 'file_a': None, 'relative': {'file_b': b'content_b'}})

    repository.put_object_from_tree(str(directory))
    serialized = repository.serialize()

    assert isinstance(serialized, dict)


def test_serialize_roundtrip(repository):
    """Test the serialization round trip."""
    serialized = repository.serialize()
    reconstructed = Repository.from_serialized(repository.backend, serialized)

    assert isinstance(reconstructed, Repository)
    assert repository.get_directory() == reconstructed.get_directory()


def test_hash(repository, generate_directory):
    """Test the ``Repository.hash`` method."""
    generate_directory({'empty': {}, 'file_a': b'content', 'relative': {'file_b': None, 'sub': {'file_c': None}}})
    assert isinstance(repository.hash(), str)


def test_flatten(repository, generate_directory):
    """Test the ``Repository.flatten`` classmethod."""
    directory = generate_directory(
        {
            'empty': {},
            'file_a': b'content',
            'relative': {
                'file_b': None,
                'sub': {'file_c': None},
                'sub_empty': {},
            },
        }
    )
    repository.put_object_from_tree(str(directory))
    flattened = repository.flatten(repository.serialize())
    assert isinstance(flattened, dict)
    if isinstance(repository.backend, DiskObjectStoreRepositoryBackend):
        assert flattened == {
            'empty/': None,
            'relative/': None,
            'file_a': 'ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73',
            'relative/sub/': None,
            'relative/file_b': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'relative/sub/file_c': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'relative/sub_empty/': None,
        }
