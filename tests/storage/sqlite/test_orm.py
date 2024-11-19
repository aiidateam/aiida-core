###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the ORM implementation."""

import json

import pytest
from aiida.orm import Dict, QueryBuilder
from aiida.storage.sqlite_temp import SqliteTempBackend


@pytest.mark.parametrize(
    'filters,matches',
    (
        # type match
        ({'attributes.text': {'of_type': 'string'}}, 1),
        ({'attributes.integer': {'of_type': 'number'}}, 1),
        ({'attributes.float': {'of_type': 'number'}}, 1),
        ({'attributes.true': {'of_type': 'boolean'}}, 1),
        ({'attributes.false': {'of_type': 'boolean'}}, 1),
        ({'attributes.null': {'of_type': 'null'}}, 3),
        ({'attributes.list': {'of_type': 'array'}}, 1),
        ({'attributes.dict': {'of_type': 'object'}}, 1),
        # equality match
        ({'attributes.text': {'==': 'abcXYZ'}}, 1),
        ({'attributes.integer': {'==': 1}}, 1),
        ({'attributes.float': {'==': 1.1}}, 1),
        ({'attributes.true': {'==': True}}, 1),
        ({'attributes.false': {'==': False}}, 1),
        ({'attributes.list': {'==': [1, 2]}}, 1),
        ({'attributes.list2': {'==': ['a', 'b']}}, 1),
        ({'attributes.dict': {'==': {'key-1': 1, 'key-none': None}}}, 1),
        # equality non-match
        ({'attributes.text': {'==': 'lmn'}}, 0),
        ({'attributes.integer': {'==': 2}}, 0),
        ({'attributes.float': {'==': 2.2}}, 0),
        ({'attributes.true': {'==': False}}, 0),
        ({'attributes.false': {'==': True}}, 0),
        ({'attributes.list': {'==': [1, 3]}}, 0),
        # text regexes
        ({'attributes.text': {'like': 'abcXYZ'}}, 1),
        ({'attributes.text': {'like': 'abcxyz'}}, 0),
        ({'attributes.text': {'ilike': 'abcxyz'}}, 1),
        ({'attributes.text': {'like': 'abc%'}}, 1),
        ({'attributes.text': {'like': 'abc_YZ'}}, 1),
        (
            {
                'attributes.text2': {
                    'like': 'abc\\_XYZ'  # Literal match
                }
            },
            1,
        ),
        ({'attributes.text2': {'like': 'abc_XYZ'}}, 2),
        # integer comparisons
        ({'attributes.float': {'<': 1}}, 0),
        ({'attributes.float': {'<': 2}}, 1),
        ({'attributes.float': {'>': 2}}, 0),
        ({'attributes.float': {'>': 0}}, 1),
        ({'attributes.integer': {'<': 1}}, 0),
        ({'attributes.integer': {'<': 2}}, 1),
        ({'attributes.integer': {'>': 2}}, 0),
        ({'attributes.integer': {'>': 0}}, 1),
        # float comparisons
        ({'attributes.float': {'<': 0.99}}, 0),
        ({'attributes.float': {'<': 2.01}}, 1),
        ({'attributes.float': {'>': 2.01}}, 0),
        ({'attributes.float': {'>': 0.01}}, 1),
        ({'attributes.integer': {'<': 0.99}}, 0),
        ({'attributes.integer': {'<': 2.01}}, 1),
        ({'attributes.integer': {'>': 2.01}}, 0),
        ({'attributes.integer': {'>': 0.01}}, 1),
        # array operators
        ({'attributes.list': {'of_length': 0}}, 0),
        ({'attributes.list': {'of_length': 2}}, 1),
        ({'attributes.list': {'longer': 3}}, 0),
        ({'attributes.list': {'longer': 1}}, 1),
        ({'attributes.list': {'shorter': 1}}, 0),
        ({'attributes.list': {'shorter': 3}}, 1),
        # in operator
        ({'attributes.text': {'in': ['x', 'y', 'z']}}, 0),
        ({'attributes.text': {'in': ['x', 'y', 'abcXYZ']}}, 1),
        ({'attributes.integer': {'in': [5, 6, 7]}}, 0),
        ({'attributes.integer': {'in': [1, 2, 3]}}, 1),
        # object operators
        ({'attributes.dict': {'has_key': 'non-exist'}}, 0),
        ({'attributes.dict': {'!has_key': 'non-exist'}}, 3),
        ({'attributes.dict': {'has_key': 'key-1'}}, 1),
        ({'attributes.dict': {'has_key': 'key-none'}}, 1),
        ({'attributes.dict': {'!has_key': 'key-none'}}, 2),
    ),
    ids=json.dumps,
)
def test_qb_json_filters(filters, matches):
    """Test QueryBuilder filtering for JSON fields."""
    profile = SqliteTempBackend.create_profile(debug=False)
    backend = SqliteTempBackend(profile)
    Dict(
        {
            'text': 'abcXYZ',
            'text2': 'abc_XYZ',
            'integer': 1,
            'float': 1.1,
            'true': True,
            'false': False,
            'null': None,
            'list': [1, 2],
            'list2': ['a', 'b'],
            'dict': {
                'key-1': 1,
                'key-none': None,
            },
        },
        backend=backend,
    ).store()
    Dict({'text2': 'abcxXYZ'}, backend=backend).store()

    # a false dict, added to test `has_key`'s behavior when key is not of json type
    Dict({'dict': 0xFA15ED1C7}, backend=backend).store()

    qbuilder = QueryBuilder(backend=backend)
    qbuilder.append(Dict, filters=filters)
    assert qbuilder.count() == matches


