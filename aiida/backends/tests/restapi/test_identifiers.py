# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `aiida.restapi.common.identifiers` module."""
from aiida.backends.testbase import AiidaTestCase
from aiida.restapi.common.identifiers import get_full_type_filters, FULL_TYPE_CONCATENATOR, LIKE_OPERATOR_CHARACTER


class TestIdentifiers(AiidaTestCase):
    """Tests for the :py:mod:`~aiida.restapi.common.identifiers` module."""

    def test_get_full_type_filters(self):
        """Test the `get_full_type_filters` function."""

        with self.assertRaises(TypeError):
            get_full_type_filters(10)

        with self.assertRaises(ValueError):
            get_full_type_filters('string_without_full_type_concatenator')

        with self.assertRaises(ValueError):
            get_full_type_filters(
                'too_many_{like}{like}{concat}process_type'.format(
                    like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR
                )
            )

        with self.assertRaises(ValueError):
            get_full_type_filters(
                'node_type{concat}too_many_{like}{like}'.format(
                    like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR
                )
            )

        with self.assertRaises(ValueError):
            get_full_type_filters(
                'not_at_{like}_the_end{concat}process_type'.format(
                    like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR
                )
            )

        with self.assertRaises(ValueError):
            get_full_type_filters(
                'node_type{concat}not_at_{like}_the_end'.format(
                    like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR
                )
            )

        # Equals on both
        filters = get_full_type_filters('node_type{concat}process_type'.format(concat=FULL_TYPE_CONCATENATOR))
        self.assertEqual(filters['node_type'], 'node\\_type')
        self.assertEqual(filters['process_type'], 'process\\_type')

        # Like on `node_type`
        filters = get_full_type_filters(
            'node_type{like}{concat}process_type'.format(like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR)
        )
        self.assertEqual(filters['node_type'], {'like': 'node\\_type%'})
        self.assertEqual(filters['process_type'], 'process\\_type')

        # Like on `process_type`
        filters = get_full_type_filters(
            'node_type{concat}process_type{like}'.format(like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR)
        )
        self.assertEqual(filters['node_type'], 'node\\_type')
        self.assertEqual(filters['process_type'], {'like': 'process\\_type%'})

        # Like on both
        filters = get_full_type_filters(
            'node_type{like}{concat}process_type{like}'.format(
                like=LIKE_OPERATOR_CHARACTER, concat=FULL_TYPE_CONCATENATOR
            )
        )
        self.assertEqual(filters['node_type'], {'like': 'node\\_type%'})
        self.assertEqual(filters['process_type'], {'like': 'process\\_type%'})
