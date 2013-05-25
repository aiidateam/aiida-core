#!/usr/bin/env python
from aida.common.utils import load_django
load_django()

def shorten(v):
    limit = 60
    text = unicode(v)
    text.replace('\n','').replace('\r','')
    if len(text) > limit:
        return text[:limit-3] + u"..."
    else:
        return text

import sys
from aida.orm import Node, Calculation

try:
    idstr = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Pass a UUID or a ID"
    sys.exit(1)

try:
    print idstr
    the_id = int(idstr)
except ValueError:
    c = Calculation(uuid=idstr)
else:
    c = Calculation.get_subclass_from_pk(the_id)

print "CALCULATION STATE:", c.get_state()

print "INPUTS:"
for label, node in c.get_inputs(also_labels=True):
    print "* input of type {} with link name {}".format(
        node.__class__.__name__, label)
print ""
print "OUTPUTS:"
for label, node in c.get_outputs(also_labels=True):
    print "* output of type {} with link name {}".format(
        node.__class__.__name__, label)

lj = c.get_last_jobinfo()
if lj:
    print "\n".join("{} = {}".format(*i) for i in lj.iteritems())
else:
    print "unable to get last_jobinfo"