class TestJsonFilters:
    @pytest.mark.parametrize(
        'data,filters,is_match',
        (
            # contains different types of element
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [1]}}, True),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': ['2']}}, True),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [None]}}, True),
            # contains multiple elements of various types
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [1, None]}}, True),
            # contains non-exist elements
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': [114514]}}, False),
            # contains empty set
            ({'arr': [1, '2', None]}, {'attributes.arr': {'contains': []}}, True),
            ({'arr': []}, {'attributes.arr': {'contains': []}}, True),
            # nested arrays
            ({'arr': [[1, 0], [0, 2]]}, {'attributes.arr': {'contains': [[1, 0]]}}, True),
            ({'arr': [[2, 3], [0, 1], []]}, {'attributes.arr': {'contains': [[1, 0]]}}, True),  # order doesn't matter
            ({'arr': [[2, 3], [1]]}, {'attributes.arr': {'contains': [[4]]}}, False),
            # TODO: the test below is supposed to pass but currently doesn't
            # ({'arr': [[2, 3], [1]]}, {'attributes.arr': {'contains': [[2]]}}, False),
            # negations
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': [1]}}, False),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': []}}, False),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': [114514]}}, True),
            ({'arr': [1, '2', None]}, {'attributes.arr': {'!contains': [1, 114514]}}, True),
            # TODO: these pass, but why? are these behaviors expected?
            # non-exist `attr_key`s
            ({'foo': []}, {'attributes.arr': {'contains': []}}, False),
            ({'foo': []}, {'attributes.arr': {'!contains': []}}, False),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    @pytest.mark.requires_psql
    def test_json_filters_contains_arrays(self, data, filters, is_match):
        """Test QueryBuilder filter `contains` for JSON array fields"""
        profile = SqliteTempBackend.create_profile(debug=False)
        backend = SqliteTempBackend(profile)
        Dict(data, backend=backend).store()
        qb = QueryBuilder(backend=backend).append(Dict, filters=filters)
        assert qb.count() in {0, 1}
        found = qb.count() == 1
        assert found == is_match

    @pytest.mark.parametrize(
        'data,filters,is_match',
        (
            # contains different types of values
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k1': 1}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k1': 1, 'k2': '2'}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k3': None}}},
                True,
            ),
            # contains empty set
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {}}},
                True,
            ),
            # doesn't contain non-exist entries
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'contains': {'k1': 1, 'k': 'v'}}},
                False,
            ),
            # negations
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'!contains': {'k1': 1}}},
                False,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'!contains': {'k1': 1, 'k': 'v'}}},
                True,
            ),
            (
                {
                    'dict': {
                        'k1': 1,
                        'k2': '2',
                        'k3': None,
                    }
                },
                {'attributes.dict': {'!contains': {}}},
                False,
            ),
            # TODO: these pass, but why? are these behaviors expected?
            # non-exist `attr_key`s
            ({'map': {}}, {'attributes.dict': {'contains': {}}}, False),
            ({'map': {}}, {'attributes.dict': {'!contains': {}}}, False),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    @pytest.mark.requires_psql
    def test_json_filters_contains_object(self, data, filters, is_match):
        """Test QueryBuilder filter `contains` for JSON object fields"""
        profile = SqliteTempBackend.create_profile(debug=False)
        backend = SqliteTempBackend(profile)
        Dict(data, backend=backend).store()
        qb = QueryBuilder(backend=backend).append(Dict, filters=filters)
        assert qb.count() in {0, 1}
        found = qb.count() == 1
        assert found == is_match


@pytest.mark.parametrize(
    'filters,matches',
    (
        ({'label': {'like': 'abc_XYZ'}}, 2),
        ({'label': {'like': 'abc\\_XYZ'}}, 1),
        ({'label': {'like': 'abcxXYZ'}}, 1),
        ({'label': {'like': 'abc%XYZ'}}, 2),
    ),
    ids=json.dumps,
)
def test_qb_column_filters(filters, matches):
    """Test querying directly those stored in the columns"""
    profile = SqliteTempBackend.create_profile(debug=False)
    backend = SqliteTempBackend(profile)
    dict1 = Dict(
        {
            'text2': 'abc_XYZ',
        },
        backend=backend,
    ).store()
    dict2 = Dict({'text2': 'abcxXYZ'}, backend=backend).store()
    dict1.label = 'abc_XYZ'
    dict2.label = 'abcxXYZ'
    qbuilder = QueryBuilder(backend=backend)
    qbuilder.append(Dict, filters=filters)
    assert qbuilder.count() == matches


@pytest.mark.parametrize(
    'key,cast_type',
    (
        ('text', 't'),
        ('integer', 'i'),
        ('float', 'f'),
    ),
)
def test_qb_json_order_by(key, cast_type):
    """Test QueryBuilder ordering by JSON field keys."""
    profile = SqliteTempBackend.create_profile(debug=False)
    backend = SqliteTempBackend(profile)
    dict1 = Dict(
        {
            'text': 'b',
            'integer': 2,
            'float': 2.2,
        },
        backend=backend,
    ).store()
    dict2 = Dict(
        {
            'text': 'a',
            'integer': 1,
            'float': 1.1,
        },
        backend=backend,
    ).store()
    dict3 = Dict(
        {
            'text': 'c',
            'integer': 3,
            'float': 3.3,
        },
        backend=backend,
    ).store()
    qbuilder = QueryBuilder(backend=backend)
    qbuilder.append(Dict, tag='dict', project=['id']).order_by(
        {'dict': {f'attributes.{key}': {'order': 'asc', 'cast': cast_type}}}
    )
    assert qbuilder.all(flat=True) == [dict2.pk, dict1.pk, dict3.pk]
