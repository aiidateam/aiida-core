# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `FolderData` class."""
import pytest

from aiida.orm import FolderData


@pytest.mark.usefixtures('aiida_profile_clean')
def test_constructor_tree(tmp_path):
    """Test the `tree` constructor keyword."""
    tree = {
        'a.txt': 'Content of file A\nWith some newlines',
        'b.txt': 'Content of file B without newline',
    }
    for filename, content in tree.items():
        tmp_path.joinpath(filename).write_text(content, encoding='utf8')
    node = FolderData(tree=str(tmp_path))
    assert sorted(node.list_object_names()) == sorted(tree.keys())
