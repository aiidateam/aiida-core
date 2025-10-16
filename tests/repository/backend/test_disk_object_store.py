"""Tests for the :mod:`aiida.repository.backend.disk_object_store` module."""

import io
import pathlib

import pytest

from aiida.repository.backend.disk_object_store import DiskObjectStoreRepositoryBackend


@pytest.fixture(scope='function')
def repository(tmp_path):
    """Return a `DiskObjectStoreRepositoryBackend`.

    Cannot use the ``tmp_path`` fixture because it will have the exact same path as the ``folder`` fixture and the
    container requires an empty folder to be initialized in.
    """
    from disk_objectstore import Container

    container = Container(tmp_path)
    yield DiskObjectStoreRepositoryBackend(container=container)


@pytest.fixture(scope='function')
def populated_repository(repository):
    """Initializes the storage and database with minimal population."""
    from io import BytesIO

    repository.initialise()

    content = BytesIO(b'Packed file number 1')
    repository.put_object_from_filelike(content)

    content = BytesIO(b'Packed file number 2')
    repository.put_object_from_filelike(content)

    repository.maintain(live=False)

    content = BytesIO(b'Packed file number 3 (also loose)')
    repository.put_object_from_filelike(content)

    repository.maintain(live=True)

    content = BytesIO(b'Unpacked file')
    repository.put_object_from_filelike(content)
    yield repository


def test_str(repository):
    """Test the ``__str__`` method."""
    assert str(repository)
    repository.initialise()
    assert str(repository)


def test_uuid(repository):
    """Test the ``uuid`` property."""
    assert repository.uuid is None
    repository.initialise()
    assert isinstance(repository.uuid, str)


def test_initialise(repository):
    """Test the ``initialise`` method and the ``is_initialised`` property."""
    assert not repository.is_initialised
    repository.initialise()
    assert repository.is_initialised


def test_put_object_from_filelike_raises(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method when it should raise."""
    repository.initialise()
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # Path-like object

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # String

    with pytest.raises(TypeError):
        with open(directory / 'file_a', encoding='utf8') as handle:
            repository.put_object_from_filelike(handle)  # Not in binary mode


def test_put_object_from_filelike(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method."""
    repository.initialise()
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert isinstance(key, str)


def test_has_object(repository, generate_directory):
    """Test the ``Repository.has_object`` method."""
    repository.initialise()
    directory = generate_directory({'file_a': None})

    assert not repository.has_object('non_existant')

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)


def test_open_raise(repository):
    """Test the ``Repository.open`` method when it should raise."""
    repository.initialise()

    with pytest.raises(FileNotFoundError):
        with repository.open('non_existant'):
            pass


def test_open(repository, generate_directory):
    """Test the ``Repository.open`` method."""
    repository.initialise()
    directory = generate_directory({'file_a': b'content_a', 'relative': {'file_b': b'content_b'}})

    with open(directory / 'file_a', 'rb') as handle:
        key_a = repository.put_object_from_filelike(handle)

    with open(directory / 'relative/file_b', 'rb') as handle:
        key_b = repository.put_object_from_filelike(handle)

    with repository.open(key_a) as handle:
        assert isinstance(handle, io.BufferedReader)

    with repository.open(key_a) as handle:
        assert handle.read() == b'content_a'

    with repository.open(key_b) as handle:
        assert handle.read() == b'content_b'


def test_iter_object_streams(repository):
    """Test the ``Repository.iter_object_streams`` method."""
    repository.initialise()
    key = repository.put_object_from_filelike(io.BytesIO(b'content'))

    for _key, stream in repository.iter_object_streams([key]):
        assert _key == key
        assert stream.read() == b'content'


def test_delete_object(repository, generate_directory):
    """Test the ``Repository.delete_object`` method."""
    repository.initialise()
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)

    repository.delete_object(key)
    assert not repository.has_object(key)


def test_erase(repository, generate_directory):
    """Test the ``Repository.erase`` method."""
    repository.initialise()
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)

    dirpath = pathlib.Path(repository._container.get_folder())
    repository.erase()

    assert not dirpath.exists()
    assert not repository.is_initialised


