import json

import pytest

from aiida.storage.sqlite_zip.utils import _contains, _json_contains


class TestCustomFunction:
    @pytest.mark.parametrize(
        'lhs,rhs,is_match',
        (
            # contains different types of element
            ([1, '2', None], [1], True),
            ([1, '2', None], ['2'], True),
            ([1, '2', None], [None], True),
            # contains multiple elements of various types
            ([1, '2', None], [1, None], True),
            # contains non-exist elements
            ([1, '2', None], [114514], False),
            # contains empty set
            ([1, '2', None], [], True),
            ([], [], True),
            # nested arrays
            ([[1, 0], [0, 2]], [[1, 0]], True),
            ([[2, 3], [0, 1], []], [[1, 0]], True),
            ([[2, 3], [1]], [[4]], False),
            ([[1, 0], [0, 2]], [[3]], False),
            ([[1, 0], [0, 2]], [3], False),
            ([[1, 0], [0, 2]], [[2]], True),
            ([[1, 0], [0, 2]], [2], False),
            ([[1, 0], [0, 2], 3], [[3]], False),
            ([[1, 0], [0, 2], 3], [3], True),
            # contains different types of values
            (
                {
                    'k1': 1,
                    'k2': '2',
                    'k3': None,
                },
                {'k1': 1},
                True,
            ),
            (
                {
                    'k1': 1,
                    'k2': '2',
                    'k3': None,
                },
                {'k1': 1, 'k2': '2'},
                True,
            ),
            (
                {
                    'k1': 1,
                    'k2': '2',
                    'k3': None,
                },
                {'k3': None},
                True,
            ),
            # contains empty set
            (
                {
                    'k1': 1,
                    'k2': '2',
                    'k3': None,
                },
                {},
                True,
            ),
            # nested dicts
            (
                {'k1': {'k2': {'kx': 1, 'k3': 'secret'}, 'kxx': None}, 'kxxx': 'vxxx'},
                {'k1': {'k2': {'k3': 'secret'}}},
                True,
            ),
            (
                {
                    'k1': [
                        0,
                        1,
                        {
                            'k2': [
                                '0',
                                {
                                    'kkk': 'vvv',
                                    'k3': 'secret',
                                },
                                '2',
                            ]
                        },
                        3,
                    ],
                    'kkk': 'vvv',
                },
                {
                    'k1': [
                        {
                            'k2': [
                                {
                                    'k3': 'secret',
                                }
                            ]
                        }
                    ]
                },
                True,
            ),
            # doesn't contain non-exist entries
            (
                {
                    'k1': 1,
                    'k2': '2',
                    'k3': None,
                },
                {'k1': 1, 'k': 'v'},
                False,
            ),
        ),
        ids=json.dumps,
    )
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_json_contains(self, lhs, rhs, is_match):
        """Test QueryBuilder filter `contains` for JSON array fields"""
        lhs_json = json.dumps(lhs)
        rhs_json = json.dumps(rhs)
        assert is_match == _contains(lhs, rhs)
        assert is_match == _json_contains(lhs, rhs)
        assert is_match == _json_contains(lhs_json, rhs)
        assert is_match == _json_contains(lhs, rhs_json)
        assert is_match == _json_contains(lhs_json, rhs_json)
