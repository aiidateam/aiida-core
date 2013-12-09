#!/usr/bin/env python
import sys
from aiida.common.utils import load_django
load_django()

from aiida.orm.workflow import Workflow

#12 for BN, 20 for BNH2
try:
    wfid = int(sys.argv[1])
except (ValueError, IndexError):
    print >> sys.stderr, "Pass as parameter the WF ID"
    sys.exit(1)

w = Workflow.get_subclass_from_pk(wfid)
l = w.get_step_calculations(w.start)

a = []
b = []
en = []

for c in l:
    a.append(c.res.cell['lattice_vectors'][0][0])
    b.append(c.res.cell['lattice_vectors'][1][1])
    en.append(c.res.energy[-1])

print "# a b en"
for aa, bb, een in  sorted(zip(a,b,en)):
    print aa, bb, een


