#!/usr/bin/env python
import sys
import os

from aiida.common.utils import load_django
load_django()

from aiida.common import aiidalogger
import logging
from aiida.common.exceptions import NotExistent
aiidalogger.setLevel(logging.INFO)

from aiida.orm import Code
from aiida.orm import CalculationFactory, DataFactory
from aiida.djsite.db.models import DbGroup
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')
import numpy
from aiida.orm import Calculation

################################################################
try:
    parent_id = sys.argv[1]
except IndexError:
    parent_id = None

try:
    codename = sys.argv[2]
except IndexError:
    codename = None

num_machines = 1 # node numbers
queue = None

#####
expected_exec_name='q2r.x'

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
            dbattributes__key="_remote_exec_path",
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

computer = code.get_remote_computer()

if computer.hostname.startswith("aries"):
    num_cpus_per_machine = 48
elif computer.hostname.startswith("rosa"):
    num_cpus_per_machine = 32
elif computer.hostname.startswith("bellatrix"):
    num_cpus_per_machine = 16
elif computer.hostname.startswith("theospc12"):
    num_cpus_per_machine = 8
elif computer.hostname.startswith("localhost"):
    num_cpus_per_machine = 6
else:
    raise ValueError("num_cpus_per_machine not specified for the current machine: {0}".format(computer.hostname))

parameters = ParameterData({
            'INPUT': {
                'zasr': 'simple',
                },
            }).store()
                
Q2rCalc = CalculationFactory('quantumespresso.q2r')
calc = Q2rCalc(computer=computer)
calc.set_max_wallclock_seconds(60*30) # 30 min
calc.set_resources(num_machines=num_machines, num_cpus_per_machine=num_cpus_per_machine) # must run in serial
calc.store()

calc.use_parameters(parameters)
parentcalc = Calculation.get_subclass_from_pk(parent_id)
calc.set_parent_calc(parentcalc)
calc.use_code(code)

calc.submit()
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

