#!/usr/bin/env python
import sys
import os
import paramiko
import getpass

from aiida.common.utils import load_django
load_django()

from aiida.common import aiidalogger
import logging
from aiida.common.exceptions import NotExistent
aiidalogger.setLevel(logging.INFO)

from aiida.orm import Code, Computer
from aiida.djsite.utils import get_automatic_user
from aiida.orm import CalculationFactory, DataFactory

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')
RemoteData = DataFactory('remote')



################################################################

try:
    parent_id = sys.argv[1]
except IndexError:
    parent_id = None

try:
    codename = sys.argv[2]
except IndexError:
    raise IOError("Must provide codename in input")
#codename = None

# If True, load the pseudos from the family specified below
# Otherwise, use static files provided
expected_exec_name='ph.x'

queue = None
#queue = "P_share_queue"
     
#####

if parent_id is None:
    raise ValueError("Must provide parent_id")
try:
    int(parent_id)
except ValueError:
    raise ValueError('Parent_id not an integer: {}'.format(parent_id))

try:
    if codename is None:
        raise ValueError
    code = Code.get(codename)
    if not code.get_remote_exec_path().endswith(expected_exec_name):
        raise ValueError
except (NotExistent, ValueError):
    valid_code_labels = [c.label for c in Code.query(
            dbattributes__key="remote_exec_path",
            dbattributes__tval__endswith="/{}".format(expected_exec_name))]
    if valid_code_labels:
        print >> sys.stderr, "Pass as first parameter a valid code label."
        print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_exec_name)
        for l in valid_code_labels:
            print >> sys.stderr, "*", l
    else:
        print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_exec_name)
        print >> sys.stderr, "    verdi code setup"
    sys.exit(1)

######

computer = code.get_remote_computer()

if computer.hostname.startswith("aries"):
    num_cpus_per_machine = 48
elif computer.hostname.startswith("rosa"):
    num_cpus_per_machine = 32
elif computer.hostname.startswith("bellatrix"):
    num_cpus_per_machine = 16
else:
    raise ValueError("num_cpus_per_machine not specified for the current machine")

parameters = ParameterData(dict={
            'INPUTPH': {
                'tr2_ph' : 1.0e-8,
                'epsil' : True,
                'ldisp' : True,
                'nq1' : 1,
                'nq2' : 1,
                'nq3' : 1,
                }}).store()

QEPhCalc = CalculationFactory('quantumespresso.ph')
QEPwCalc = CalculationFactory('quantumespresso.pw')
parentcalc = QEPwCalc.get_subclass_from_pk(parent_id)
calc = QEPhCalc(computer=computer)

calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources({"num_machines": 1, "num_cpus_per_machine": num_cpus_per_machine})
if queue is not None:
    calc.set_queue_name(queue)
calc.store()
print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

calc.use_parameters(parameters)
calc.use_code(code)
calc.set_parent_calc( parentcalc )

calc.submit()
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

