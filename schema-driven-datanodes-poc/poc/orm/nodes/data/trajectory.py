###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Concrete data-node class for trajectory-like payloads."""

from poc.orm.nodes.data.schema import FieldSpec, SchemaSpec
from poc.orm.nodes.data.data import Data


class TrajectoryData(Data):
    """Concrete stored data-node reconstructed from the persisted schema."""

    schema_name = 'TrajectoryMetadata'
    schema_spec = SchemaSpec(
        name=schema_name,
        fields=(
            FieldSpec('label', 0, validator_name='non_empty', description='Human-readable label'),
            FieldSpec('nsteps', 1, validator_name='positive_int', description='Number of MD steps'),
            FieldSpec('code', 0, required=False, default_str='cp2k', description='Code label'),
            FieldSpec('tags', 4, required=False, description='Free-form tags'),
        ),
    )
