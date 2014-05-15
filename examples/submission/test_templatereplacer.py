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
from aiida.orm import CalculationFactory, DataFactory

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')

queue = None
#queue = "P_share_queue"

def get_or_create_machine():
    import json
    from aiida.common.exceptions import NotExistent
    from aiida.djsite.db.models import DbAuthInfo
        
#    # I can delete the computer first
#### DON'T DO THIS! WILL ALSO DELETE ALL CALCULATIONS THAT WERE USING
#### THIS COMPUTER!
#    from aiida.djsite.db.models import DbComputer, DbNode
#    DbNode.objects.filter(dbcomputer__hostname=machine).delete()
#    DbComputer.objects.filter(hostname=machine).delete()

    
    if machine == 'localhost':
        try:
            computer = Computer.get("localhost")
            print >> sys.stderr, "Using the existing computer {localhost}..."
        except NotExistent:
            print >> sys.stderr, "Creating a new localhostcomputer..."
            computer = Computer(hostname="localhost",transport_type='local',
                                scheduler_type='pbspro')
            computer.set_workdir("/tmp/{username}/aiida")
            computer.set_mpirun_command("mpirun", "-np", "{tot_num_mpiprocs}")
            computer.store()

        auth_params = {}

        authinfo, created = DbAuthInfo.objects.get_or_create(
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
            mpirun_command = ['mpirun', '-np', '{tot_num_mpiprocs}']
        if machine.startswith('aries'):
            computername = "aries.epfl.ch"
            schedulertype = 'pbspro'
            workdir = "/scratch/{username}/aiida"
            mpirun_command = ['mpirun', '-np', '{tot_num_mpiprocs}']
        elif machine.startswith('rosa'):
            computername = "rosa.cscs.ch"
            schedulertype = 'slurm'
            workdir = "/scratch/rosa/{username}/aiida"
            mpirun_command = ['aprun', '-n', '{tot_num_mpiprocs}']
        elif machine.startswith('vulcan'):
            computername = "vulcan.icams.rub.de"
            schedulertype = 'sge'
            workdir = "/home/users/dorigm7s/aiida"
        else:
            print >> sys.stderr, "Unkown computer!"
            sys.exit(1)
            
        try:
            # TODO: check if this is correct:
            #computer = Computer.get(computername) #this gave an error, since the
            #computer is not identified by the computername 'name.address.address', 
            #but by 'name' only.
            computer = Computer.get(machine)
            print >> sys.stderr, "Using the existing computer {}...".format(computername)
        except NotExistent:
            print >> sys.stderr, "Creating a new computer..."
            computer = Computer(hostname=computername,transport_type='ssh',
                                scheduler_type=schedulertype)
            computer.set_workdir(workdir)
            #computer.set_mpirun_command(mpirun_command)
            computer.store()

        auth_params = {'load_system_host_keys': True,
                       'compress': True}


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

        authinfo, created = DbAuthInfo.objects.get_or_create(
            aiidauser=get_automatic_user(),
            computer=computer.dbcomputer, 
            defaults= {'auth_params': json.dumps(auth_params)},
            )

        if created:
            print "  (Created authinfo)"
        else:
            print "  (Retrieved authinfo)"
        print "*** DbAuthInfo: "
        for k,v in json.loads(authinfo.auth_params).iteritems():
            print "{} = {}".format(k, v)
        print ""

    return computer

def get_or_create_code(computer):
    #if not computer.hostname.startswith("aries"):
    #    raise ValueError("Only aries is supported at the moment.")
    code_path = "/usr/bin/less"
    code_version = "5.0.2"
    useful_codes = Code.query(computer=computer.dbcomputer,
                              dbattributes__key="_remote_exec_path",
                              dbattributes__tval=code_path).filter(
                                  dbattributes__key="version", dbattributes__tval=code_version)

    if not(useful_codes):
        print >> sys.stderr, "Creating the code..."
        code = Code(remote_computer_exec=(computer, code_path)).store()
        code.set_extra("version", code_version)
        return code
    
    elif len(useful_codes) == 1:
        print >> sys.stderr, "Using the existing code {}...".format(useful_codes[0].pk)
        return useful_codes[0]
    else:
        raise ValueError("More than one valid code!")
        

#####
computer = get_or_create_machine()
code = get_or_create_code(computer)

SimpleCalc = CalculationFactory('simpleplugins.templatereplacer')
calc = SimpleCalc(computer=computer)
calc.set_max_wallclock_seconds(4*60) # 1 min
calc.set_resources({"parallel_env": 'smp',"tot_num_mpiprocs": 1})
calc.set_queue_name('serial.q') #No parallel needed. 
calc.store()
calc.use_code(code)

from aiida.orm.data.parameter import ParameterData
input_dict = {'input_file_template':'Content to be copied: TEST',
              'input_file_name':'aiida.in',
              'output_file_name':'aiida.out'}
params = ParameterData(dict=input_dict).store()
params.add_link_to(calc,label='template')

calc.submit()
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

