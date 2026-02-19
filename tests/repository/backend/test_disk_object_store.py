"""Tests for the :mod:`aiida.repository.backend.disk_object_store` module."""

import io
import pathlib
from unittest.mock import patch

import pytest
from disk_objectstore import Container

from aiida.repository.backend.disk_object_store import DiskObjectStoreRepositoryBackend


@pytest.fixture(scope='function')
def repository(tmp_path):
    """Return a `DiskObjectStoreRepositoryBackend`.

    Cannot use the ``tmp_path`` fixture because it will have the exact same path as the ``folder`` fixture and the
    container requires an empty folder to be initialized in.
    """
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


@pytest.fixture(scope='function')
def create_repository(tmp_path):
    """Factory fixture to create initialised repositories."""

    def _create(name: str) -> DiskObjectStoreRepositoryBackend:
        container = Container(tmp_path / name)
        repo = DiskObjectStoreRepositoryBackend(container=container)
        repo.initialise()
        return repo

    return _create


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


class TestImportObjectsToPack:
    """Tests for the ``import_objects_to_pack`` method."""

    @pytest.mark.parametrize(
        'contents',
        [
            pytest.param([], id='empty'),
            pytest.param([b'single object content'], id='single'),
            pytest.param([b'content one', b'content two', b'content three'], id='multiple'),
        ],
    )
    def test_import_objects(self, create_repository, contents):
        """Test importing objects: empty, single, and multiple."""
        source = create_repository('source')
        target = create_repository('target')

        keys = {source.put_object_from_filelike(io.BytesIO(c)) for c in contents}

        imported_keys = target.import_objects_to_pack(source, keys)

        assert set(imported_keys) == keys
        for key in keys:
            assert target.has_object(key)

        # Verify objects are in packed storage (not loose),
        # and only a single pack file is created for one or multiple content additions< not one per file
        with target._container as container:
            counts = container.count_objects()
            assert counts.packed == len(keys)
            assert counts.pack_files == (1 if len(contents) > 0 else 0)
            assert counts.loose == 0

    def test_step_callback(self, create_repository):
        """Test that the step callback is called for each object."""
        source = create_repository('source')
        target = create_repository('target')

        contents = [b'cb content one', b'cb content two', b'cb content three']
        keys = {source.put_object_from_filelike(io.BytesIO(c)) for c in contents}

        callback_calls = []

        def step_cb(key, current, total):
            callback_calls.append((key, current, total))

        target.import_objects_to_pack(source, keys, step_cb=step_cb)

        assert len(callback_calls) == len(keys)
        # Check that progress counts are correct
        for i, (_, current, total) in enumerate(callback_calls, 1):
            assert current == i
            assert total == len(keys)

    def test_large_object_streaming(self, create_repository, monkeypatch):
        """Test that objects larger than memory limit use streaming path."""

        import aiida.repository.backend.disk_object_store as dos_module

        source = create_repository('source')
        target = create_repository('target')

        # Set memory limit to 10 bytes, create 50-byte object
        monkeypatch.setattr(dos_module, '_IMPORT_BATCH_MEMORY_BYTES', 10)
        key = source.put_object_from_filelike(io.BytesIO(b'x' * 50))

        with patch.object(
            target._container, 'add_streamed_object_to_pack', wraps=target._container.add_streamed_object_to_pack
        ) as mock:
            target.import_objects_to_pack(source, {key})
            assert mock.call_count == 1  # Large object should use streaming path

    def test_batch_count_limit(self, create_repository, monkeypatch):
        """Test that batch flushes when count limit is reached.

        Note: No separate memory limit test since it would verify the same thing
        (multiple calls to add_objects_to_pack). This count limit test is sufficient
        to verify batching works.
        """

        import aiida.repository.backend.disk_object_store as dos_module

        source = create_repository('source')
        target = create_repository('target')

        # Set count limit to 2, create 5 objects -> should trigger multiple batch flushes
        monkeypatch.setattr(dos_module, '_IMPORT_BATCH_COUNT', 2)
        keys = {source.put_object_from_filelike(io.BytesIO(f'content {i}'.encode())) for i in range(5)}

        with patch.object(
            target._container, 'add_objects_to_pack', wraps=target._container.add_objects_to_pack
        ) as mock:
            target.import_objects_to_pack(source, keys)
            assert mock.call_count >= 2  # Should flush multiple times due to count limit

    def test_import_to_non_empty_repository(self, create_repository):
        """Test importing to a repository with existing loose and packed objects.

        Verifies:
        - Existing loose objects remain loose
        - Existing packed objects remain packed
        - New objects are added as packed
        - Duplicate objects (same hash) are deduplicated
        - Repository state is consistent after import
        """
        source = create_repository('source')
        target = create_repository('target')

        # Add existing objects to target: some loose, some packed
        existing_loose_content = b'existing loose object'
        existing_packed_content = b'existing packed object'
        duplicate_content = b'duplicate content'  # Will exist in both source and target

        existing_loose_key = target.put_object_from_filelike(io.BytesIO(existing_loose_content))
        existing_packed_key = target.put_object_from_filelike(io.BytesIO(existing_packed_content))
        duplicate_key = target.put_object_from_filelike(io.BytesIO(duplicate_content))

        # Pack some objects (not the loose one)
        target.maintain(live=False)  # Packs all loose objects

        # Add a new loose object after packing
        new_loose_content = b'new loose after packing'
        new_loose_key = target.put_object_from_filelike(io.BytesIO(new_loose_content))

        # Verify initial state: 1 loose, 3 packed
        with target._container as container:
            counts = container.count_objects()
            assert counts.loose == 1
            assert counts.packed == 3

        # Create source objects: one new, one duplicate
        new_content = b'brand new object'
        new_key = source.put_object_from_filelike(io.BytesIO(new_content))
        source_duplicate_key = source.put_object_from_filelike(io.BytesIO(duplicate_content))

        # Import to target
        imported_keys = target.import_objects_to_pack(source, {new_key, source_duplicate_key})

        # Verify import results
        assert set(imported_keys) == {new_key, source_duplicate_key}
        assert duplicate_key == source_duplicate_key  # Same content = same hash

        # Verify final state:
        # - 1 loose (new_loose_key, unchanged)
        # - 4 packed (3 original + 1 new, duplicate was deduplicated)
        with target._container as container:
            counts = container.count_objects()
            assert counts.loose == 1
            assert counts.packed == 4

        # Verify all objects are accessible
        for key, expected_content in [
            (existing_loose_key, existing_loose_content),
            (existing_packed_key, existing_packed_content),
            (duplicate_key, duplicate_content),
            (new_loose_key, new_loose_content),
            (new_key, new_content),
        ]:
            assert target.has_object(key)
            with target.open(key) as handle:
                assert handle.read() == expected_content
