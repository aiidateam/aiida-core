###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Extras tests for the export and import routines"""

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


@pytest.fixture(scope='function')
def new_archive(aiida_profile, tmp_path):
    """Create a new archive"""
    data = orm.Data()
    data.label = 'my_test_data_node'
    data.store()
    data.base.extras.set_many({'b': 2, 'c': 3})
    archive_file = tmp_path / 'export.aiida'
    create_archive([data], filename=archive_file)
    aiida_profile.reset_storage()
    yield archive_file


def import_extras(path, import_new_extras=True) -> orm.Data:
    """Import an aiida database"""
    import_archive(path, import_new_extras=import_new_extras, merge_extras=('k', 'c', 'l'))

    builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})
    data = builder.all()
    assert builder.count() == 1, data
    return data[0][0]


def modify_extras(path, imported_node, mode_existing) -> orm.Data:
    """Import the same aiida database again"""
    imported_node.base.extras.set('a', 1)
    imported_node.base.extras.set('b', 1000)
    imported_node.base.extras.delete('c')

    import_archive(path, merge_extras=mode_existing)

    # Query again the database
    builder = orm.QueryBuilder().append(orm.Data, filters={'label': 'my_test_data_node'})
    assert builder.count() == 1
    return builder.all()[0][0]


def test_import_of_extras(new_archive):
    """Check if extras are properly imported"""
    imported_node = import_extras(new_archive)
    assert imported_node.base.extras.get('b') == 2
    assert imported_node.base.extras.get('c') == 3


def test_absence_of_extras(new_archive):
    """Check whether extras are not imported if the mode is set to 'none'"""
    imported_node = import_extras(new_archive, import_new_extras=False)
    with pytest.raises(AttributeError):
        # the extra 'b' should not exist
        imported_node.base.extras.get('b')
    with pytest.raises(AttributeError):
        # the extra 'c' should not exist
        imported_node.base.extras.get('c')


def test_extras_import_mode_keep_existing(new_archive):
    """Check if old extras are not modified in case of name collision
    (keep original, create new, leave original)
    """
    imported_node = import_extras(new_archive)
    imported_node = modify_extras(new_archive, imported_node, mode_existing=('k', 'c', 'l'))

    # Check that extras are imported correctly
    assert imported_node.base.extras.get('a') == 1
    assert imported_node.base.extras.get('b') == 1000
    assert imported_node.base.extras.get('c') == 3


def test_extras_import_mode_update_existing(new_archive):
    """Check if old extras are modified in case of name collision
    (keep original, create new, update original)
    """
    imported_node = import_extras(new_archive)
    imported_node = modify_extras(new_archive, imported_node, mode_existing=('k', 'c', 'u'))

    # Check that extras are imported correctly
    assert imported_node.base.extras.get('a') == 1
    assert imported_node.base.extras.get('b') == 2
    assert imported_node.base.extras.get('c') == 3


def test_extras_import_mode_mirror(new_archive):
    """Check if old extras are fully overwritten by the imported ones
    (not keep original, create new, update original)
    """
    imported_node = import_extras(new_archive)
    imported_node = modify_extras(new_archive, imported_node, mode_existing=('n', 'c', 'u'))

    # Check that extras are imported correctly
    with pytest.raises(AttributeError):  # the extra
        # 'a' should not exist, as the extras were fully mirrored with respect to
        # the imported node
        imported_node.base.extras.get('a')
    assert imported_node.base.extras.get('b') == 2
    assert imported_node.base.extras.get('c') == 3


def test_extras_import_mode_none(new_archive):
    """Check if old extras are fully overwritten by the imported ones
    (keep original, not create new, leave original)
    """
    imported_node = import_extras(new_archive)
    imported_node = modify_extras(new_archive, imported_node, mode_existing=('k', 'n', 'l'))

    # Check if extras are imported correctly
    assert imported_node.base.extras.get('b') == 1000
    assert imported_node.base.extras.get('a') == 1
    with pytest.raises(AttributeError):  # the extra
        # 'c' should not exist, as the extras were keept untached
        imported_node.base.extras.get('c')


def test_extras_import_mode_strange(new_archive):
    """Check a mode that probably does not make much sense but is still available
    (keep original, create new, delete)
    """
    imported_node = import_extras(new_archive)
    imported_node = modify_extras(new_archive, imported_node, mode_existing=('k', 'c', 'd'))

    # Check if extras are imported correctly
    assert imported_node.base.extras.get('a') == 1
    assert imported_node.base.extras.get('c') == 3
    with pytest.raises(AttributeError):  # the extra
        # 'b' should not exist, as the collided extras are deleted
        imported_node.base.extras.get('b')


def test_extras_import_mode_correct(new_archive):
    """Test all possible import modes except 'ask'"""
    import_extras(new_archive)
    for mode1 in ['k', 'n']:  # keep or not keep old extras
        for mode2 in ['n', 'c']:  # create or not create new extras
            for mode3 in ['l', 'u', 'd']:  # leave old, update or delete collided extras
                import_archive(new_archive, merge_extras=(mode1, mode2, mode3))


def test_extras_import_mode_wrong(new_archive):
    """Check a mode that is wrong"""
    import_extras(new_archive)
    with pytest.raises(ValueError):
        import_archive(new_archive, merge_extras=('x', 'n', 'd'))  # first letter is wrong
    with pytest.raises(ValueError):
        import_archive(new_archive, merge_extras=('n', 'x', 'd'))  # second letter is wrong
    with pytest.raises(ValueError):
        import_archive(new_archive, merge_extras=('n', 'n', 'x'))  # third letter is wrong
    with pytest.raises(ValueError):
        import_archive(new_archive, merge_extras=('n',))  # too short
    with pytest.raises(ValueError):
        import_archive(new_archive, merge_extras=('n', 'n', 'd', 'n', 'n'))  # too long
    with pytest.raises(TypeError):
        import_archive(new_archive, merge_extras=5)  # wrong type
