###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for entity fields"""

import pytest
from aiida import orm
from aiida.orm.fields import add_field
from importlib_metadata import entry_points

EPS = entry_points()


@pytest.mark.parametrize(
    'entity_cls',
    (orm.AuthInfo, orm.Comment, orm.Computer, orm.Group, orm.Log, orm.User),
)
def test_all_entity_fields(entity_cls, data_regression):
    data_regression.check(
        {key: repr(value) for key, value in entity_cls.fields._dict.items()},
        basename=f'fields_{entity_cls.__name__}',
    )


@pytest.mark.parametrize(
    'group,name',
    (
        (group, name)
        for group in (
            'aiida.node',
            'aiida.data',
        )
        for name in EPS.select(group=group).names
    ),
)
def test_all_node_fields(group, name, data_regression):
    """Test that all the node fields are correctly registered."""
    node_cls = next(iter(tuple(EPS.select(group=group, name=name)))).load()
    data_regression.check(
        {key: repr(value) for key, value in node_cls.fields._dict.items()},
        basename=f'fields_{group}.{name}.{node_cls.__name__}',
    )


def test_add_field():
    """Test the `add_field` API."""

    class NewNode(orm.Data):
        __qb_fields__ = (
            add_field(
                'key1',
                dtype=str,
                is_subscriptable=False,
            ),
        )

    node = NewNode()

    assert 'key1' in node.fields
    assert node.fields.key1.dtype is str
    assert isinstance(node.fields.key1, orm.fields.QbStrField)
    assert node.fields.key1.backend_key == 'attributes.key1'
    assert not node.fields.key1.is_subscriptable


@pytest.mark.parametrize('key', ('|', 'some.field', '1key'))
def test_invalid_field_keys(key):
    """Test for invalid field keys."""
    with pytest.raises(ValueError):
        _ = add_field(key)


def test_disallowed_alias_for_db_field():
    """Test for disallowed alias argument for database fields."""
    with pytest.raises(ValueError):
        _ = add_field(
            'some_key',
            'alias_not_allowed_for_db_fields',
            is_attribute=False,
        )


@pytest.mark.usefixtures('aiida_profile_clean')
def test_query_new_class(monkeypatch):
    """Test that fields are correctly registered on a new data class,
    and can be used in a query.
    """
    from aiida import plugins

    def _dummy(*args, **kwargs):
        return True

    monkeypatch.setattr(
        plugins.entry_point,
        'is_registered_entry_point',
        _dummy,
    )

    class NewNode(orm.Data):
        __qb_fields__ = [
            add_field('some_label', dtype=str),
            add_field('some_value', dtype=int),
        ]

    node = NewNode()
    node.base.attributes.set_many({'some_label': 'A', 'some_value': 1})
    node.store()

    node = NewNode()
    node.base.attributes.set_many({'some_label': 'B', 'some_value': 2})
    node.store()

    node = NewNode()
    node.base.attributes.set_many({'some_label': 'C', 'some_value': 3})
    node.store()

    result = (
        orm.QueryBuilder()
        .append(
            NewNode,
            tag='node',
            project=[
                NewNode.fields.some_label,
                NewNode.fields.some_value,
            ],
            filters=NewNode.fields.some_value > 1,
        )
        .order_by({'node': NewNode.fields.ctime})
        .all()
    )
    assert result == [['B', 2], ['C', 3]]


def test_filter_operators():
    """Test that the operators are correctly registered."""
    pk = orm.Data.fields.pk
    filters = (pk == 1) & (pk != 2) & (pk > 3) & (pk >= 4) & (pk < 5) & (pk <= 6) & ~(pk == 7) & ~(pk < 8)
    # print(filters.as_dict())
    assert filters.as_dict() == {
        'and': [
            {'pk': {'==': 1}},
            {'pk': {'!==': 2}},
            {'pk': {'>': 3}},
            {'pk': {'>=': 4}},
            {'pk': {'<': 5}},
            {'pk': {'<=': 6}},
            {'pk': {'!==': 7}},
            {'pk': {'!<': 8}},
        ]
    }


def test_filter_comparators():
    """Test that the comparators are correctly registered."""
    field = orm.Data.fields.attributes['something']
    filters = (
        (field.in_(['a'])) & ~(field.in_(['b']))
        | (field.like('a%')) & (field.ilike('a%'))
        | ~((field.contains(['a'])) & (field.shorter(3)))
    )
    assert filters.as_dict() == {
        'or': [
            {
                'and': [
                    {'attributes.something': {'in': ['a']}},
                    {'attributes.something': {'!in': ['b']}},
                ]
            },
            {
                'and': [
                    {'attributes.something': {'like': 'a%'}},
                    {'attributes.something': {'ilike': 'a%'}},
                ]
            },
            {
                '!and': [
                    {'attributes.something': {'contains': ['a']}},
                    {'attributes.something': {'shorter': 3}},
                ]
            },
        ]
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_query_filters():
    """Test using fields to generate a query filter."""
    node = orm.Data().store()
    orm.Data().store()
    filters = (orm.Data.fields.pk == node.pk) & (orm.Data.fields.pk >= node.pk)
    result = (
        orm.QueryBuilder()
        .append(
            orm.Data,
            project=orm.Data.fields.pk,
            filters=filters,
        )
        .all()
    )
    assert result == [[node.pk]]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_query_subscriptable():
    """Test using subscriptable fields in a query."""
    node = orm.Dict(dict={'a': 1}).store()
    node.base.extras.set('b', 2)
    result = (
        orm.QueryBuilder()
        .append(
            orm.Dict,
            project=[
                orm.Dict.fields.dict['a'],
                orm.Dict.fields.extras['b'],
            ],
        )
        .all()
    )
    assert result == [[1, 2]]
