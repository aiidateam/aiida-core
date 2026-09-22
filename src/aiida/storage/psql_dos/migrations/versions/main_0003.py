###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Prepare the storage schema for AiiDA v3.0.0.

Rename the ``core.ssh_async`` transport plugin to ``core.ssh``. The legacy paramiko-based
``core.ssh`` transport plugin was removed in v3.0, and the asynchronous plugin (formerly
``core.ssh_async``) took over its entry point name. Consequently:

* computers configured with ``core.ssh_async`` have their ``transport_type`` rewritten to
  ``core.ssh``, and keep working unchanged;
* computers configured with the legacy ``core.ssh`` keep their ``transport_type`` as is, and are now
  served by the asynchronous plugin. That plugin has none of the connection parameters the legacy
  one stored in ``db_dbauthinfo.auth_params`` (username, port, key_filename, proxy_jump, ...), so
  they are written out as an OpenSSH client configuration entry and replaced by the alias of that
  entry. See :mod:`~aiida.storage.migrations.legacy_ssh`.

Note that neither step has an inverse: once both kinds of computers share the ``core.ssh`` transport
type they can no longer be told apart, and the parameters that were converted are gone from the
database. The downgrade therefore only restores the schema revision.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

from alembic import op

from aiida.storage.migrations.legacy_ssh import migrate_ssh_transports

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    migrate_ssh_transports(op.get_bind())


def downgrade():
    """Migrations for the downgrade."""
