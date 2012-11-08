# Functions for submitting jobs to SGE within AIDA

import os, sys, glob, django, getpass, pickle, json, socket
from string import *
from ase import *
from numpy import *
from django.conf import settings
from django.template import Context, Template
from shortcuts import *
from codeplugins import *

# Repository locations on the AIDA server, they may not be visible on the cluster
calc_repo_path = '/s1/abinitio/software/aida/repository/calculations/'
struc_repo_path = '/s1/abinitio/software/aida/repository/structures/'
server = socket.gethostname()
localhost = 'localhost'
# some global placeholders
location_temp = ''
location_perm = ''
cluster = ''

os.environ['DJANGO_SETTINGS_MODULE'] = 'environment.aidadb.settings'
from environment.aidadb.data.models import *


def Get_calc(arg):
    if isinstance(arg, int):
        C = Calculation.objects.get(pk=arg)
        C.params = json.loads(C.attributes['parameters'])   # need to implem
    else:
        C = Calculation()
        params = arg
        C.user = AuthUser.objects.get(username=getpass.getuser())
        C.project = Project.objects.get(title=params.PROJECT)
        C.type = CalculationType.objects.get(title=params.CALCTYPE)
        C.computer = Computer.objects.get(hostname=params.COMPUTER)
        C.code = Code.objects.get(title=params.CODE, computer__hostname__exact=params.COMPUTER)
        C.usedb = params.USEDB        #whether DB writing is allowed

        #Save_params(C, params)     #save param as dict to db
        C.params = params   #the server will know these temporary params, cluster may not

        #save for the first time to DB to get id
        Set_calc_status(C, 'Initiated')
        return C

def Submit(C):
    # Initiate new entry in db. This is done on the server in script dir
    # Initated calc is only bare bones, more meat later
    # An initial save in needed to get and id, to attach foreign links
    # This is due to Django's active record pattern, SqlAlchemy would not care

    global location_perm
    global location_temp
    global cluster

    location_perm = calc_repo_path + str(C.id)
    location_temp = C.computer.scratch_location  + str(C.id)
    cluster = C.computer.hostname  
    # make dirs for calculations
    run_command(localhost, '/bin/mkdir %s' % (location_perm))
    run_command(cluster, '/bin/mkdir %s' % (location_temp))
    # record the calling script itself
    scriptfile = os.getenv('PWD') + '/' + sys.argv[0]
    run_command (localhost, '/bin/cp -a %s %s' % (scriptfile, location_perm))
    # chdir to calc dir on server
    os.chdir(location_perm)
    Assign_potentials(C)
    Write_inputs(C)
    SGE_submit(C)
    

def Set_calc_status(C, status):
    if C.usedb:
        C.status = CalculationStatus.objects.get(title=status)
        C.save()


def SGE_submit(C):
    #SGE job submission. This is done on the server in calc dir
    qscript_template = """
#$ -S /bin/bash
#$ -N {{ QJOBNAME }}
#$ -j y
#$ -cwd
#$ -l h_rt={{ RUNTIME }}
#$ -q {{ QUEUE }}
#$ -hold_jid {{ JOBPREV }}
#$ -l excl={{ QEXCL }}
#$ -V
#$ -P cr_garnets
#$ -pe intel_mpi {{ NPROC }}

cat > jobscript.py <<EOF
from newaidajob import *
Start_calc(ID)
EOF

/software/python/python27 jobscript.py
""" 
# make substitutions in the above template with defined attributes in file
#   if C.runparams.JOBPREV:
    #cluster needs to know the full qscript path
    qscript_fname = 'qscript.sge'
    qscript_file = location_temp + '/' + qscript_fname
    f = open(qscript_fname,'w')
    
    #params = Load_params(C)
    #params['QJOBNAME'] = C.type + str(C.id)
    #params['JOBPREV'] = None  # to be done
    #params['ID'] = C.id
    #Save_params(C, params)   #save updated params just in case
    C.params.QJOBNAME = C.type.title + str(C.id)
    C.params.JOBPREV = None  # to be done
    C.params.ID = C.id

    qscript_text = Template(qscript_template).render(Context(C.params.__dict__))
    f.write(qscript_text)
    f.close()
    run_command (localhost, 'scp -p %s %s:%s' % (qscript_fname, cluster, location_temp))
    #run_command(cluster, 'qsub %s' % (qscript_file))
    Set_calc_status(C, 'Queued')


