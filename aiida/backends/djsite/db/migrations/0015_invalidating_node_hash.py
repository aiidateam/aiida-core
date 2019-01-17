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
from aiida.cmdline.utils.echo import echo_warning

REVISION = '1.0.15'
DOWN_REVISION = '1.0.14'

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


def notify_user(apps, schema_editor):
    echo_warning("Invalidating all the hashes of all the nodes. Please run verdi rehash", bold=True)


class Migration(migrations.Migration):
    """Invalidating node hash - User should rehash nodes for caching"""

    dependencies = [
        ('db', '0014_add_node_uuid_unique_constraint'),
    ]

    operations = [
        migrations.RunPython(notify_user, reverse_code=notify_user),
        migrations.RunSQL(
            """ DELETE FROM db_dbextra WHERE key='""" + _HASH_EXTRA_KEY + """';""",
            reverse_sql=""" DELETE FROM db_dbextra WHERE key='""" + _HASH_EXTRA_KEY + """';"""),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
