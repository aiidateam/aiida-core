# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Common variables"""
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable, Sequence, Union

from archive_path import TarPath, ZipPath
from sqlalchemy import event
from sqlalchemy.future.engine import Engine, create_engine

from aiida.common import json
from aiida.common.progress_reporter import create_callback, get_progress_reporter

META_FILENAME = 'metadata.json'
DB_FILENAME = 'db.sqlite3'
# folder to store repository files in
REPO_FOLDER = 'repo'


def sqlite_enforce_foreign_keys(dbapi_connection, _):
    """Enforce foreign key constraints, when using sqlite backend (off by default)"""
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON;')
    cursor.close()


def create_sqla_engine(path: Union[str, Path], *, enforce_foreign_keys: bool = True, **kwargs) -> Engine:
    """Create a new engine instance."""
    engine = create_engine(
        f'sqlite:///{path}',
        json_serializer=json.dumps,
        json_deserializer=json.loads,
        encoding='utf-8',
        future=True,
        **kwargs
    )
    if enforce_foreign_keys:
        event.listen(engine, 'connect', sqlite_enforce_foreign_keys)
    return engine


def copy_zip_to_zip(
    inpath: Path,
    outpath: Path,
    path_callback: Callable[[ZipPath, ZipPath], bool],
    *,
    compression: int = 6,
    overwrite: bool = True,
    title: str = 'Writing new zip file',
    info_order: Sequence[str] = ()
) -> None:
    """Create a new zip file from an existing zip file.

    All files/folders are streamed directly to the new zip file,
    with the ``path_callback`` allowing for per path modifications.
    The new zip file is first created in a temporary directory, and then moved to the desired location.

    :param inpath: the path to the existing archive
    :param outpath: the path to output the new archive
    :param path_callback: a callback that is called for each path in the archive: ``(inpath, outpath) -> handled``
        If handled is ``True``, the path is assumed to already have been copied to the new zip file.
    :param compression: the default compression level to use for the new zip file
    :param overwrite: whether to overwrite the output file if it already exists
    :param title: the title of the progress bar
    :param info_order: ``ZipInfo`` for these file names will be written first to the zip central directory.
        This allows for faster reading of these files, with ``archive_path.read_file_in_zip``.
    """
    if (not overwrite) and outpath.exists() and outpath.is_file():
        raise FileExistsError(f'{outpath} already exists')
    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_archive = Path(tmpdirname) / 'archive.zip'
        with ZipPath(temp_archive, mode='w', compresslevel=compression, info_order=info_order) as new_path:
            with ZipPath(inpath, mode='r') as path:
                length = sum(1 for _ in path.glob('**/*', include_virtual=False))
                with get_progress_reporter()(desc=title, total=length) as progress:
                    for subpath in path.glob('**/*', include_virtual=False):
                        new_path_sub = new_path.joinpath(subpath.at)
                        if path_callback(subpath, new_path_sub):
                            pass
                        elif subpath.is_dir():
                            new_path_sub.mkdir(exist_ok=True)
                        else:
                            new_path_sub.putfile(subpath)
                        progress.update()
        if overwrite and outpath.exists() and outpath.is_file():
            outpath.unlink()
        shutil.move(temp_archive, outpath)  # type: ignore[arg-type]


def copy_tar_to_zip(
    inpath: Path,
    outpath: Path,
    path_callback: Callable[[Path, ZipPath], bool],
    *,
    compression: int = 6,
    overwrite: bool = True,
    title: str = 'Writing new zip file',
    info_order: Sequence[str] = ()
) -> None:
    """Create a new zip file from an existing tar file.

    The tar file is first extracted to a temporary directory, and then the new zip file is created,
    with the ``path_callback`` allowing for per path modifications.
    The new zip file is first created in a temporary directory, and then moved to the desired location.

    :param inpath: the path to the existing archive
    :param outpath: the path to output the new archive
    :param path_callback: a callback that is called for each path in the archive: ``(inpath, outpath) -> handled``
        If handled is ``True``, the path is assumed to already have been copied to the new zip file.
    :param compression: the default compression level to use for the new zip file
    :param overwrite: whether to overwrite the output file if it already exists
    :param title: the title of the progress bar
    :param info_order: ``ZipInfo`` for these file names will be written first to the zip central directory.
        This allows for faster reading of these files, with ``archive_path.read_file_in_zip``.
    """
    if (not overwrite) and outpath.exists() and outpath.is_file():
        raise FileExistsError(f'{outpath} already exists')
    with tempfile.TemporaryDirectory() as tmpdirname:
        # for tar files we extract first, since the file is compressed as a single object
        temp_extracted = Path(tmpdirname) / 'extracted'
        with get_progress_reporter()(total=1) as progress:
            callback = create_callback(progress)
            TarPath(inpath, mode='r:*').extract_tree(
                temp_extracted,
                allow_dev=False,
                allow_symlink=False,
                callback=callback,
                cb_descript=f'{title} (extracting tar)'
            )
        temp_archive = Path(tmpdirname) / 'archive.zip'
        with ZipPath(temp_archive, mode='w', compresslevel=compression, info_order=info_order) as new_path:
            length = sum(1 for _ in temp_extracted.glob('**/*'))
            with get_progress_reporter()(desc=title, total=length) as progress:
                for subpath in temp_extracted.glob('**/*'):
                    new_path_sub = new_path.joinpath(subpath.relative_to(temp_extracted).as_posix())
                    if path_callback(subpath.relative_to(temp_extracted), new_path_sub):
                        pass
                    elif subpath.is_dir():
                        new_path_sub.mkdir(exist_ok=True)
                    else:
                        # files extracted from the tar do not include a modified time, yet zip requires one
                        os.utime(subpath, (subpath.stat().st_ctime, subpath.stat().st_ctime))
                        new_path_sub.putfile(subpath)
                    progress.update()

        if overwrite and outpath.exists() and outpath.is_file():
            outpath.unlink()
        shutil.move(temp_archive, outpath)  # type: ignore[arg-type]
