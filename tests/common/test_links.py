###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the links utilities."""

import pytest

from aiida.common.links import validate_link_label


def test_validate_link_label():
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
        with pytest.raises(ValueError):
            validate_link_label(link_label)