def Start_calc(id):
    # The job only starts at this instance!!!
    # This funciton is executed on the cluster compute node in scratch dir
    C = Calculation.objects.get(pk=id)
    location_temp = C.computer.scratch_location + '/' + str(C.id)
    # go to scratch dir. It should have all input files there already.
    os.chdir(location_temp)
    # if calc.JOBPREV != None:
    # command = '/bin/cp -r %s/temp %s/' % (calc.restartfrom.location_temp, calc.location_temp)
    # run_command(command)
    exec_file = 'run.exe'
    Set_calc_status(C, 'Running')  
    run_command(localhost, './' + exec_file)
    Set_calc_status(C, 'Finished')
    Process_outputs()

def Write_inputs(C):
    # these are run on the server
    if C.code.family.title == 'espresso':
        import espresso_plugin
        espresso_plugin.Write_inputs(C)
    elif C.code.family.title == 'vasp':
        import vasp_plugin
        vasp_plugin.Write_inputs(C)

def Restart_from(rid):
    C = Calculation.objects.get(pk=rid)
    C.params = json.loads(C.attributes['parameters'])
    C.pk = None
    C.save() # make a new duplicate calc
    

def Process_outputs(): pass


def Load_params(C):
    #produces a dict of params from db
    return json.loads(C.attributes)['parameters']


def Save_params(C, params):
    if not isinstance(params, dict):
        #assume we get a class
        params = params.__dict__
    old_params = Load_params(C)
    C.attributes['parameters'] = json.dumps(old_params.update(params))


def Get_structure(arg):
    if isinstance(arg,int) or isinstance(arg,long):
        id = arg
        S = Structure.objects.get(pk = id)
#        S.ase_obj = read_pickle('%s/struc_%s.pkl' % (struc_repo_path, S.id))
        #alternatively reconstruct ase from json
        ase_obj = Atoms(pbc=True)
        serial = json.loads(S.serial)
        ase_obj.set_cell(serial['cell'])
        for atom in serial['atoms']:
            symbol = atom['symbol']
            position = atom['position']
            ase_atom = Atom()
            ase_atom.symbol = symbol
            ase_atom.position = position
            ase_obj.append(ase_atom)
        S.num_of_atoms = ase_obj.get_number_of_atoms()
        S.formula = ase_obj.get_chemical_formula()
        S.ntype = len(set(ase_obj.get_atomic_numbers())) #number of different elements   
        S.ase_obj = ase_obj
    else:
        #assume we get ase object
        ase_obj = arg
        S = Structure()
        S.num_of_atoms = ase_obj.get_number_of_atoms()
        S.formula = ase_obj.get_chemical_formula()
        S.ntype = len(set(ase_obj.get_atomic_numbers())) #number of different elements
        cell = [list(vec) for vec in ase_obj.cell]
        serial = {'cell': cell,
                  'atoms':[{'symbol':atom.symbol, 'position':list(atom.position)} for atom in ase_obj]}
        S.serial = json.dumps(serial)
#        write_pickle('%s/struc_%s.pkl' % (struc_repo_path, S.id), ase_obj)
        S.ase_obj = ase_obj
    S.save()
    return S


def Compute_composition(S):
    pass


def Link_calc_input_struc(C,input_strucs):
    if isinstance(input_strucs, list):
        for struc in input_strucs:
            C.input_structures.add(struc)
    else:
        #assume only one struc
        C.input_structures.add(input_strucs)


def Assign_potentials(C):
    #need to modify for Vasp later
    #params = Load_params(C)
    for item in C.params.POTENTIALS:
        pot = Potential.objects.get(title=item)
        C.potentials.add(pot)


# --------- ignore ------------
class junk:
    def prepare(self):
        calc.composition = get_composition(calc)
        
        if self.code.family.title == 'espresso':     #perform all operations in the scratch dir
            write_qe_input(self)
        elif self.code.family.title == 'vasp':
            write_vasp_input(self)

        # pickle the calculation instance for record
        # overwrite previous pickle if restarting
        write_json('calc.json',self) 		
        write_pickle('calc.pkl',self)     
        
    def startfrom(self, **kwargs):
        ''' Clone the calculation and delete pk, set up dependency'''
        newcalc = self
        newcalc.pk = None
        newcalc.parent_calcs.add(self)
        return newcalc

class MyStruc(Structure):
    #smart structure class. Has ase object attached as an attribute
    class Meta:
        proxy = True
        app_label = aidadb
    
    def __init__(self, *args, **kwargs):
        super(MyStruc, self).__init__(*args, **kwargs)
        if 'dbid' in kwargs.keys():
            return self.objects.get(id=kwargs['dbid'])
            self.ase_struc = read_pickle(location)
        elif 'ase_struc' in kwargs.keys():
            ase = kwargs['ase_struc']
            self.num_of_atoms = 'test'
            self.formula = 'test'
            location = '%s/struc_%s.pkl' % (structure_path, str(self.id))


