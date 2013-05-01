#!/usr/bin/env python
import sys

from aida.common.utils import load_django
load_django()

from django.db.models import Q
from aida.orm import Calculation
from aida.common.datastructures import calcStates

print_all = False
try:
    allstr = sys.argv[1]
    if allstr != '--all':
        print >> sys.stderr, "If you pass a parameter, this must be --all"
        sys.exit(1)
    print_all = True
except IndexError:
    pass

if print_all:
    calclist = Calculation.query()
else:
    calclist = Calculation.query(~Q(attributes__tval=calcStates.RETRIEVED),
                                  ~Q(attributes__tval=calcStates.SUBMISSIONFAILED),
                                  ~Q(attributes__tval=calcStates.UNDETERMINED),
                                  ~Q(attributes__tval=calcStates.NEW),
                                  attributes__key="_state"
                                  )

for c in calclist:
    print "{} {} {} {} {} {}".format(int(c), c.label, c.get_state(), c.get_scheduler_state(), c.get_job_id(), c.dbnode.time)