def test_get_object_hash(repository, generate_directory):
    """Test the ``Repository.get_object_hash`` returns the expected value."""
    repository.initialise()
    directory = generate_directory({'file_a': b'content'})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.get_object_hash(key) == 'ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73'


def test_list_objects(repository, generate_directory):
    """Test the ``Repository.delete_object`` method."""
    repository.initialise()
    keylist = []

    directory = generate_directory({'file_a': b'content a'})
    with open(directory / 'file_a', 'rb') as handle:
        keylist.append(repository.put_object_from_filelike(handle))

    directory = generate_directory({'file_b': b'content b'})
    with open(directory / 'file_b', 'rb') as handle:
        keylist.append(repository.put_object_from_filelike(handle))

    assert sorted(list(repository.list_objects())) == sorted(keylist)


def test_key_format(repository):
    """Test the ``key_format`` property."""
    repository.initialise()
    assert repository.key_format == repository._container.hash_type


def test_get_info(populated_repository):
    """Test the ``get_info`` method."""
    repository_info = populated_repository.get_info()
    assert 'SHA-hash algorithm' in repository_info
    assert 'Compression algorithm' in repository_info
    assert repository_info['SHA-hash algorithm'] == 'sha256'
    assert repository_info['Compression algorithm'] == 'zlib+1'

    repository_info = populated_repository.get_info(detailed=True)
    assert 'SHA-hash algorithm' in repository_info
    assert 'Compression algorithm' in repository_info
    assert repository_info['SHA-hash algorithm'] == 'sha256'
    assert repository_info['Compression algorithm'] == 'zlib+1'

    assert 'Objects' in repository_info
    assert 'pack_files' in repository_info['Objects']
    assert 'loose' in repository_info['Objects']
    assert 'packed' in repository_info['Objects']
    assert repository_info['Objects']['pack_files'] == 1
    assert repository_info['Objects']['loose'] == 1
    assert repository_info['Objects']['packed'] == 3

    assert 'Size (MB)' in repository_info
    assert 'total_size_loose' in repository_info['Size (MB)']
    assert 'total_size_packed' in repository_info['Size (MB)']


@pytest.mark.parametrize(
    ('kwargs', 'output_info'),
    (
        ({'live': True}, {'unpacked': 0, 'packed': 4}),
        ({'live': False}, {'unpacked': 0, 'packed': 4}),
        ({'live': False, 'compress': True}, {'unpacked': 0, 'packed': 4}),
        ({'live': False, 'do_vacuum': False}, {'unpacked': 0, 'packed': 4}),
        (
            {
                'live': False,
                'pack_loose': False,
                'do_repack': False,
                'clean_storage': False,
                'do_vacuum': False,
            },
            {'unpacked': 1, 'packed': 3},
        ),
    ),
)
def test_maintain(populated_repository, kwargs, output_info):
    """Test the ``maintain`` method."""
    populated_repository.maintain(**kwargs)
    file_info = populated_repository._container.count_objects()
    assert file_info.loose == output_info['unpacked']
    assert file_info.packed == output_info['packed']


@pytest.mark.parametrize('do_vacuum', [True, False])
def test_maintain_logging(caplog, populated_repository, do_vacuum):
    """Test the logging of the ``maintain`` method."""
    populated_repository.maintain(live=False, do_vacuum=do_vacuum)

    list_of_logmsg = []
    for record in caplog.records:
        assert record.levelname == 'REPORT'
        assert record.name.endswith('.disk_object_store')
        list_of_logmsg.append(record.msg)

    assert 'packing' in list_of_logmsg[0].lower()
    assert 're-packing' in list_of_logmsg[1].lower()
    assert 'cleaning' in list_of_logmsg[2].lower()

    if do_vacuum:
        assert 'vacuum=true' in list_of_logmsg[2].lower()
    else:
        assert 'vacuum=false' in list_of_logmsg[2].lower()


@pytest.mark.parametrize('kwargs', [{'do_repack': True}, {'clean_storage': True}, {'do_vacuum': True}])
def test_maintain_live_overload(populated_repository, kwargs):
    """Test the ``maintain`` method."""
    with pytest.raises(ValueError):
        populated_repository.maintain(live=True, **kwargs)
