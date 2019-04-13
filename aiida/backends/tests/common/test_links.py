# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the links utilities."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import validate_link_label


class TestValidateLinkLabel(AiidaTestCase):
    """Tests for `validate_link_label` function."""

    def test_validate_link_label(self):
        """Test that illegal link labels will raise a `ValueError`."""

        illegal_link_labels = [
            '_leading_underscore',
            'trailing_underscore_',
            'non_numeric_%',
            'including.period',
            'disallowed👻unicodecharacters',
            'white space',
            'das-hes',
        ]

        for link_label in illegal_link_labels:
            with self.assertRaises(ValueError):
                validate_link_label(link_label)
