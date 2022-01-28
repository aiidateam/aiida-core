# -*- coding: utf-8 -*-
"""Test fixtures for the :mod:`aiida.repository` module."""
import os
import pathlib
import typing

import pytest


@pytest.fixture
def generate_directory(tmp_path: pathlib.Path) -> typing.Callable:
    """Construct a temporary directory with some arbitrary file hierarchy in it."""

    def _generate_directory(metadata: dict = None) -> pathlib.Path:
        """Construct the contents of the temporary directory based on the metadata mapping.

        :param: file object hierarchy to construct. Each key corresponds to either a directory or file to create. If the
            value is a dictionary a directory is created with the name of the key. Otherwise it is assumed to be a file.
            The value should be the byte string that should be written to file or `None` if the file should be empty.
            Example metadata:

                {
                    'relative': {
                        'empty_folder': {},
                        'empty_file': None,
                        'filename': b'content',
                    }
                }

            will yield a directory with the following file hierarchy:

                relative
                └── empty_folder
                |     └──
                └── empty_file
                └── filename


        :return: the path to the temporary directory
        """
        if metadata is None:
            metadata = {}

        def create_files(basepath: pathlib.Path, data: dict):
            """Construct the files in data at the given basepath."""
            for key, values in data.items():
                if isinstance(values, dict):
                    dirpath = os.path.join(basepath, key)
                    os.makedirs(dirpath, exist_ok=True)
                    create_files(dirpath, values)
                else:
                    filepath = os.path.join(basepath, key)
                    with open(filepath, 'wb') as handle:
                        if values is not None:
                            handle.write(values)

        create_files(tmp_path, metadata)

        return pathlib.Path(tmp_path)

    return _generate_directory
