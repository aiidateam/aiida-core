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

from aiida.common.links import LinkType, validate_link_label


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


def test_backend_bulk_insert_rejects_contains(backend):
    """Low-level `bulk_insert` of a `contains` link must never reach `db_dblink`."""
    from aiida import orm
    from aiida.common.exceptions import IntegrityError
    from aiida.orm.entities import EntityTypes

    source = orm.Data().store()
    target = orm.Data().store()
    with pytest.raises(IntegrityError, match='non-provenance'):
        backend.bulk_insert(
            EntityTypes.LINK,
            [
                {
                    'input_id': source.pk,
                    'output_id': target.pk,
                    'type': LinkType.CONTAINS.value,
                    'label': 'child',
                }
            ],
        )
