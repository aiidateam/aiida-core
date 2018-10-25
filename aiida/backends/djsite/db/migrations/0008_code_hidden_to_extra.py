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
        ('db', '0007_update_linktypes'),
    ]

    operations = [
        # The 'hidden' property of AbstractCode has been changed from an attribute to an extra
        # Therefore we find all nodes of type Code and if they have an attribute with the key 'hidden'
        # we move that value to the extra table
        #
        # First we copy the 'hidden' attributes from code.Code. nodes to the db_extra table
        migrations.RunSQL("""
            INSERT INTO db_dbextra (key, datatype, tval, fval, ival, bval, dval, dbnode_id) (
                SELECT db_dbattribute.key, db_dbattribute.datatype, db_dbattribute.tval, db_dbattribute.fval, db_dbattribute.ival, db_dbattribute.bval, db_dbattribute.dval, db_dbattribute.dbnode_id
                FROM db_dbattribute JOIN db_dbnode ON db_dbnode.id = db_dbattribute.dbnode_id
                WHERE db_dbattribute.key = 'hidden'
                    AND db_dbnode.type = 'code.Code.'
            );
        """),
        # Secondly, we delete the original entries from the DbAttribute table
        migrations.RunSQL("""
            DELETE FROM db_dbattribute
            WHERE id in (
                SELECT db_dbattribute.id
                FROM db_dbattribute 
                JOIN db_dbnode ON db_dbnode.id = db_dbattribute.dbnode_id
                WHERE db_dbattribute.key = 'hidden' AND db_dbnode.type = 'code.Code.'
            );
        """),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
