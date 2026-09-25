###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test utility to import, inspect, or migrate AiiDA export archives."""

import json
import os
import tarfile
import zipfile

from archive_path import read_file_in_tar, read_file_in_zip

from tests.static import STATIC_DIR


def get_archive_file(archive: str, filepath=None, external_module=None) -> str:
    """Return the absolute path of the archive file used for testing purposes.

    The expected path for these files:

        tests.static.filepath

    :param archive: the relative filename of the archive
    :param filepath: str of directories of where to find archive (starting "/"s are irrelevant)
    :param external_module: string with name of external module, where archive can be found
    :return: absolute filepath of the archive test file
    """
    import importlib

    # Initialize
    dirpath_archive = archive

    # If the complete path has already been given, return archive immediately
    if os.path.isabs(dirpath_archive):
        return dirpath_archive

    # Add possible filepath
    if filepath and not isinstance(filepath, str):
        raise TypeError('filepath must be a string')
    elif filepath:
        dirpath_archive = os.path.join(*filepath.split(os.sep), dirpath_archive)

    # Use possible external module (otherwise use default, see above)
    if external_module and not isinstance(external_module, str):
        raise TypeError('external_module must be a string')
    elif external_module:
        # Use external module (will prepend the absolute path to `external_module`)
        external_path = os.path.dirname(os.path.realpath(importlib.import_module(external_module).__file__ or ''))

        dirpath_archive = os.path.join(external_path, dirpath_archive)
    else:
        # Add absolute path to local repo's static
        dirpath_archive = os.path.join(STATIC_DIR, dirpath_archive)

    if not os.path.isfile(dirpath_archive):
        dirpath_parent = os.path.dirname(dirpath_archive)
        msg = f'archive {archive} does not exist in the archives directory {dirpath_parent}'
        raise ValueError(msg)

    return dirpath_archive


def import_test_archive(archive, filepath=None, external_module=None):
    """Import a test archive that is an AiiDA export archive

    :param archive: the relative filename of the archive
    :param filepath: str of directories of where to find archive (starting "/"s are irrelevant)
    :param external_module: string with name of external module, where archive can be found
    """
    from aiida.tools.archive import import_archive

    dirpath_archive = get_archive_file(archive, filepath=filepath, external_module=external_module)

    import_archive(dirpath_archive)


def generate_archive_main_0001(dest_dir) -> str:
    """Natively build the ``main_0001`` reference dataset and export it.

    This defines the fixture in code: one computer, one code, one sealed
    ``CalcJobNode`` with ``INPUT_CALC``/``CREATE`` links, seven bare data
    nodes, four groups and one user.

    :param dest_dir: directory to write ``export_main_0001_simple.aiida`` into
    :return: absolute filepath of the generated archive

    Requires a loaded profile (e.g. via ``aiida_profile_tmp``).
    """
    from pathlib import Path

    return _generate_archive(Path(dest_dir) / 'export_main_0001_simple.aiida', _build_main_0001_dataset)


