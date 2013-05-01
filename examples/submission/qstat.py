#!/usr/bin/env python
from aida.common.utils import load_django
load_django()

from django.db.models import Q
from aida.orm import Calculation
from aida.common.datastructures import calcStates

calclist = Calculation.query(~Q(attributes__tval=calcStates.RETRIEVED),
                             ~Q(attributes__tval=calcStates.SUBMISSIONFAILED),
                             ~Q(attributes__tval=calcStates.UNDETERMINED),
                             ~Q(attributes__tval=calcStates.NEW),
                              attributes__key="_state"
                              )

for c in calclist:
    print "{} {} {} {}".format(int(c), c.get_state(), c.get_scheduler_state(), c.dbnode.time)



