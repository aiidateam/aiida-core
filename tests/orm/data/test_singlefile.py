# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `SinglefileData` class."""

import os
import io
import tempfile
import pathlib

import pytest

from aiida.orm import SinglefileData, load_node


@pytest.fixture
def check_singlefile_content():
    """Fixture to check the content of a SinglefileData.

    Checks the content of a SinglefileData node against the given
    reference content and filename.
    """

    def inner(node, content_reference, filename, open_mode='r'):
        with node.open(mode=open_mode) as handle:
            assert handle.read() == content_reference

        assert node.list_object_names() == [filename]

    return inner


@pytest.fixture
def check_singlefile_content_with_store(check_singlefile_content):  # pylint: disable=redefined-outer-name
    """Fixture to check the content of a SinglefileData before and after .store().

    Checks the content of a SinglefileData node against the given reference
    content and filename twice, before and after calling .store().
    """

    def inner(node, content_reference, filename, open_mode='r'):
        check_singlefile_content(
            node=node,
            content_reference=content_reference,
            filename=filename,
            open_mode=open_mode,
        )
        node.store()
        check_singlefile_content(
            node=node,
            content_reference=content_reference,
            filename=filename,
            open_mode=open_mode,
        )

    return inner


def test_reload_singlefile_data(
    clear_database_before_test,  # pylint: disable=unused-argument
    check_singlefile_content_with_store,  # pylint: disable=redefined-outer-name
    check_singlefile_content  # pylint: disable=redefined-outer-name
):
    """Test writing and reloading a `SinglefileData` instance."""
    content_original = 'some text ABCDE'

    with tempfile.NamedTemporaryFile(mode='w+') as handle:
        filepath = handle.name
        basename = os.path.basename(filepath)
        handle.write(content_original)
        handle.flush()
        node = SinglefileData(file=filepath)

    check_singlefile_content_with_store(
        node=node,
        content_reference=content_original,
        filename=basename,
    )

    node_loaded = load_node(node.uuid)
    assert isinstance(node_loaded, SinglefileData)

    check_singlefile_content(
        node=node,
        content_reference=content_original,
        filename=basename,
    )
    check_singlefile_content(
        node=node_loaded,
        content_reference=content_original,
        filename=basename,
    )


def test_construct_from_filelike(
    clear_database_before_test,  # pylint: disable=unused-argument
    check_singlefile_content_with_store  # pylint: disable=redefined-outer-name
):
    """Test constructing an instance from filelike instead of filepath."""
    content_original = 'some testing text\nwith a newline'

    with tempfile.NamedTemporaryFile(mode='wb+') as handle:
        basename = os.path.basename(handle.name)
        handle.write(content_original.encode('utf-8'))
        handle.flush()
        handle.seek(0)
        node = SinglefileData(file=handle)

    check_singlefile_content_with_store(
        node=node,
        content_reference=content_original,
        filename=basename,
    )


def test_construct_from_string(
    clear_database_before_test,  # pylint: disable=unused-argument
    check_singlefile_content_with_store  # pylint: disable=redefined-outer-name
):
    """Test constructing an instance from a string."""
    content_original = 'some testing text\nwith a newline'

    with io.BytesIO(content_original.encode('utf-8')) as handle:
        node = SinglefileData(file=handle)

    check_singlefile_content_with_store(
        node=node,
        content_reference=content_original,
        filename=SinglefileData.DEFAULT_FILENAME,
    )


def test_construct_with_path(
    clear_database_before_test,  # pylint: disable=unused-argument
    check_singlefile_content_with_store  # pylint: disable=redefined-outer-name
):
    """Test constructing an instance from a pathlib.Path."""
    content_original = 'please report to the ministry of silly walks'

    with tempfile.NamedTemporaryFile(mode='w+') as handle:
        filepath = pathlib.Path(handle.name).resolve()
        filename = filepath.name
        handle.write(content_original)
        handle.flush()
        node = SinglefileData(file=filepath)

    check_singlefile_content_with_store(
        node=node,
        content_reference=content_original,
        filename=filename,
    )


def test_construct_with_filename(
    clear_database_before_test,  # pylint: disable=unused-argument
    check_singlefile_content  # pylint: disable=redefined-outer-name
):
    """Test constructing an instance, providing a filename."""
    content_original = 'some testing text\nwith a newline'
    filename = 'myfile.txt'

    # test creating from string
    with io.BytesIO(content_original.encode('utf-8')) as handle:
        node = SinglefileData(file=handle, filename=filename)

    check_singlefile_content(node=node, content_reference=content_original, filename=filename)

    # test creating from file
    with tempfile.NamedTemporaryFile(mode='wb+') as handle:
        handle.write(content_original.encode('utf-8'))
        handle.flush()
        handle.seek(0)
        node = SinglefileData(file=handle, filename=filename)

    check_singlefile_content(node=node, content_reference=content_original, filename=filename)


def test_binary_file(
    clear_database_before_test,  # pylint: disable=unused-argument
    check_singlefile_content_with_store  # pylint: disable=redefined-outer-name
):
    """Test that the constructor accepts binary files."""
    byte_array = [120, 3, 255, 0, 100]
    content_binary = bytearray(byte_array)

    with tempfile.NamedTemporaryFile(mode='wb+') as handle:
        basename = os.path.basename(handle.name)
        handle.write(bytearray(content_binary))
        handle.flush()
        handle.seek(0)
        node = SinglefileData(handle.name)

    check_singlefile_content_with_store(
        node=node,
        content_reference=content_binary,
        filename=basename,
        open_mode='rb',
    )
