#!/usr/bin/env python
import sys

from aiida.common.utils import load_django
load_django()

from aiida.orm import Calculation
       
try:
    idstr = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Pass a UUID or a ID"
    sys.exit(1)

try:
    the_id = int(idstr)
except ValueError:
    c = Calculation.get_subclass_from_uuid(idstr)
else:
    c = Calculation.get_subclass_from_pk(the_id)

print "CALCULATION STATE:", c.get_state()
print "Trying to kill it..."

retval = c.kill()





