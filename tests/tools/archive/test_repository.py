# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the export for nodes with files in the repository."""
import os

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


@pytest.mark.usefixtures('aiida_profile_clean')
def test_export_repository(aiida_profile, tmp_path):
    """Test exporting a node with files in the repository."""
    node = orm.Data()
    node.base.repository.put_object_from_bytes(b'file_a', 'file_a')
    node.base.repository.put_object_from_bytes(b'file_b', 'relative/file_b')
    node.store()
    node_uuid = node.uuid
    repository_metadata = node.base.repository.metadata

    filepath = os.path.join(tmp_path / 'export.aiida')
    create_archive([node], filename=filepath)

    aiida_profile.clear_profile()
    import_archive(filepath)

    loaded = orm.load_node(uuid=node_uuid)
    assert loaded.base.repository.metadata == repository_metadata
    assert loaded.base.repository.get_object_content('file_a', mode='rb') == b'file_a'
    assert loaded.base.repository.get_object_content('relative/file_b', mode='rb') == b'file_b'
