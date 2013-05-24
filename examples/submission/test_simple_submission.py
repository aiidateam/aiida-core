#!/usr/bin/env python
import sys
import os
import paramiko

try:
    machine = sys.argv[1]
except IndexError:
    print >> sys.stderr, "Pass the machine name."
    sys.exit(1)

from aida.common.utils import load_django
load_django()

from aida.common import aidalogger
import logging
aidalogger.setLevel(logging.INFO)

import tempfile
import datetime

from aida.orm import Calculation, Code, Data, Computer
from aida.execmanager import submit_calc
from aida.djsite.utils import get_automatic_user

#from aida.common.pluginloader import load_plugin
#ParameterData = load_plugin(Data, 'aida.orm.dataplugins', 'parameter')
from aida.orm.dataplugins.parameter import ParameterData
from aida.orm.dataplugins.singlefile import SinglefileData
from aida.orm.dataplugins.remote import RemoteData

# A string with the version of this script, used to recreate a code when necessary
current_version = "1.0.4"
queue = None
#queue = "P_share_queue"

def get_or_create_machine():
    import json
    from aida.common.exceptions import NotExistent

#    # I can delete the computer first
#### DON'T DO THIS! WILL ALSO DELETE ALL CALCULATIONS THAT WERE USING
#### THIS COMPUTER!
#    from aida.djsite.db.models import DbComputer
#    DbComputer.objects.filter(hostname=computername).delete()
    
    if machine == 'localhost':
        try:
            computer = Computer.get("localhost")
            print >> sys.stderr, "Using the existing computer {localhost}..."
        except NotExistent:
            print >> sys.stderr, "Creating a new localhostcomputer..."
            computer = Computer(hostname="localhost",transport_type='local',
                                scheduler_type='pbspro')
            computer.set_workdir("/tmp/{username}/aida")
            computer.store()

        from aida.djsite.db.models import AuthInfo
        auth_params = {}

        authinfo, created = AuthInfo.objects.get_or_create(
            aidauser=get_automatic_user(),
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
            workdir = "/scratch/{username}/aida"
        elif machine.startswith('rosa'):
            computername = "rosa.cscs.ch"
            schedulertype = 'slurm'
            workdir = "/scratch/rosa/{username}/aida"
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
            computer.store()

        from aida.djsite.db.models import AuthInfo
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
            aidauser=get_automatic_user(),
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

def get_or_create_code():
    import tempfile

    useful_codes = Code.query(attributes__key="_local_executable",
                              attributes__tval="sum.py").filter(
                                  attributes__key="version", attributes__tval=current_version)

    if not(useful_codes):
        print >> sys.stderr, "Creating the code..."
        with tempfile.NamedTemporaryFile() as f:
            f.write("""#!/usr/bin/env python
import sys

try:
    with open('factor.dat') as f:
       factor = float(f.read().strip())
except IOError:
    print >> sys.stderr, "No factor file found, using factor = 1"
except ValueError:
    print >> sys.stderr, "The value in factor.dat is not a valid number"
    sys.exit(1)

try:
    print factor*float(sys.argv[1])+float(sys.argv[2])
except KeyError:
    print >> sys.stderr, "Pass two numbers on the command line"
    sys.exit(1)
except ValueError:
    print >> sys.stderr, "The values on the command line are not valid numbers"
    sys.exit(1)

try:
    with open('check.txt') as f:
        print '*'*80
        print "Read from file check.txt:"
        print f.read()
        print '*'*80
except IOError:
    print >> sys.stderr, "No check file found!"
    sys.exit(1)
""")
            f.flush()
            code = Code(local_executable = "sum.py", 
                        input_plugin='simpleplugins.templatereplacer')
            code.add_path(f.name, "sum.py")
            code.store()
            code.set_metadata("version", current_version)
        return code
    
    elif len(useful_codes) == 1:
        print >> sys.stderr, "Using the existing code {}...".format(useful_codes[0].uuid)
        return useful_codes[0]
    else:
        raise ValueError("More than one valid code!")
        

#####

computer = get_or_create_machine()
code = get_or_create_code()

template_data = ParameterData({
    'input_file_template': "{factor}\n",
    # TODO: pass only input_file_name and no template and see if an error is raised
    'input_file_name': "factor.dat",
    'cmdline_params': ["{add1}", "{add2}"],
    'output_file_name': "result.txt",
    'files_to_copy': [('the_only_local_file','check.txt'),
                      ('the_only_remote_node','bashrc-copy')],
    }).store()

parameters = ParameterData({
    'add1': 3.45,
    'add2': 7.89,
    'factor': 2,
    }).store()

with tempfile.NamedTemporaryFile() as f:
    f.write("double check, created @ {}".format(datetime.datetime.now()))
    f.flush()
    # I don't worry of the name with which it is internally stored
    fileparam = SinglefileData(filename=f.name).store()

remoteparam = RemoteData(remote_machine=computer.hostname,
                         remote_path="/etc/inittab").store()

calc = Calculation(computer=computer)
calc.set_max_wallclock_seconds(12*60) # 12 min
calc.set_num_nodes(1)
calc.set_num_cpus_per_node(1)
if queue is not None:
    calc.set_queue_name(queue)
calc.store()
print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

calc.set_code(code)
## Just for debugging purposes, I check that I can 'reset' the code
#calc.set_code(code)

calc.add_link_from(template_data, label="template")
calc.add_link_from(parameters, label="parameters")
calc.add_link_from(fileparam, label="the_only_local_file")
calc.add_link_from(remoteparam, label="the_only_remote_node")

submit_calc(calc)
print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
    calc.uuid,calc.dbnode.pk)

