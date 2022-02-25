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
from typing import Callable, Sequence

from archive_path import TarPath, ZipPath

from aiida.common import exceptions
from aiida.common.progress_reporter import create_callback, get_progress_reporter


def update_metadata(metadata, version):
    """Update the metadata with a new version number and a notification of the conversion that was executed.

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the updated metadata should get
    """
    from aiida import get_version

    old_version = metadata['export_version']
    conversion_info = metadata.get('conversion_info', [])

    conversion_message = f'Converted from version {old_version} to {version} with AiiDA v{get_version()}'
    conversion_info.append(conversion_message)

    metadata['aiida_version'] = get_version()
    metadata['export_version'] = version
    metadata['conversion_info'] = conversion_info


def verify_metadata_version(metadata, version=None):
    """Utility function to verify that the metadata has the correct version number.

    If no version number is passed, it will just extract the version number and return it.

    :param metadata: the content of an export archive metadata.json file
    :param version: string version number that the metadata is expected to have
    """
    try:
        metadata_version = metadata['export_version']
    except KeyError:
        raise exceptions.StorageMigrationError("metadata is missing the 'export_version' key")

    if version is None:
        return metadata_version

    if metadata_version != version:
        raise exceptions.StorageMigrationError(
            f'expected archive file with version {version} but found version {metadata_version}'
        )

    return None


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
