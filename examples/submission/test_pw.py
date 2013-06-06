#!/usr/bin/env python
import sys
import os
import paramiko
import getpass

try:
    machine = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Pass the machine name."
    sys.exit(1)

from aiida.common.utils import load_django
load_django()

from aiida.common import aiidalogger
import logging
aiidalogger.setLevel(logging.INFO)

from aiida.orm import Code, Computer
from aiida.djsite.utils import get_automatic_user
import aiida.common.utils
from aiida.orm import CalculationFactory, DataFactory

#from aiida.orm.data.upf import UpfData
#from aiida.orm.data.parameter import ParameterData
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')

#print ParameterData.__module__

# A string with the version of this script, used to recreate a code when necessary
current_version = "1.0.5"
queue = None
#queue = "P_share_queue"

def get_or_create_machine():
    import json
    from aiida.common.exceptions import NotExistent
    from aiida.djsite.db.models import AuthInfo
        
#    # I can delete the computer first
#### DON'T DO THIS! WILL ALSO DELETE ALL CALCULATIONS THAT WERE USING
#### THIS COMPUTER!
#    from aiida.djsite.db.models import DbComputer
#    DbComputer.objects.filter(hostname=computername).delete()
    
    if machine == 'localhost':
        try:
            computer = Computer.get("localhost")
            print >> sys.stderr, "Using the existing computer {localhost}..."
        except NotExistent:
            print >> sys.stderr, "Creating a new localhostcomputer..."
            computer = Computer(hostname="localhost",transport_type='local',
                                scheduler_type='pbspro')
            computer.set_workdir("/tmp/{username}/aiida")
            computer.set_mpirun_command("mpirun", "-np", "{tot_num_cpus}")
            computer.store()

        auth_params = {}

        authinfo, created = AuthInfo.objects.get_or_create(
            aiidauser=get_automatic_user(),
            computer=computer.dbcomputer, 
            defaults= {'auth_params': json.dumps(auth_params)},
            )

        if created:
            print "  (Created authinfo)"
        else:
            print "  (Retrieved authinfo)"

    else: # ssh case
        if machine.startswith('bellatrix'):
            computername = "bellatrix.epfl.ch"
            schedulertype = 'pbspro'
            workdir = "/scratch/{username}/aiida"
            mpirun_command = ['mpirun', '-np', '{tot_num_cpus}']
        elif machine.startswith('rosa'):
            computername = "rosa.cscs.ch"
            schedulertype = 'slurm'
            workdir = "/scratch/rosa/{username}/aiida"
            mpirun_command = ['aprun', '-n', '{tot_num_cpus}']
        else:
            print >> sys.stderr, "Unkown computer!"
            sys.exit(1)
            
        try:
            computer = Computer.get(computername)
            print >> sys.stderr, "Using the existing computer {}...".format(computername)
        except NotExistent:
            print >> sys.stderr, "Creating a new computer..."
            computer = Computer(hostname=computername,transport_type='ssh',
                                scheduler_type=schedulertype)
            computer.set_workdir(workdir)
            computer.set_mpirun_command(mpirun_command)
            computer.store()

        auth_params = {'load_system_host_keys': True}


        config = paramiko.SSHConfig()
        try:
            config.parse(open(os.path.expanduser('~/.ssh/config')))
        except IOError:
            # No file found, so empty configuration
            pass
        # machine_config is a dict with only relevant properties set
        machine_config = config.lookup(computername)

        try:
            auth_params['username'] = machine_config['user']
        except KeyError:
            # No user set up in the config file: I explicitly set the local username
            auth_params['username'] = getpass.getuser()

        try:
            auth_params['key_filename'] = os.path.expanduser(
                machine_config['identityfile'])
        except KeyError:
            pass 
        
        try:
            auth_params['port'] = machine_config['port']
        except KeyError:
            pass       

        authinfo, created = AuthInfo.objects.get_or_create(
            aiidauser=get_automatic_user(),
            computer=computer.dbcomputer, 
            defaults= {'auth_params': json.dumps(auth_params)},
            )

        if created:
            print "  (Created authinfo)"
        else:
            print "  (Retrieved authinfo)"
        print "*** AuthInfo: "
        for k,v in json.loads(authinfo.auth_params).iteritems():
            print "{} = {}".format(k, v)
        print ""

    return computer

def get_or_create_code(computer):
    if not computer.hostname.startswith("rosa"):
        raise ValueError("Only rosa is supported at the momen.")
    code_path = "/project/s337/espresso-svn/bin/pw.x"
    code_version = "5.0.3a1"
    useful_codes = Code.query(computer=computer.dbcomputer,
                              attributes__key="_remote_exec_path",
                              attributes__tval=code_path).filter(
                                  attributes__key="version", attributes__tval=code_version)

    if not(useful_codes):
        print >> sys.stderr, "Creating the code..."
        code = Code(remote_machine_exec=(computer, code_path)).store()
        code.set_metadata("version", code_version)
        return code
    
    elif len(useful_codes) == 1:
        print >> sys.stderr, "Using the existing code {}...".format(useful_codes[0].pk)
        return useful_codes[0]
    else:
        raise ValueError("More than one valid code!")
        

#####

computer = get_or_create_machine()
code = get_or_create_code(computer)

raw_pseudos = [
    ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba', 'pbesol'),
    ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti', 'pbesol'),
    ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O', 'pbesol')]

pseudos_to_use = {}
for fname, elem, pot_type in raw_pseudos:
    absname = os.path.realpath(os.path.join(os.path.dirname(__file__),"data",fname))
    pseudo, created = UpfData.get_or_create(
        absname, element=elem,pot_type=pot_type,use_first=True)
    if created:
        print "Created the pseudo for {}".format(elem)
    else:
        print "Using the pseudo for {} from DB: {}".format(elem,pseudo.pk)
    pseudos_to_use[elem] = pseudo

parameters = ParameterData({
    'ecutwfc': 45.,
    'ecutrho': 300.,
    }).store()

QECalc = CalculationFactory('quantumespresso.pw')
calc = QECalc(computer=computer)
calc.set_max_wallclock_seconds(1*3600) # 1 hour
calc.set_num_machines(2)
calc.set_num_cpus_per_machine(32)
if queue is not None:
    calc.set_queue_name(queue)
calc.store()
print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

calc.set_code(code)
## Just for debugging purposes, I check that I can 'reset' the code
#calc.set_code(code)
calc.set_parameters(parameters)
for k, v in pseudos_to_use.iteritems():
    calc.set_pseudo(v, kind=k)

calc.set_kpoints(kpoints)
calc.set_settings(settings)
#from aiida.orm.data.remote import RemoteData
#calc.set_outdir(remotedata)

calc.submit()
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

