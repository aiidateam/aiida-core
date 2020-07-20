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
import io
import os

from aiida import orm
from aiida.tools.importexport import export, import_data


def test_export_repository(aiida_profile, tmp_path):
    """Test exporting a node with files in the repository."""
    from aiida.manage.manager import get_manager

    aiida_profile.reset_db()

    node = orm.Data()
    node.put_object_from_filelike(io.BytesIO(b'file_a'), 'file_a')
    node.put_object_from_filelike(io.BytesIO(b'file_b'), 'relative/file_b')
    node.store()
    node_uuid = node.uuid
    repository_metadata = node.repository_metadata

    filepath = os.path.join(tmp_path / 'export.aiida')
    export([node], filename=filepath)

    aiida_profile.reset_db()
    container = get_manager().get_profile().get_repository_container()
    container.init_container(clear=True)
    import_data(filepath, silent=True)

    loaded = orm.load_node(uuid=node_uuid)
    assert loaded.repository_metadata == repository_metadata
    assert loaded.get_object_content('file_a', mode='rb') == b'file_a'
    assert loaded.get_object_content('relative/file_b', mode='rb') == b'file_b'
