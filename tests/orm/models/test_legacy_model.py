###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the deprecated ``Model`` compatibility wrapper."""

import pytest

from aiida import orm
from aiida.common.warnings import AiidaDeprecationWarning


@pytest.mark.presto
@pytest.mark.parametrize(
    ('orm_class', 'payload'),
    (
        (orm.User, {'email': 'legacy@aiida.net'}),
        (orm.Int, {'value': 5}),
        (orm.Dict, {'value': {'answer': 42}}),
        (orm.Int, {'user': 2, 'computer': 3, 'value': 5}),
    ),
)
def test_legacy_model_is_available_for_validation(orm_class, payload):
    """The deprecated ``Model`` wrapper should remain available for validation."""
    with pytest.warns(AiidaDeprecationWarning, match=r'\.Model` is deprecated'):
        model_class = orm_class.Model

    model = model_class(**payload)

    assert isinstance(model, model_class)


@pytest.mark.presto
@pytest.mark.parametrize(
    ('orm_class', 'payload', 'expected_model_name'),
    (
        (orm.User, {'email': 'legacy@aiida.net'}, 'WriteModel'),
        (orm.Int, {'user': 2, 'computer': 3, 'value': 5}, 'WriteModel'),
    ),
)
def test_legacy_model_cannot_be_used_with_from_model(orm_class, payload, expected_model_name):
    """The deprecated ``Model`` wrapper should fail loudly when passed to ``from_model``."""
    with pytest.warns(AiidaDeprecationWarning, match=r'\.Model` is deprecated'):
        model_class = orm_class.Model

    model = model_class(**payload)

    with pytest.raises(ValueError, match=expected_model_name):
        orm_class.from_model(model)
