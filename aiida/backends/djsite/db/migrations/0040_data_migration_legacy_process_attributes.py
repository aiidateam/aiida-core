# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Data migration for some legacy process attributes.

Attribute keys that are renamed:

  * `_sealed` -> `sealed`

Attribute keys that are removed entirely:

  * `_finished`
  * `_failed`
  * `_aborted`
  * `_do_abort`

Finally, after these first migrations, any remaining process nodes that still do not have a sealed attribute, have
it set to `True`. Excluding the nodes that have a `process_state` attribute of one of the active states: `created`;
`running`; or `waiting`, because those are valid active processes that are not yet sealed.

"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.40'
DOWN_REVISION = '1.0.39'


class Migration(migrations.Migration):
    """Data migration for legacy process attributes."""

    dependencies = [
        ('db', '0039_reset_hash'),
    ]

    operations = [
        migrations.RunSQL(
            sql=r"""
                UPDATE db_dbnode
                SET attributes = jsonb_set(attributes, '{"sealed"}', attributes->'_sealed')
                WHERE attributes ? '_sealed' AND node_type LIKE 'process.%';
                -- Copy `_sealed` -> `sealed`

                UPDATE db_dbnode SET attributes = attributes - '_sealed'
                WHERE attributes ? '_sealed' AND node_type LIKE 'process.%';
                -- Delete `_sealed`

                UPDATE db_dbnode SET attributes = attributes - '_finished'
                WHERE attributes ? '_finished' AND node_type LIKE 'process.%';
                -- Delete `_finished`

                UPDATE db_dbnode SET attributes = attributes - '_failed'
                WHERE attributes ? '_failed' AND node_type LIKE 'process.%';
                -- Delete `_failed`

                UPDATE db_dbnode SET attributes = attributes - '_aborted'
                WHERE attributes ? '_aborted' AND node_type LIKE 'process.%';
                -- Delete `_aborted`

                UPDATE db_dbnode SET attributes = attributes - '_do_abort'
                WHERE attributes ? '_do_abort' AND node_type LIKE 'process.%';
                -- Delete `_do_abort`

                UPDATE db_dbnode
                SET attributes = jsonb_set(attributes, '{"sealed"}', to_jsonb(True))
                WHERE
                    node_type LIKE 'process.%' AND
                    NOT (attributes ? 'sealed') AND
                    attributes->>'process_state' NOT IN ('created', 'running', 'waiting');
                -- Set `sealed=True` for process nodes that do not yet have a `sealed` attribute AND are not in an active state
                """,
            reverse_sql=''
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
