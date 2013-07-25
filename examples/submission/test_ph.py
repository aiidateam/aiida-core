#!/usr/bin/env python
import sys
import os
import paramiko
import getpass

try:
    computername = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Pass the computer name."
    sys.exit(1)

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

# If True, load the pseudos from the family specified below
# Otherwise, use static files provided
auto_pseudos = True
pseudo_family = 'pslib030-pbesol-rrkjus'

queue = None
#queue = "P_share_queue"


def get_or_create_code(computer):
    if computer.hostname.startswith("aries"):
#        code_path = "/home/cepellot/software/espresso-5.0.2/bin/ph.x"
        code_path = "/home/cepellot/software/espresso-svn/espresso/bin/ph.x"
        code_version = "5.0.3"
        prepend_text = 'module load intel/mpi/4.0.3 intel/12.1.2'
    elif computer.hostname.startswith("rosa"):
        code_path = "/project/s337/espresso-svn/bin/ph.x"
        code_version = "5.0.3"
        prepend_text = ''        
    else:
        raise ValueError("Only aries and rosa are supported at the moment.")
    
    useful_codes = Code.query(computer=computer.dbcomputer,
                              attributes__key="_remote_exec_path",
                              attributes__tval=code_path).filter(
                                  attributes__key="version", attributes__tval=code_version)

    if not(useful_codes):
        print >> sys.stderr, "Creating the code..."
        code = Code(remote_computer_exec=(computer, code_path))
        code.set_prepend_text(prepend_text)
        code.store()
        code.set_metadata("version", code_version)
        return code
    
    elif len(useful_codes) == 1:
        print >> sys.stderr, "Using the existing code {}...".format(useful_codes[0].pk)
        return useful_codes[0]
    else:
        raise ValueError("More than one valid code!")
        

#####

computer = Computer.get(computername)
code = get_or_create_code(computer)

if computer.hostname.startswith("aries"):
    num_cpus_per_machine = 48
elif computer.hostname.startswith("rosa"):
    num_cpus_per_machine = 32
else:
    raise ValueError("num_cpus_per_machine not specified for the current machine")

parameters = ParameterData({
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
parentcalc = QEPwCalc.get_subclass_from_uuid('9265f520-f478-11e2-95a0-00259024cefd')
calc = QEPhCalc(computer=computer)

calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources(num_machines=1, num_cpus_per_machine=num_cpus_per_machine)
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

