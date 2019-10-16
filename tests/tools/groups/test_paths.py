# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for GroupPath"""
# pylint: disable=redefined-outer-name,unused-argument
import pytest

from aiida import orm
from aiida.tools.groups.paths import (GroupAttr, GroupPath, InvalidPath, GroupNotFoundError, NoGroupsInPathError)


@pytest.fixture
def setup_groups(clear_database_before_test):
    """Setup some groups for testing."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f']:
        group, _ = orm.Group.objects.get_or_create(label, type_string=orm.GroupTypeString.USER.value)
        group.description = 'A description of {}'.format(label)
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


def test_walk_with_invalid_path(clear_database_before_test):
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f', 'bad//group', 'bad/other']:
        orm.Group.objects.get_or_create(label, type_string=orm.GroupTypeString.USER.value)
    group_path = GroupPath()
    assert [c.path for c in sorted(group_path.walk())
           ] == ['a', 'a/b', 'a/c', 'a/c/d', 'a/c/e', 'a/c/e/g', 'a/f', 'bad', 'bad/other']


def test_walk_nodes(clear_database):
    """Test the ``GroupPath.walk_nodes()`` function."""
    group, _ = orm.Group.objects.get_or_create('a', type_string=orm.GroupTypeString.USER.value)
    node = orm.Data()
    node.set_attribute_many({'i': 1, 'j': 2})
    node.store()
    group.add_nodes(node)
    group_path = GroupPath()
    assert [(r.group_path.path, r.node.attributes) for r in group_path.walk_nodes()] == [('a', {'i': 1, 'j': 2})]


def test_type_string(clear_database_before_test):
    """Test that only the type_string instantiated in ``GroupPath`` is returned."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g']:
        orm.Group.objects.get_or_create(label, type_string=orm.GroupTypeString.USER.value)
    for label in ['a/c/e', 'a/f']:
        orm.Group.objects.get_or_create(label, type_string=orm.GroupTypeString.UPFGROUP_TYPE.value)
    group_path = GroupPath()
    assert sorted([c.path for c in group_path.walk()]) == ['a', 'a/b', 'a/c', 'a/c/d', 'a/c/e', 'a/c/e/g']
    group_path = GroupPath(type_string=orm.GroupTypeString.UPFGROUP_TYPE.value)
    assert sorted([c.path for c in group_path.walk()]) == ['a', 'a/c', 'a/c/e', 'a/f']
    assert GroupPath('a/b/c') != GroupPath('a/b/c', type_string=orm.GroupTypeString.UPFGROUP_TYPE.value)


def test_attr(clear_database_before_test):
    """Test ``GroupAttr``."""
    for label in ['a', 'a/b', 'a/c/d', 'a/c/e/g', 'a/f', 'bad space', 'bad@char', '_badstart']:
        orm.Group.objects.get_or_create(label)
    group_path = GroupPath()
    assert isinstance(group_path.browse.a.c.d, GroupAttr)
    assert isinstance(group_path.browse.a.c.d(), GroupPath)
    assert group_path.browse.a.c.d().path == 'a/c/d'
    assert not set(group_path.browse.__dir__()).intersection(['bad space', 'bad@char', '_badstart'])
    with pytest.raises(AttributeError):
        group_path.browse.a.c.x  # pylint: disable=pointless-statement
