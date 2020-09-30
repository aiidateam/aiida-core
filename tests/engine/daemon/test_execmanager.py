# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.engine.daemon.execmanager` module."""
import io
import os
import pytest

from aiida.engine.daemon import execmanager
from aiida.transports.plugins.local import LocalTransport


@pytest.mark.usefixtures('clear_database_before_test')
def test_retrieve_files_from_list(tmp_path_factory, generate_calculation_node):
    """Test the `retrieve_files_from_list` function."""
    node = generate_calculation_node()

    retrieve_list = [
        'file_a.txt',
        ('sub/folder', 'sub/folder', 0),
    ]

    source = tmp_path_factory.mktemp('source')
    target = tmp_path_factory.mktemp('target')

    content_a = b'content_a'
    content_b = b'content_b'

    with open(str(source / 'file_a.txt'), 'wb') as handle:
        handle.write(content_a)
        handle.flush()

    os.makedirs(str(source / 'sub' / 'folder'))

    with open(str(source / 'sub' / 'folder' / 'file_b.txt'), 'wb') as handle:
        handle.write(content_b)
        handle.flush()

    with LocalTransport() as transport:
        transport.chdir(str(source))
        execmanager.retrieve_files_from_list(node, transport, str(target), retrieve_list)

    assert sorted(os.listdir(str(target))) == sorted(['file_a.txt', 'sub'])
    assert os.listdir(str(target / 'sub')) == ['folder']
    assert os.listdir(str(target / 'sub' / 'folder')) == ['file_b.txt']

    with open(str(target / 'sub' / 'folder' / 'file_b.txt'), 'rb') as handle:
        assert handle.read() == content_b

    with open(str(target / 'file_a.txt'), 'rb') as handle:
        assert handle.read() == content_a


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
