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

REVISION = '1.0.16'
DOWN_REVISION = '1.0.15'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0015_invalidating_node_hash'),
    ]

    operations = [
        # The Code class used to be just a sub class of Node but was changed to act like a Data node.
        # To make everything fully consistent, its type string should therefore also start with `data.`
        migrations.RunSQL(
            sql="""UPDATE db_dbnode SET type = 'data.code.Code.' WHERE type = 'code.Code.';""",
            reverse_sql="""UPDATE db_dbnode SET type = 'code.Code.' WHERE type = 'data.code.Code.';"""),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
