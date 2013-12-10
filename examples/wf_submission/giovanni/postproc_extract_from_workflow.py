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
jid = []

for c in l:
    a.append(c.res.cell['lattice_vectors'][0][0])
    b.append(c.res.cell['lattice_vectors'][1][1])
    en.append(c.res.energy[-1])
    jid.append(c.pk)

print "# a b en"
for bb, aa, een, pk in  sorted(zip(b,a,en,jid)):
    print aa, bb, een, pk


