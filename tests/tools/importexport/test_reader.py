# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for archive reader."""
# pylint: disable=pointless-statement,redefined-outer-name
import pytest

from aiida.common import InvalidOperation
from aiida.tools.importexport import EXPORT_VERSION, CorruptArchive
from aiida.tools.importexport.archive import get_reader
from tests.utils.archives import get_archive_file


@pytest.fixture
def archive_reader():
    """Return an initiated archive reader.

    If a filename is given, instantiate with that file,
    otherwise instantiate with the latest archive version.
    """

    def _func(filename=None):
        archive_path = get_archive_file(filename or f'export_v{EXPORT_VERSION}_simple.aiida', 'export/migrate')
        reader_cls = get_reader('zip')
        return reader_cls(archive_path)

    return _func


def test_reader(archive_reader):
    """Test reader API."""

    with archive_reader() as archive:
        assert archive.export_version == EXPORT_VERSION
        assert archive.metadata.aiida_version == '1.5.0'
        assert sorted(archive.entity_names) == ['Comment', 'Computer', 'Group', 'Log', 'Node', 'User']
        assert archive.entity_count('Node') == 10
        assert sum(1 for _ in archive.iter_entity_fields('Node')) == 10
        assert archive.entity_count('Computer') == 1
        assert archive.entity_count('User') == 1
        assert archive.entity_count('Group') == 4
        assert sum(1 for _ in archive.iter_group_uuids()) == 4
        assert archive.link_count == 8
        assert sum(1 for _ in archive.iter_link_data()) == 8
        assert next(archive.iter_entity_fields('Node', fields=('label', 'node_type', 'attributes'))) == (
            837, {
                'label': 'pw.x',
                'node_type': 'data.code.Code.',
                'attributes': {
                    'is_local': False,
                    'append_text': '',
                    'remote_exec_path': '/ssoft/quantum-espresso/5.1.1/RH6/intel-15.0.0/x86_E5v2/intel/pw.x',
                    'input_plugin': 'quantumespresso.pw',
                    'prepend_text': 'module load quantum-espresso/5.1.1/intel-15.0.0'
                }
            }
        )
        assert next(archive.iter_entity_fields('Group', fields=('type_string', 'user'))
                    ) == (50, {
                        'user': 1,
                        'type_string': 'core'
                    })


def test_context_required(archive_reader):
    """Verify that accessing a property of an Archive outside of a context manager raises."""
    archive = archive_reader()
    with pytest.raises(InvalidOperation, match='should be used within a context'):
        archive._extract(path_prefix='')  # pylint: disable=protected-access


def test_empty_archive(archive_reader):
    """Verify that attempting to unpack an empty archive raises a `CorruptArchive` exception."""
    with pytest.raises(CorruptArchive, match='input file cannot be read'):
        with archive_reader('empty.aiida') as archive:
            assert archive.export_version == EXPORT_VERSION
