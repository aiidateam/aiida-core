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

# If True, load the pseudos from the family specified below
# Otherwise, use static files provided
auto_pseudos = True
pseudo_family = 'pslib030-pbesol-rrkjus'

queue = None
#queue = "P_share_queue"


def get_or_create_code(computer):
    if computer.hostname.startswith("aries"):
        code_path = "/home/cepellot/software/espresso-5.0.2/bin/cp.x"
        code_version = "5.0.2"
        prepend_text = 'module load intel/mpi/4.0.3 intel/12.1.2'
    elif computer.hostname.startswith("rosa"):
        code_path = "/project/s337/espresso-svn/bin/cp.x"
        code_version = "5.0.2"
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


alat = 4. # angstrom
cell = [[alat, 0., 0.,],
        [0., alat, 0.,],
        [0., 0., alat,],
       ]

# BaTiO3 cubic structure
s = StructureData(cell=cell)
s.append_atom(position=(0.,0.,0.),symbols=['Ba'])
s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])
s.store()

parameters = ParameterData({
            'CONTROL': {
                'calculation': 'cp',
                'restart_mode': 'from_scratch',
                'wf_collect': False,
                'iprint': 1,
                'isave': 100,
                'dt': 3.,
                'max_seconds': 25*60,
                'nstep': 10,
                },
            'SYSTEM': {
                'ecutwfc': 30.,
                'ecutrho': 240.,
                'nr1b': 24,
                'nr2b': 24,
                'nr3b': 24,
                },
            'ELECTRONS': {
                'electron_damping': 1.e-1,
                'electron_dynamics': 'damp', 
                'emass': 400.,
                'emass_cutoff': 3.,
                },
            'IONS': {
                'ion_dynamics': 'none',
            }}).store()
                

QECalc = CalculationFactory('quantumespresso.cp')
calc = QECalc(computer=computer)
calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources(num_machines=1, num_cpus_per_machine=num_cpus_per_machine)
if queue is not None:
    calc.set_queue_name(queue)
calc.store()
print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

calc.use_structure(s)
calc.use_code(code)
calc.use_parameters(parameters)

if auto_pseudos:
    try:
        calc.use_pseudo_from_family(pseudo_family)
        print "Pseudos successfully loaded from family {}".format(pseudo_family)
    except NotExistent:
        print ("Pseudo or pseudo family not found. You may want to load the "
               "pseudo family, or set auto_pseudos to False.")
        raise
else:
    raw_pseudos = [
       ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba', 'pbesol'),
       ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti', 'pbesol'),
       ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O', 'pbesol')]

    pseudos_to_use = {}
    for fname, elem, pot_type in raw_pseudos:
        absname = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                "data",fname))
        pseudo, created = UpfData.get_or_create(
            absname, element=elem,pot_type=pot_type,use_first=True)
        if created:
            print "Created the pseudo for {}".format(elem)
        else:
            print "Using the pseudo for {} from DB: {}".format(elem,pseudo.pk)
        pseudos_to_use[elem] = pseudo

    for k, v in pseudos_to_use.iteritems():
        calc.use_pseudo(v, kind=k)

#calc.use_settings(settings)
#from aiida.orm.data.remote import RemoteData
#calc.set_outdir(remotedata)

calc.submit()
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

