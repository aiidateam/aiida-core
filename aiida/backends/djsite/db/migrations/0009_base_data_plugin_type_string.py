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


REVISION = '1.0.9'
DOWN_REVISION = '1.0.8'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0008_code_hidden_to_extra'),
    ]

    operations = [
        # The base Data types Bool, Float, Int and Str have been moved in the source code, which means that their
        # module path changes, which determines the plugin type string which is stored in the databse.
        # The type string now will have a type string prefix that is unique to each sub type.
        migrations.RunSQL("""
            UPDATE db_dbnode SET type = 'data.bool.Bool.' WHERE type = 'data.base.Bool.';
            UPDATE db_dbnode SET type = 'data.float.Float.' WHERE type = 'data.base.Float.';
            UPDATE db_dbnode SET type = 'data.int.Int.' WHERE type = 'data.base.Int.';
            UPDATE db_dbnode SET type = 'data.str.Str.' WHERE type = 'data.base.Str.';
            UPDATE db_dbnode SET type = 'data.list.List.' WHERE type = 'data.base.List.';
        """),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
