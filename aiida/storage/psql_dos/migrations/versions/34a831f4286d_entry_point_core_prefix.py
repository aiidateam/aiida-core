# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,line-too-long
"""Update node types after `core.` prefix was added to entry point names.

Revision ID: 34a831f4286d
Revises: 535039300e4a
Create Date: 2021-08-11 18:25:48.706298

"""
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '34a831f4286d'
down_revision = '535039300e4a'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()
    statement = text(
        """
        UPDATE db_dbnode SET node_type = 'data.core.array.ArrayData.' WHERE node_type = 'data.array.ArrayData.';
        UPDATE db_dbnode SET node_type = 'data.core.array.bands.BandsData.' WHERE node_type = 'data.array.bands.BandsData.';
        UPDATE db_dbnode SET node_type = 'data.core.array.kpoints.KpointsData.' WHERE node_type = 'data.array.kpoints.KpointsData.';
        UPDATE db_dbnode SET node_type = 'data.core.array.projection.ProjectionData.' WHERE node_type = 'data.array.projection.ProjectionData.';
        UPDATE db_dbnode SET node_type = 'data.core.array.trajectory.TrajectoryData.' WHERE node_type = 'data.array.trajectory.TrajectoryData.';
        UPDATE db_dbnode SET node_type = 'data.core.array.xy.XyData.' WHERE node_type = 'data.array.xy.XyData.';
        UPDATE db_dbnode SET node_type = 'data.core.base.BaseData.' WHERE node_type = 'data.base.BaseData.';
        UPDATE db_dbnode SET node_type = 'data.core.bool.Bool.' WHERE node_type = 'data.bool.Bool.';
        UPDATE db_dbnode SET node_type = 'data.core.cif.CifData.' WHERE node_type = 'data.cif.CifData.';
        UPDATE db_dbnode SET node_type = 'data.core.code.Code.' WHERE node_type = 'data.code.Code.';
        UPDATE db_dbnode SET node_type = 'data.core.dict.Dict.' WHERE node_type = 'data.dict.Dict.';
        UPDATE db_dbnode SET node_type = 'data.core.float.Float.' WHERE node_type = 'data.float.Float.';
        UPDATE db_dbnode SET node_type = 'data.core.folder.FolderData.' WHERE node_type = 'data.folder.FolderData.';
        UPDATE db_dbnode SET node_type = 'data.core.int.Int.' WHERE node_type = 'data.int.Int.';
        UPDATE db_dbnode SET node_type = 'data.core.list.List.' WHERE node_type = 'data.list.List.';
        UPDATE db_dbnode SET node_type = 'data.core.numeric.NumericData.' WHERE node_type = 'data.numeric.NumericData.';
        UPDATE db_dbnode SET node_type = 'data.core.orbital.OrbitalData.' WHERE node_type = 'data.orbital.OrbitalData.';
        UPDATE db_dbnode SET node_type = 'data.core.remote.RemoteData.' WHERE node_type = 'data.remote.RemoteData.';
        UPDATE db_dbnode SET node_type = 'data.core.remote.stash.RemoteStashData.' WHERE node_type = 'data.remote.stash.RemoteStashData.';
        UPDATE db_dbnode SET node_type = 'data.core.remote.stash.folder.RemoteStashFolderData.' WHERE node_type = 'data.remote.stash.folder.RemoteStashFolderData.';
        UPDATE db_dbnode SET node_type = 'data.core.singlefile.SinglefileData.' WHERE node_type = 'data.singlefile.SinglefileData.';
        UPDATE db_dbnode SET node_type = 'data.core.str.Str.' WHERE node_type = 'data.str.Str.';
        UPDATE db_dbnode SET node_type = 'data.core.structure.StructureData.' WHERE node_type = 'data.structure.StructureData.';
        UPDATE db_dbnode SET node_type = 'data.core.upf.UpfData.' WHERE node_type = 'data.upf.UpfData.';
        UPDATE db_dbcomputer SET scheduler_type = 'core.direct' WHERE scheduler_type = 'direct';
        UPDATE db_dbcomputer SET scheduler_type = 'core.lsf' WHERE scheduler_type = 'lsf';
        UPDATE db_dbcomputer SET scheduler_type = 'core.pbspro' WHERE scheduler_type = 'pbspro';
        UPDATE db_dbcomputer SET scheduler_type = 'core.sge' WHERE scheduler_type = 'sge';
        UPDATE db_dbcomputer SET scheduler_type = 'core.slurm' WHERE scheduler_type = 'slurm';
        UPDATE db_dbcomputer SET scheduler_type = 'core.torque' WHERE scheduler_type = 'torque';
        UPDATE db_dbcomputer SET transport_type = 'core.local' WHERE transport_type = 'local';
        UPDATE db_dbcomputer SET transport_type = 'core.ssh' WHERE transport_type = 'ssh';
        UPDATE db_dbnode SET process_type = 'aiida.calculations:core.arithmetic.add' WHERE process_type = 'aiida.calculations:arithmetic.add';
        UPDATE db_dbnode SET process_type = 'aiida.calculations:core.templatereplacer' WHERE process_type = 'aiida.calculations:templatereplacer';
        UPDATE db_dbnode SET process_type = 'aiida.workflows:core.arithmetic.add_multiply' WHERE process_type = 'aiida.workflows:arithmetic.add_multiply';
        UPDATE db_dbnode SET process_type = 'aiida.workflows:core.arithmetic.multiply_add' WHERE process_type = 'aiida.workflows:arithmetic.multiply_add';
        UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"parser_name"}', '"core.arithmetic.add"') WHERE attributes->>'parser_name' = 'arithmetic.add';
        UPDATE db_dbnode SET attributes = jsonb_set(attributes, '{"parser_name"}', '"core.templatereplacer.doubler"') WHERE attributes->>'parser_name' = 'templatereplacer.doubler';
        """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 34a831f4286d.')
