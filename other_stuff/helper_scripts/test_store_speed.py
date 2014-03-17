# coding: utf-8
import sys

from aiida.orm import Node, Calculation
from aiida.orm.data.parameter import ParameterData
from aiida.common.utils import load_django
import time
load_django()
from aiida.djsite.db.models import DbAttribute

## DEF VALUE
#pk=5
pk = 29
#pk = 244

try:
    pk = int(sys.argv[1])
except (IndexError, ValueError):
    pass

calc = Node.get_subclass_from_pk(pk)
if isinstance(calc, Calculation):
    data = dict(calc.get_outputs(also_labels=True))['output_parameters']
else:
    data = calc

print "Starting to read pk = %s..." % pk

a = time.time()
datadict = data.get_dict()
b = time.time()
print "Read in %6.3f s. Creating new node..." % (b-a)

#try:    
#    del datadict['symmetries']
#    print "(Also removing symmetries...)"
#except KeyError:
#    print "(No 'symmetries' key to remove)"

data2 = ParameterData(datadict)

print "Starting to store..."

a = time.time()
data2.store()
b = time.time()

print "Pk of new node: %s" % data2.pk
print "Number of attributes created:", len(DbAttribute.objects.filter(dbnode=data2.dbnode))
print "Time spent to store: %6.3f s." % (b-a)
