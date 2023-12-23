###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=missing-class-docstring,protected-access,unused-argument
"""Test for entity fields"""
import pytest
from aiida import orm
from aiida.orm import Data, Dict, QueryBuilder, fields
from importlib_metadata import entry_points

EPS = entry_points()


@pytest.mark.parametrize('entity_cls', (orm.AuthInfo, orm.Comment, orm.Computer, orm.Group, orm.Log, orm.User))
def test_all_entity_fields(entity_cls, data_regression):
    data_regression.check(
        {key: repr(value) for key, value in entity_cls.fields._dict.items()}, basename=f'fields_{entity_cls.__name__}'
    )


@pytest.mark.parametrize(
    'group,name', ((group, name) for group in ('aiida.node', 'aiida.data') for name in EPS.select(group=group).names)
)
def test_all_node_fields(group, name, data_regression):
    """Test that all the node fields are correctly registered."""
    node_cls = next(iter(tuple(EPS.select(group=group, name=name)))).load()
    data_regression.check(
        {key: repr(value) for key, value in node_cls.fields._dict.items()},
        basename=f'fields_{group}.{name}.{node_cls.__name__}',
    )


def test_query_new_class(clear_database_before_test, monkeypatch):
    """Test that fields are correctly registered on a new data class,
    and can be used in a query.
    """
    from aiida import plugins

    def _dummy(*args, **kwargs):
        return True

    monkeypatch.setattr(plugins.entry_point, 'is_registered_entry_point', _dummy)

    class NewNode(Data):
        __qb_fields__ = (
            fields.QbField('key1', 'attributes.key1'),
            fields.QbAttrField('key2'),
            fields.QbAttrField('key3'),
        )

    node = NewNode()
    node.set_attribute_many({'key1': 2, 'key2': 2, 'key3': 3})
    node.store()

    node = NewNode()
    node.set_attribute_many({'key1': 1, 'key2': 2, 'key3': 1})
    node.store()

    node = NewNode()
    node.set_attribute_many({'key1': 4, 'key2': 5, 'key3': 6})
    node.store()

    result = (
        QueryBuilder()
        .append(
            NewNode,
            tag='node',
            project=[NewNode.fields.key1, NewNode.fields.key2, NewNode.fields.key3],
            filters={NewNode.fields.key2: 2},
        )
        .order_by({'node': NewNode.fields.ctime})
        .all()
    )
    assert result == [[2, 2, 3], [1, 2, 1]]


def test_filter_operators():
    """Test that the operators are correctly registered."""
    field = Data.fields.pk
    filters = (field == 1) & (field != 2) & (field > 3) & (field >= 4) & (field < 5) & (field <= 6)
    # print(filters.as_dict())
    assert filters.as_dict() == {
        fields.QbField('pk', qb_field='id', dtype=int): {
            'and': [{'==': 1}, {'!=': 2}, {'>': 3}, {'>=': 4}, {'<': 5}, {'<=': 6}]
        }
    }


def test_filter_comparators():
    """Test that the comparators are correctly registered."""
    field = Data.fields.uuid
    filters = (field.in_(['a'])) & (field.not_in(['b'])) & (field.like('a%')) & (field.ilike('a%'))
    print(filters.as_dict())
    assert filters.as_dict() == {
        fields.QbField('uuid', qb_field='uuid', dtype=str): {
            'and': [{'in': {'a'}}, {'!in': {'b'}}, {'like': 'a%'}, {'ilike': 'a%'}]
        }
    }


def test_query_filters(clear_database_before_test):
    """Test using fields to generate a query filter."""
    node1 = Data().store()
    Data().store()
    filters = (Data.fields.pk == node1.pk) & (Data.fields.pk >= node1.pk)
    result = QueryBuilder().append(Data, project=Data.fields.pk, filters=filters).all()
    assert result == [[node1.pk]]


def test_query_subscriptable(clear_database_before_test):
    """Test using subscriptable fields in a query."""
    node = Dict(dict={'a': 1}).store()
    node.set_extra('b', 2)
    result = QueryBuilder().append(Dict, project=[Dict.fields.dict['a'], Dict.fields.extras['b']]).all()
    assert result == [[1, 2]]
