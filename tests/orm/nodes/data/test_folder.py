###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `FolderData` class."""

import warnings

import pytest

from aiida.orm import FolderData


def test_constructor_tree(tmp_path):
    """Test the `tree` constructor keyword."""
    tree = {
        'a.txt': 'Content of file A\nWith some newlines',
        'b.txt': 'Content of file B without newline',
    }
    for filename, content in tree.items():
        tmp_path.joinpath(filename).write_text(content, encoding='utf8')
    node = FolderData.from_tree(str(tmp_path))
    assert sorted(node.base.repository.list_object_names()) == sorted(tree.keys())


def test_cli_repo_source_tree(tmp_path):
    """Test that the CLI tree input maps to relative repository paths."""
    nested = tmp_path / 'nested'
    nested.mkdir()
    (nested / 'file.txt').write_text('tree content', encoding='utf8')

    model = FolderData.cli_spec.validate({'tree': tmp_path})
    node = model.to_entity()

    assert node.base.repository.list_object_names('nested') == ['file.txt']
    assert node.base.repository.get_object_content('nested/file.txt') == 'tree content'


@pytest.mark.parametrize(
    'method',
    (
        'list_objects',
        'list_object_names',
        'open',
        'as_path',
        'get_object',
        'get_object_content',
        'put_object_from_bytes',
        'put_object_from_filelike',
        'put_object_from_file',
        'put_object_from_tree',
        'walk',
        'glob',
        'copy_tree',
        'delete_object',
        'erase',
    ),
)
def test_api(method):
    """Test the direct interface can be called without deprecation warnings.

    During the reorganization of the ``Node`` interface, the repository methods were moved to the ``base.repository``
    namespace and deprecation warnings would be printed when the repository interface would be called directly from the
    top-level namespace. The change was corrected for the ``FolderData`` since for that data type the repository API
    _should_ be the direct interface, and users should not have to go down the ``.base.repository`` namespace. Here we
    test that no deprecation warnings are emitted for the public API. Once the deprecation warnings are removed in
    AiiDA v3.0, this test can also be removed.
    """
    node = FolderData()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        try:
            getattr(node, method)()
        except Exception:
            pass
    assert len(caught) == 0
