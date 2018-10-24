# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version


REVISION = '1.0.8'
DOWN_REVISION = '1.0.7'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0006_delete_dbpath'),
    ]

    operations = [
        # I am first migrating the wrongly declared returnlinks out of
        # the InlineCalculations.
        # This bug is reported #628 https://github.com/aiidateam/aiida_core/issues/628
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
        migrations.RunSQL("""
            UPDATE db_dblink set type='createlink' WHERE db_dblink.id IN (
                SELECT db_dblink_1.id 
                FROM db_dbnode AS db_dbnode_1
                    JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                    JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id
                WHERE db_dbnode_1.type LIKE 'calculation.inline.%'
                    AND db_dbnode_2.type LIKE 'data.%'
                    AND db_dblink_1.type = 'returnlink'
            );
        """),
        # Now I am updating the link-types that are null because of either an export and subsequent import
        # https://github.com/aiidateam/aiida_core/issues/685
        # or because the link types don't exist because the links were added before the introduction of link types.
        # This is reported here: https://github.com/aiidateam/aiida_core/issues/687
        #
        # The following sql statement:
        # 1) selects all links that
        #   - joins Data (or subclass) or Code as input
        #   - joins Calculation (or subclass) as output. This includes WorkCalculation, InlineCalcuation, JobCalculations...
        #   - has no type (null)
        # 2) set for these links the type to 'inputlink'
        migrations.RunSQL("""
             UPDATE db_dblink set type='inputlink' where id in (
                SELECT db_dblink_1.id
                FROM db_dbnode AS db_dbnode_1
                    JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                    JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id 
                WHERE ( db_dbnode_1.type LIKE 'data.%' or db_dbnode_1.type = 'code.Code.' )
                    AND db_dbnode_2.type LIKE 'calculation.%'
                    AND ( db_dblink_1.type = null OR db_dblink_1.type = '')
            );
        """),
        #
        # The following sql statement:
        # 1) selects all links that
        #   - join JobCalculation (or subclass) or InlineCalculation as input
        #   - joins Data (or subclass) as output.
        #   - has no type (null)
        # 2) set for these links the type to 'createlink'
        migrations.RunSQL("""
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
            );
        """),
        # The following sql statement:
        # 1) selects all links that
        #   - join WorkCalculation as input. No subclassing was introduced so far, so only one type string is checked for.
        #   - join Data (or subclass) as output.
        #   - has no type (null)
        # 2) set for these links the type to 'returnlink'
        migrations.RunSQL("""
             UPDATE db_dblink set type='returnlink' where id in (
                SELECT db_dblink_1.id
                FROM db_dbnode AS db_dbnode_1
                    JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                    JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id 
                WHERE db_dbnode_2.type LIKE 'data.%'
                    AND db_dbnode_1.type = 'calculation.work.WorkCalculation.'
                    AND ( db_dblink_1.type = null OR db_dblink_1.type = '')
            );
        """),
        # Now I update links that are CALLS:
        # The following sql statement:
        # 1) selects all links that
        #   - join WorkCalculation as input. No subclassing was introduced so far, so only one type string is checked for.
        #   - join Calculation (or subclass) as output. Includes JobCalculation and WorkCalculations and all subclasses.
        #   - has no type (null)
        # 2) set for these links the type to 'calllink'
        migrations.RunSQL("""
             UPDATE db_dblink set type='calllink' where id in (
                SELECT db_dblink_1.id
                FROM db_dbnode AS db_dbnode_1
                    JOIN db_dblink AS db_dblink_1 ON db_dblink_1.input_id = db_dbnode_1.id
                    JOIN db_dbnode AS db_dbnode_2 ON db_dblink_1.output_id = db_dbnode_2.id 
                WHERE db_dbnode_1.type = 'calculation.work.WorkCalculation.'
                    AND db_dbnode_2.type LIKE 'calculation.%'
                    AND ( db_dblink_1.type = null  OR db_dblink_1.type = '')
            );
        """),
        upgrade_schema_version(REVISION, DOWN_REVISION)

    ]
