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

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')
RemoteData = DataFactory('remote')
# Used to make sure that the parent is a pw.x calculation
QEPwCalc = CalculationFactory('quantumespresso.pw') 


################################################################

try:
    dontsend = sys.argv[1]
    if dontsend == "--dont-send":
        submit_test = True
    elif dontsend == "--send":
        submit_test = False
    else:
        raise IndexError
except IndexError:
    print >> sys.stderr, ("The first parameter can only be either "
                          "--send or --dont-send")
    sys.exit(1)
    
try:
    parent_id = sys.argv[2]
    codename = sys.argv[3]
except IndexError:
    print >> sys.stderr, ("Must provide as further parameters the parent ID and "
                     "a phonon codename")
    sys.exit(1)

# If True, load the pseudos from the family specified below
# Otherwise, use static files provided
expected_code_type='quantumespresso.ph'

queue = None
#queue = "P_share_queue"
     
#####

try:
    int(parent_id)
except ValueError:
    raise ValueError('Parent_id not an integer: {}'.format(parent_id))

try:
    if codename is None:
        raise ValueError
    code = Code.get(codename)
    if code.get_input_plugin_name() != expected_code_type: 
        raise ValueError
except (NotExistent, ValueError):
    valid_code_labels = [c.label for c in Code.query(
            dbattributes__key="input_plugin",
            dbattributes__tval=expected_code_type)]
    # TODO: query also only for codes that are on the same computer
    if valid_code_labels:
        print >> sys.stderr, "Pass as first parameter a valid code label."
        print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_code_type)
        for l in valid_code_labels:
            print >> sys.stderr, "*", l
    else:
        print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_code_type)
        print >> sys.stderr, "    verdi code setup"
    sys.exit(1)

######

parameters = ParameterData(dict={
            'INPUTPH': {
                'tr2_ph' : 1.0e-8,
                'epsil' : True,
                'ldisp' : True,
                'nq1' : 1,
                'nq2' : 1,
                'nq3' : 1,
                }})

parentcalc = QEPwCalc.get_subclass_from_pk(parent_id)

calc = code.new_calc()
calc.label = "Test QE ph.x"
calc.description = "Test calculation with the Quantum ESPRESSO ph.x code"

calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources({"num_machines": 1})
if queue is not None:
    calc.set_queue_name(queue)

calc.use_parameters(parameters)
calc.set_parent_calc( parentcalc )

if submit_test:
    subfolder, script_filename = calc.submit_test()
    print "Test_submit for calculation (uuid='{}')".format(
        calc.uuid)
    print "Submit file in {}".format(os.path.join(
        os.path.relpath(subfolder.abspath),
        script_filename
        ))
else:
    calc.store_all()
    print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)
