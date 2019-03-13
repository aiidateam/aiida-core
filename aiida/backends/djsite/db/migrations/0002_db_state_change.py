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

from django.db import models, migrations

from aiida.backends.djsite.db.migrations import upgrade_schema_version


REVISION = '1.0.2'
DOWN_REVISION = '1.0.1'


def fix_calc_states(apps, schema_editor):
    from aiida.orm.utils import load_node

    # These states should never exist in the database but we'll play it safe
    # and deal with them if they do
    DbCalcState = apps.get_model('db', 'DbCalcState')
    for calc_state in DbCalcState.objects.filter(
            state__in=[u'UNDETERMINED', u'NOTFOUND']):
        old_state = calc_state.state
        calc_state.state = u'FAILED'
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
                                   choices=[(u'RETRIEVALFAILED', u'RETRIEVALFAILED'), (u'COMPUTED', u'COMPUTED'),
                                            (u'RETRIEVING', u'RETRIEVING'), (u'WITHSCHEDULER', u'WITHSCHEDULER'),
                                            (u'SUBMISSIONFAILED', u'SUBMISSIONFAILED'), (u'PARSING', u'PARSING'),
                                            (u'FAILED', u'FAILED'), (u'FINISHED', u'FINISHED'),
                                            (u'TOSUBMIT', u'TOSUBMIT'), (u'SUBMITTING', u'SUBMITTING'),
                                            (u'IMPORTED', u'IMPORTED'), (u'NEW', u'NEW'),
                                            (u'PARSINGFAILED', u'PARSINGFAILED')]),
            preserve_default=True,
        ),
        # Fix up any calculation states that had one of the removed states
        migrations.RunPython(fix_calc_states),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
