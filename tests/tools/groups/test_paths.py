###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for GroupPath"""

import pytest

from aiida import orm
from aiida.tools.groups.paths import GroupAttr, GroupNotFoundError, GroupPath, InvalidPath, NoGroupsInPathError


@pytest.fixture
def setup_groups(aiida_profile_clean):
    """Setup some groups for testing."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f']:
        group, _ = orm.Group.collection.get_or_create(label)
        group.description = f'A description of {label}'
    yield


@pytest.mark.parametrize('path', ('/a', 'a/', '/a/', 'a//b'))
def test_invalid_paths(setup_groups, path):
    """Invalid paths should raise an ``InvalidPath`` exception."""
    with pytest.raises(InvalidPath):
        GroupPath(path=path)


def test_root_path(setup_groups):
    """Test the root path properties"""
    group_path = GroupPath()
    assert group_path.path == ''
    assert group_path.delimiter == '/'
    assert group_path.parent is None
    assert group_path.is_virtual
    assert group_path.get_group() is None


def test_path_concatenation(setup_groups):
    """Test methods to build a new path."""
    group_path = GroupPath()
    assert (group_path / 'a').path == 'a'
    assert (group_path / 'a' / 'b').path == 'a/b'
    assert (group_path / 'a/b').path == 'a/b'
    assert group_path['a/b'].path == 'a/b'
    assert GroupPath('a/b/c') == GroupPath('a/b') / 'c'


def test_path_existence(setup_groups):
    """Test existence of child "folders"."""
    group_path = GroupPath()
    assert 'a' in group_path
    assert 'x' not in group_path


def test_group_retrieval(setup_groups):
    """Test retrieval of the actual group from a path.

    The ``group`` attribute will return None
    if no group is associated with the path
    """
    group_path = GroupPath()
    assert group_path['x'].is_virtual
    assert not group_path['a'].is_virtual
    assert group_path.get_group() is None
    assert isinstance(group_path['a'].get_group(), orm.Group)


def test_group_creation(setup_groups):
    """Test creation of new groups."""
    group_path = GroupPath()
    group, created = group_path['a'].get_or_create_group()
    assert isinstance(group, orm.Group)
    assert created is False
    group, created = group_path['x'].get_or_create_group()
    assert isinstance(group, orm.Group)
    assert created is True


def test_group_deletion(setup_groups):
    """Test deletion of existing groups."""
    group_path = GroupPath()
    assert not group_path['a'].is_virtual
    group_path['a'].delete_group()
    assert group_path['a'].is_virtual
    with pytest.raises(GroupNotFoundError):
        group_path['a'].delete_group()


def test_path_iteration(setup_groups):
    """Test iteration of groups."""
    group_path = GroupPath()
    assert len(group_path) == 1
    assert [(c.path, c.is_virtual) for c in group_path.children] == [('a', False)]
    child = next(group_path.children)
    assert child.parent == group_path
    assert len(child) == 3
    assert [(c.path, c.is_virtual) for c in sorted(child)] == [('a/b', False), ('a/c', True), ('a/f', False)]


def test_path_with_no_groups(setup_groups):
    """Test ``NoGroupsInPathError`` is raised if the path contains descendant groups."""
    group_path = GroupPath()
    with pytest.raises(NoGroupsInPathError):
        list(group_path['x'])


def test_walk(setup_groups):
    """Test the ``GroupPath.walk()`` function."""
    group_path = GroupPath()
    assert [c.path for c in sorted(group_path.walk())] == ['a', 'a/b', 'a/c', 'a/c/d', 'a/c/e', 'a/c/e/g', 'a/f']


@pytest.mark.filterwarnings('ignore::UserWarning')
def test_walk_with_invalid_path():
    """Test the ``GroupPath.walk`` method with invalid paths."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f', 'bad//group', 'bad/other']:
        orm.Group.collection.get_or_create(label)
    group_path = GroupPath()
    expected = ['a', 'a/b', 'a/c', 'a/c/d', 'a/c/e', 'a/c/e/g', 'a/f', 'bad', 'bad/other']
    assert [c.path for c in sorted(group_path.walk())] == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_walk_nodes():
    """Test the ``GroupPath.walk_nodes()`` function."""
    group, _ = orm.Group.collection.get_or_create('a')
    node = orm.Data()
    node.base.attributes.set_many({'i': 1, 'j': 2})
    node.store()
    group.add_nodes(node)
    group_path = GroupPath()
    assert [(r.group_path.path, r.node.base.attributes.all) for r in group_path.walk_nodes()] == [
        ('a', {'i': 1, 'j': 2})
    ]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_cls():
    """Test that only instances of `cls` or its subclasses are matched by ``GroupPath``."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g']:
        orm.Group.collection.get_or_create(label)
    for label in ['a/c/e', 'a/f']:
        orm.UpfFamily.collection.get_or_create(label)
    group_path = GroupPath()
    assert sorted([c.path for c in group_path.walk()]) == ['a', 'a/b', 'a/c', 'a/c/d', 'a/c/e', 'a/c/e/g']
    group_path = GroupPath(cls=orm.UpfFamily)
    assert sorted([c.path for c in group_path.walk()]) == ['a', 'a/c', 'a/c/e', 'a/f']
    assert GroupPath('a/b/c') != GroupPath('a/b/c', cls=orm.UpfFamily)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_attr():
    """Test ``GroupAttr``."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f', 'bad space', 'bad@char', '_badstart']:
        orm.Group.collection.get_or_create(label)
    group_path = GroupPath()
    assert isinstance(group_path.browse.a.c.d, GroupAttr)
    assert isinstance(group_path.browse.a.c.d(), GroupPath)
    assert group_path.browse.a.c.d().path == 'a/c/d'
    assert not set(dir(group_path.browse)).intersection(['bad space', 'bad@char', '_badstart'])
    with pytest.raises(AttributeError):
        group_path.browse.a.c.x


@pytest.mark.usefixtures('aiida_profile_clean')
def test_cls_label_clashes():
    """Test behaviour when multiple group classes have the same label."""
    group_01, _ = orm.Group.collection.get_or_create('a')
    node_01 = orm.Data().store()
    group_01.add_nodes(node_01)

    group_02, _ = orm.UpfFamily.collection.get_or_create('a')
    node_02 = orm.Data().store()
    group_02.add_nodes(node_02)

    # Requests for non-existing groups should return `None`
    assert GroupPath('b').get_group() is None

    assert GroupPath('a').group_ids == [group_01.pk]
    assert GroupPath('a').get_group().pk == group_01.pk
    expected = [('a', node_01.pk)]
    assert [(r.group_path.path, r.node.pk) for r in GroupPath('a').walk_nodes()] == expected

    assert GroupPath('a', cls=orm.UpfFamily).group_ids == [group_02.pk]
    assert GroupPath('a', cls=orm.UpfFamily).get_group().pk == group_02.pk
    expected = [('a', node_02.pk)]
    assert [(r.group_path.path, r.node.pk) for r in GroupPath('a', cls=orm.UpfFamily).walk_nodes()] == expected
