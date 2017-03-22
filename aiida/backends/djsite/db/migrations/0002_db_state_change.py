# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import unicode_literals

from django.db import models, migrations

from aiida.backends.djsite.db.migrations import update_schema_version


SCHEMA_VERSION = "1.0.2"


def fix_calc_states(apps, schema_editor):
    from aiida.backends.djsite.db.models import DbCalcState
    # from aiida.orm import load_node
    from aiida.orm.utils import load_node

    # These states should never exist in the database but we'll play it safe
    # and deal with them if they do
    for calc_state in DbCalcState.objects.filter(
            state__in=[b'UNDETERMINED', b'NOTFOUND']):
        old_state = calc_state.state
        calc_state.state = b'FAILED'
        calc_state.save()
        # Now add a note in the log to say what we've done
        calc = load_node(pk=calc_state.dbnode.pk)
        calc.logger.warning(
            "Job state {} found for calculation {} which should never be in "
            "the database. Changed state to FAILED.".format(
                old_state, calc_state.dbnode.pk))

class Migration(migrations.Migration):
    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbcalcstate',
            name='state',
            # The UNDETERMINED and NOTFOUND 'states' were removed as these
            # don't make sense
            field=models.CharField(db_index=True, max_length=25,
                                   choices=[(b'RETRIEVALFAILED', b'RETRIEVALFAILED'), (b'COMPUTED', b'COMPUTED'),
                                            (b'RETRIEVING', b'RETRIEVING'), (b'WITHSCHEDULER', b'WITHSCHEDULER'),
                                            (b'SUBMISSIONFAILED', b'SUBMISSIONFAILED'), (b'PARSING', b'PARSING'),
                                            (b'FAILED', b'FAILED'), (b'FINISHED', b'FINISHED'),
                                            (b'TOSUBMIT', b'TOSUBMIT'), (b'SUBMITTING', b'SUBMITTING'),
                                            (b'IMPORTED', b'IMPORTED'), (b'NEW', b'NEW'),
                                            (b'PARSINGFAILED', b'PARSINGFAILED')]),
            preserve_default=True,
        ),
        # Fix up any calculation states that had one of the removed states
        migrations.RunPython(fix_calc_states),
        update_schema_version(SCHEMA_VERSION)
    ]
