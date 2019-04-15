# -*- coding: utf-8 -*-
from aiida.backends.djsite.db.testbase import AiidaTestCase

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


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

            # Temporarily disable logging to the stream handler (i.e. screen)
            # because otherwise fix_calc_states will print warnings
            handler = next((h for h in logging.getLogger('aiida').handlers if
                           isinstance(h, logging.StreamHandler)), None)
            if handler:
                handler.setLevel(logging.ERROR)

            # Call the code that deals with updating these states
            state_change.fix_calc_states(None, None)

            if handler:
                handler.setLevel(logging.NOTSET)

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
                              "Couldn't find a warning message with the change"
                              "from {} to {}".format(state, calc_states.FAILED)
                              )