def generate_archive_at_version(version: str, dest_dir) -> str:
    """Build the reference dataset and export it as an archive *at* ``version``.

    The dataset is built natively (see :func:`_build_main_0001_dataset`) and exported at head,
    then downgraded to ``version`` via alembic, so the resulting file reports ``version``
    from :meth:`ArchiveFormatSqlZip.read_version`.

    :param version: target archive schema version (must be ``<=`` head, downgrade must exist)
    :param dest_dir: directory to write ``export_<version>_simple.aiida`` into
    :return: absolute filepath of the generated archive at ``version``

    Requires a loaded profile (e.g. via ``aiida_profile_tmp``).
    """
    import json
    import shutil
    import tempfile
    import zipfile
    from pathlib import Path

    from alembic.command import downgrade

    from aiida.storage.sqlite_zip.migrations.utils import update_metadata
    from aiida.storage.sqlite_zip.migrator import (
        _alembic_connect,
        _migration_context,
        get_schema_version_head,
        list_versions,
    )
    from aiida.storage.sqlite_zip.utils import DB_FILENAME, META_FILENAME
    from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip

    head = get_schema_version_head()
    if version not in list_versions():
        msg = f'Unknown archive version {version!r}'
        raise ValueError(msg)

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f'export_{version}_simple.aiida'

    with tempfile.TemporaryDirectory(prefix='gen_archive_head') as tmpdir:
        head_path = Path(tmpdir) / 'head.aiida'
        _generate_archive(head_path, _build_main_0001_dataset)
        if version == head:
            shutil.move(str(head_path), dest)
            return str(dest)
        shutil.copyfile(head_path, dest)

    with tempfile.TemporaryDirectory(prefix='downgrade_archive') as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        db_path = tmpdir / DB_FILENAME
        with zipfile.ZipFile(dest, 'r') as zin:
            metadata = json.loads(zin.read(META_FILENAME))
            with zin.open(DB_FILENAME) as src, db_path.open('wb') as out:
                shutil.copyfileobj(src, out)
        # The exported database carries no ``alembic_version`` table (the version lives
        # in ``metadata.json``), so stamp it with the head revision first, mirroring ``migrate()``.
        with _migration_context(db_path) as context:
            assert context.script is not None
            assert context.connection is not None
            context.stamp(context.script, head)
            context.connection.commit()
        with _alembic_connect(db_path, enforce_foreign_keys=False) as config:
            downgrade(config, version)
        update_metadata(metadata, version)
        new_path = tmpdir / 'downgraded.aiida'
        with zipfile.ZipFile(dest, 'r') as zin:
            with zipfile.ZipFile(new_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
                for item in zin.infolist():
                    if item.filename in (DB_FILENAME, META_FILENAME):
                        continue
                    zout.writestr(item, zin.read(item.filename))
                zout.write(db_path, DB_FILENAME)
                zout.writestr(META_FILENAME, json.dumps(metadata))
        shutil.move(str(new_path), dest)

    archive_format = ArchiveFormatSqlZip()
    assert archive_format.read_version(dest) == version
    return str(dest)


def generate_archive_main_0003(dest_dir) -> str:
    """Natively build the ``main_0003`` reference dataset and export it.

    The ``main_0003`` migration only rewrites legacy ``Code`` nodes, so the reference
    data is unchanged from ``main_0001``. Once a revision changes the
    schema, give it its own builder instead of delegating here.

    :param dest_dir: directory to write ``export_main_0003_simple.aiida`` into
    :return: absolute filepath of the generated archive

    Requires a loaded profile (e.g. via ``aiida_profile_tmp``).
    """
    from pathlib import Path

    return _generate_archive(Path(dest_dir) / 'export_main_0003_simple.aiida', _build_main_0001_dataset)


def generate_archive_head(dest_dir) -> str:
    """Generate the reference simple archive for the head version.

    Currently redirects to :func:`generate_archive_main_0003`. Dispatches
    explicitly per revision so a future head without a registered builder
    fails loudly instead of silently reusing stale content.

    :param dest_dir: directory to write ``export_<head>_simple.aiida`` into
    :return: absolute filepath of the generated archive at the head version

    Requires a loaded profile (e.g. via ``aiida_profile_tmp``).
    """
    from aiida.storage.sqlite_zip.migrator import get_schema_version_head

    head = get_schema_version_head()
    builders = {
        'main_0001': generate_archive_main_0001,
        'main_0003': generate_archive_main_0003,
    }
    try:
        builder = builders[head]
    except KeyError:
        msg = f'No reference dataset defined for archive version {head!r}'
        raise ValueError(msg) from None
    return builder(dest_dir)


def _generate_archive(dest, build_dataset) -> str:
    """Build a dataset in the loaded profile and export it to ``dest``.

    Requires a loaded profile; test callers get one from the ``aiida_profile_tmp``
    or ``aiida_profile_factory`` fixtures, the manual script manages its own.
    """
    from aiida import orm
    from aiida.storage.sqlite_zip.migrator import get_schema_version_head
    from aiida.tools.archive.create import create_archive
    from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip

    head = get_schema_version_head()

    entities = build_dataset()
    output = create_archive(entities, filename=dest, overwrite=True)
    assert output == dest

    archive_format = ArchiveFormatSqlZip()
    assert archive_format.read_version(dest) == head == archive_format.latest_version
    with archive_format.open(dest, 'r') as reader:
        assert reader.querybuilder().append(orm.Node).count() == 10
        assert reader.querybuilder().append(orm.Group).count() == 4
        assert reader.querybuilder().append(orm.Computer).count() == 1
        assert reader.querybuilder().append(orm.User).count() == 1
    return str(dest)


def _build_main_0001_dataset():
    """Create the ``main_0001`` reference nodes, computer and groups. Return all entities to export."""
    from aiida import orm
    from aiida.common.links import LinkType

    computer = orm.Computer(
        label='simple-computer',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.direct',
    ).store()

    code = orm.InstalledCode(computer=computer, filepath_executable='/bin/true', label='simple-code').store()

    dict_in = orm.Dict({'x': 1}).store()
    calc = orm.CalcJobNode(computer=computer)
    # input links on process nodes must be added before storing them
    calc.base.links.add_incoming(dict_in, LinkType.INPUT_CALC, 'input')
    calc.store()

    dict_out = orm.Dict({'y': 2}).store()
    dict_out.base.links.add_incoming(calc, LinkType.CREATE, 'output')
    # seal only once all links are in place: sealed nodes cannot gain outgoing links
    calc.seal()

    dict_extra = orm.Dict({'z': 3}).store()
    list_node = orm.List([1, 2, 3]).store()
    int_node = orm.Int(42).store()
    str_node = orm.Str('hello').store()
    float_node = orm.Float(3.14).store()
    remote = orm.RemoteData(remote_path='/tmp/simple', computer=computer).store()

    nodes = [code, calc, dict_in, dict_out, dict_extra, list_node, int_node, str_node, float_node, remote]
    assert len(nodes) == 10

    groups = []
    for label, members in [
        ('testing1', [dict_in, dict_out, calc]),
        ('testing2', [list_node, int_node]),
        ('testing3', [str_node, float_node, dict_extra]),
        ('testing4', [code, remote]),
    ]:
        group = orm.Group(label=label).store()
        group.add_nodes(members)
        groups.append(group)

    return [computer, *nodes, *groups]


def read_json_files(path, *, names=('metadata.json', 'data.json')) -> list[dict]:
    """Get metadata.json and data.json from an exported AiiDA archive

    :param path: the filepath of the archive
    :param names: the files to retrieve

    """
    jsons: list[dict] = []

    if zipfile.is_zipfile(path):
        for name in names:
            jsons.append(json.loads(read_file_in_zip(path, name)))
    elif tarfile.is_tarfile(path):
        for name in names:
            jsons.append(json.loads(read_file_in_tar(path, name)))
    else:
        raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

    return jsons
