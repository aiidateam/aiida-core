# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :mod:`aiida.engine.daemon.execmanager` module."""
import io
import os
import pathlib
import typing

import pytest

from aiida.engine.daemon import execmanager
from aiida.transports.plugins.local import LocalTransport


def serialize_file_hierarchy(dirpath: pathlib.Path) -> typing.Dict:
    """Serialize the file hierarchy at ``dirpath``.

    .. note:: empty directories are ignored.

    :param dirpath: the base path.
    :return: a mapping representing the file hierarchy, where keys are filenames. The leafs correspond to files and the
        values are the text contents.
    """
    serialized = {}

    for root, _, files in os.walk(dirpath):
        for filepath in files:

            relpath = pathlib.Path(root).relative_to(dirpath)
            subdir = serialized
            if relpath.parts:
                for part in relpath.parts:
                    subdir = subdir.setdefault(part, {})
            subdir[filepath] = (pathlib.Path(root) / filepath).read_text()

    return serialized


def create_file_hierarchy(hierarchy: typing.Dict, basepath: pathlib.Path) -> None:
    """Create the file hierarchy represented by the hierarchy created by ``serialize_file_hierarchy``.

    .. note:: empty directories are ignored and are not created explicitly on disk.

    :param hierarchy: mapping with structure returned by ``serialize_file_hierarchy``.
    :param basepath: the basepath where to write the hierarchy to disk.
    """
    for filename, value in hierarchy.items():
        if isinstance(value, dict):
            create_file_hierarchy(value, basepath / filename)
        else:
            basepath.mkdir(parents=True, exist_ok=True)
            (basepath / filename).write_text(value)


@pytest.fixture
def file_hierarchy():
    """Return a sample nested file hierarchy."""
    return {
        'file_a.txt': 'file_a',
        'path': {
            'file_b.txt': 'file_b',
            'sub': {
                'file_c.txt': 'file_c',
                'file_d.txt': 'file_d'
            }
        }
    }


def test_hierarchy_utility(file_hierarchy, tmp_path):
    """Test that the ``create_file_hierarchy`` and ``serialize_file_hierarchy`` function as intended.

    This is tested by performing a round-trip.
    """
    create_file_hierarchy(file_hierarchy, tmp_path)
    assert serialize_file_hierarchy(tmp_path) == file_hierarchy


# yapf: disable
@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.parametrize('retrieve_list, expected_hierarchy', (
    # Single file or folder, either toplevel or nested
    (['file_a.txt'], {'file_a.txt': 'file_a'}),
    (['path/sub/file_c.txt'], {'file_c.txt': 'file_c'}),
    (['path'], {'path': {'file_b.txt': 'file_b', 'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
    (['path/sub'], {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}),
    # Single nested file that is retrieved keeping a varying level of depth of original hierarchy
    ([('path/sub/file_c.txt', '.', 3)], {'path': {'sub': {'file_c.txt': 'file_c'}}}),
    ([('path/sub/file_c.txt', '.', 2)], {'sub': {'file_c.txt': 'file_c'}}),
    ([('path/sub/file_c.txt', '.', 1)], {'file_c.txt': 'file_c'}),
    ([('path/sub/file_c.txt', '.', 0)], {'file_c.txt': 'file_c'}),
    # Single nested folder that is retrieved keeping a varying level of depth of original hierarchy
    ([('path/sub', '.', 2)], {'path': {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
    ([('path/sub', '.', 1)], {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}),
    # Using globbing patterns
    ([('path/*', '.', 0)], {'file_b.txt': 'file_b', 'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}),
    ([('path/sub/*', '.', 0)], {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}),  # This is identical to ['path/sub']
    ([('path/sub/*c.txt', '.', 2)], {'sub': {'file_c.txt': 'file_c'}}),
    ([('path/sub/*c.txt', '.', 0)], {'file_c.txt': 'file_c'}),
    # Different target directory
    ([('path/sub/file_c.txt', 'target', 3)], {'target': {'path': {'sub': {'file_c.txt': 'file_c'}}}}),
    ([('path/sub', 'target', 1)], {'target': {'sub': {'file_c.txt': 'file_c', 'file_d.txt': 'file_d'}}}),
    ([('path/sub/*c.txt', 'target', 2)], {'target': {'sub': {'file_c.txt': 'file_c'}}}),
    # Missing files should be ignored and not cause the retrieval to except
    (['file_a.txt', 'file_u.txt', 'path/file_u.txt', ('path/sub/file_u.txt', '.', 3)], {'file_a.txt': 'file_a'}),
))
# yapf: enable
def test_retrieve_files_from_list(
    tmp_path_factory, generate_calculation_node, file_hierarchy, retrieve_list, expected_hierarchy
):
    """Test the `retrieve_files_from_list` function."""
    source = tmp_path_factory.mktemp('source')
    target = tmp_path_factory.mktemp('target')

    create_file_hierarchy(file_hierarchy, source)

    with LocalTransport() as transport:
        node = generate_calculation_node()
        transport.chdir(source)
        execmanager.retrieve_files_from_list(node, transport, target, retrieve_list)

    assert serialize_file_hierarchy(target) == expected_hierarchy


@pytest.mark.usefixtures('clear_database_before_test')
def test_upload_local_copy_list(fixture_sandbox, aiida_localhost, aiida_local_code_factory):
    """Test the ``local_copy_list`` functionality in ``upload_calculation``.

    Specifically, verify that files in the ``local_copy_list`` do not end up in the repository of the node.
    """
    from aiida.common.datastructures import CalcInfo, CodeInfo
    from aiida.orm import CalcJobNode, SinglefileData

    inputs = {
        'file_a': SinglefileData(io.BytesIO(b'content_a')).store(),
        'file_b': SinglefileData(io.BytesIO(b'content_b')).store(),
    }

    node = CalcJobNode(computer=aiida_localhost)
    node.store()

    code = aiida_local_code_factory('arithmetic.add', '/bin/bash').store()
    code_info = CodeInfo()
    code_info.code_uuid = code.uuid

    calc_info = CalcInfo()
    calc_info.uuid = node.uuid
    calc_info.codes_info = [code_info]
    calc_info.local_copy_list = [
        (inputs['file_a'].uuid, inputs['file_a'].filename, './files/file_a'),
        (inputs['file_a'].uuid, inputs['file_a'].filename, './files/file_b'),
    ]

    with LocalTransport() as transport:
        execmanager.upload_calculation(node, transport, calc_info, fixture_sandbox)

    assert node.list_object_names() == []
