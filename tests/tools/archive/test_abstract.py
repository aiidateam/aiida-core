###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for archive abstraction.

The tests highlight the features of the archive abstraction.
"""

from io import BytesIO

import pytest

from aiida import orm
from aiida.common.exceptions import IntegrityError
from aiida.orm.entities import EntityTypes
from aiida.tools.archive import ArchiveFormatSqlZip


def test_write_read(tmp_path):
    """Test writing a simple archive then reading it."""
    archive_path = tmp_path / 'archive.aiida'
    archive_format = ArchiveFormatSqlZip()

    with archive_format.open(archive_path, 'x') as writer:
        # this should insert nothing
        writer.bulk_insert(EntityTypes.USER, [])
        # this should fail due to missing fields
        with pytest.raises(IntegrityError, match='Incorrect fields'):
            writer.bulk_insert(EntityTypes.USER, [{}])
        user_row1 = {
            'id': 1,
            'email': 'jon@doe.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'institution': 'Doe Inc.',
        }
        # should fail due to unknown field
        with pytest.raises(IntegrityError, match='Incorrect fields'):
            writer.bulk_insert(EntityTypes.USER, [{**user_row1, **{'unknown': 'field'}}])
        # correctly add a user
        writer.bulk_insert(EntityTypes.USER, [user_row1])
        # should fail unique constraint
        with pytest.raises(IntegrityError):
            writer.bulk_insert(EntityTypes.USER, [user_row1])
        # add an object to the repository
        object_key1 = writer.put_object(BytesIO(b'hallo'))
        # adding the same object again should be a no-op (due to de-duplication)
        assert writer.put_object(BytesIO(b'hallo')) == object_key1

    # check the version has been written to the archive
    assert archive_format.read_version(archive_path) == archive_format.latest_version

    # check we can read the new archive
    with archive_format.open(archive_path, 'r') as reader:
        # get the metadata
        assert isinstance(reader.get_metadata(), dict)
        # retrieve the user
        query = reader.querybuilder().append(orm.User, tag='user', project=['**'])
        assert query.count() == 1
        user_data = query.dict()[0]['user']
        assert user_data == user_row1
        user = reader.get(orm.User, pk=user_data['id'])
        assert user.email == user_data['email']
        # retrieve the object
        repository = reader.get_backend().get_repository()
        assert set(repository.list_objects()) == {object_key1}
        with repository.open(object_key1) as obj:
            assert obj.read() == b'hallo'

    # now append to the archive
    with archive_format.open(archive_path, 'a') as appender:
        # add a second user
        user_row2 = {
            'id': 2,
            'email': 'jane@smith.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'institution': 'Doe Inc.',
        }
        appender.bulk_insert(EntityTypes.USER, [user_row2])
        # delete the existing object
        appender.delete_object(object_key1)
        # add an object to the repository
        object_key2 = appender.put_object(BytesIO(b'other'))

    # read the amended archive and check the content
    with archive_format.open(archive_path, 'r') as reader:
        query = reader.querybuilder().append(orm.User, tag='user', project=['**'])
        assert query.count() == 2
        repository = reader.get_backend().get_repository()
        assert set(repository.list_objects()) == {object_key2}
        assert repository.has_object(object_key2) is True
        assert repository.has_object('other') is False
        assert repository.has_objects([object_key2, 'other']) == [True, False]
        with repository.open(object_key2) as obj:
            assert obj.read() == b'other'
