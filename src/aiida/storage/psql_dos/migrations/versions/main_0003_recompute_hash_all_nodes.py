###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Drop the hashes for all ``Node`` instances.

The caching implementation was altered significantly recently. Most
notably the following changes were committed:

* Remove core and plugin information from hash calculation [4c60bbef852eef55a06b48b813d3fbcc8fb5a43f]
* `NodeCaching._get_objects_to_hash` return type to `dict` [c9c7c4bd8e1cd306271b5cf267095d3cbd8aafe2]
* Include the node's class in objects to hash [68ce111610c40e3d9146e128c0a698fc60b6e5e5]

This means that all existing hashes are now incompatible.
A migration is added to remove all hashes such that they can be recomputed.

Revision ID: main_0003
Revises: main_0002
Create Date: 2024-04-16

"""

from alembic import op

from aiida.storage.psql_dos.migrations.utils.integrity import drop_hashes

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    drop_hashes(op.get_bind(), hash_extra_key='_aiida_hash')


def downgrade():
    """Migrations for the downgrade."""
    drop_hashes(op.get_bind(), hash_extra_key='_aiida_hash')
