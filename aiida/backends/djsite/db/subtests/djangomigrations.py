# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.testbase import AiidaTestCase



class CalcStateChanges(AiidaTestCase):
    # Class to check if the migration code that deals with removing the
    # NOTFOUND and UNDETERMINED calc states works properly
    def test_unexpected_calc_states(self):
        import logging

        from django.utils import timezone
        from aiida.orm.calculation import Calculation

        # Have to use this ugly way of importing because the django migration
        # files start with numbers which are not a valid package name
        state_change = __import__(
            'aiida.backends.djsite.db.migrations.0002_db_state_change',
            fromlist=['fix_calc_states']
        )
        from aiida.common.datastructures import calc_states
        from aiida.backends.djsite.db.models import DbCalcState, DbLog
        from aiida.orm.calculation.job import JobCalculation

        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        for state in ['NOTFOUND', 'UNDETERMINED']:
            # Let's create a dummy job calculation
            job = JobCalculation(**calc_params)
            job.store()
            # Now save the errant state
            DbCalcState(dbnode=job.dbnode, state=state).save()

            time_before_fix = timezone.now()

            # First of all, I re-enable logging in case it was disabled by
            # mistake by a previous test (e.g. one that disables and reenables
            # again, but that failed)
            logging.disable(logging.NOTSET)
            # Temporarily disable logging to the stream handler (i.e. screen)
            # because otherwise fix_calc_states will print warnings
            handler = next((h for h in logging.getLogger('aiida').handlers if
                            isinstance(h, logging.StreamHandler)), None)

            if handler:
                original_level = handler.level
                handler.setLevel(logging.ERROR)

            # Call the code that deals with updating these states
            state_change.fix_calc_states(None, None)

            if handler:
                handler.setLevel(original_level)

            current_state = job.get_state()
            self.assertNotEqual(current_state, state,
                                "Migration code failed to change removed state {}".
                                format(state))
            self.assertEqual(current_state, calc_states.FAILED,
                             "Migration code failed to set removed state {} to {}".
                             format(current_state, calc_states.FAILED))

            result = DbLog.objects.filter(
                objpk__exact=job.pk,
                levelname__exact=logging.getLevelName(logging.WARNING),
                time__gt=time_before_fix
            )

            self.assertEquals(len(result), 1,
                              "Couldn't find a warning message with the change "
                              "from {} to {}, or found too many: I got {} log "
                              "messages".format(state, calc_states.FAILED, len(result))
                              )
