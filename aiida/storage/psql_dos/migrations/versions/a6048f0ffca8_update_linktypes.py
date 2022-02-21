# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Updating link types - This is a copy of the Django migration script

Revision ID: a6048f0ffca8
Revises:
Create Date: 2017-10-17 10:51:23.327195

"""
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'a6048f0ffca8'
down_revision = '70c7d732f1b2'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # I am first migrating the wrongly declared returnlinks out of
    # the InlineCalculations.
    # This bug is reported #628 https://github.com/aiidateam/aiida-core/issues/628
    # There is an explicit check in the code of the inline calculation
    # ensuring that the calculation returns UNSTORED nodes.
    # Therefore, no cycle can be created with that migration!
    #
    # this command:
    # 1) selects all links that
    #   - joins an InlineCalculation (or subclass) as input
    #   - joins a Data (or subclass) as output
    #   - is marked as a returnlink.
    # 2) set for these links the type to 'createlink'
    stmt1 = text(
        """
        UPDATE db_dblink set type='createlink' WHERE db_dblink.id IN (
            SELECT db_dblink_1.id
            FROM db_dbnode AS db_dbnode_1
                JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id
            WHERE db_dbnode_1.type LIKE 'calculation.inline.%'
                AND db_dbnode_2.type LIKE 'data.%'
                AND db_dblink_1.type = 'returnlink'
        )
    """
    )
    conn.execute(stmt1)
    # Now I am updating the link-types that are null because of either an export and subsequent import
    # https://github.com/aiidateam/aiida-core/issues/685
    # or because the link types don't exist because the links were added before the introduction of link types.
    # This is reported here: https://github.com/aiidateam/aiida-core/issues/687
    #
    # The following sql statement:
    # 1) selects all links that
    #   - joins Data (or subclass) or Code as input
    #   - joins Calculation (or subclass) as output. This includes WorkCalculation, InlineCalcuation, JobCalculations...
    #   - has no type (null)
    # 2) set for these links the type to 'inputlink'
    stmt2 = text(
        """
         UPDATE db_dblink set type='inputlink' where id in (
            SELECT db_dblink_1.id
            FROM db_dbnode AS db_dbnode_1
                JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id
            WHERE ( db_dbnode_1.type LIKE 'data.%' or db_dbnode_1.type = 'code.Code.' )
                AND db_dbnode_2.type LIKE 'calculation.%'
                AND ( db_dblink_1.type = null OR db_dblink_1.type = '')
        );
    """
    )
    conn.execute(stmt2)
    #
    # The following sql statement:
    # 1) selects all links that
    #   - join JobCalculation (or subclass) or InlineCalculation as input
    #   - joins Data (or subclass) as output.
    #   - has no type (null)
    # 2) set for these links the type to 'createlink'
    stmt3 = text(
        """
         UPDATE db_dblink set type='createlink' where id in (
            SELECT db_dblink_1.id
            FROM db_dbnode AS db_dbnode_1
                JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id
            WHERE db_dbnode_2.type LIKE 'data.%'
                AND (
                    db_dbnode_1.type LIKE 'calculation.job.%'
                    OR
                    db_dbnode_1.type = 'calculation.inline.InlineCalculation.'
                )
                AND ( db_dblink_1.type = null OR db_dblink_1.type = '')
        )
    """
    )
    conn.execute(stmt3)
    # The following sql statement:
    # 1) selects all links that
    #   - join WorkCalculation as input. No subclassing was introduced so far, so only one type string is checked for.
    #   - join Data (or subclass) as output.
    #   - has no type (null)
    # 2) set for these links the type to 'returnlink'
    stmt4 = text(
        """
         UPDATE db_dblink set type='returnlink' where id in (
            SELECT db_dblink_1.id
            FROM db_dbnode AS db_dbnode_1
                JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id
            WHERE db_dbnode_2.type LIKE 'data.%'
                AND db_dbnode_1.type = 'calculation.work.WorkCalculation.'
                AND ( db_dblink_1.type = null OR db_dblink_1.type = '')
        )
    """
    )
    conn.execute(stmt4)
    # Now I update links that are CALLS:
    # The following sql statement:
    # 1) selects all links that
    #   - join WorkCalculation as input. No subclassing was introduced so far, so only one type string is checked for.
    #   - join Calculation (or subclass) as output. Includes JobCalculation and WorkCalculations and all subclasses.
    #   - has no type (null)
    # 2) set for these links the type to 'calllink'
    stmt5 = text(
        """
         UPDATE db_dblink set type='calllink' where id in (
            SELECT db_dblink_1.id
            FROM db_dbnode AS db_dbnode_1
                JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id
            WHERE db_dbnode_1.type = 'calculation.work.WorkCalculation.'
                AND db_dbnode_2.type LIKE 'calculation.%'
                AND ( db_dblink_1.type = null  OR db_dblink_1.type = '')
        )
    """
    )
    conn.execute(stmt5)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of a6048f0ffca8.')
