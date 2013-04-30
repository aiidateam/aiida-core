'''
This file contains specifications on the user interface of Aiida.
The goal is to keep the UI as simple as possible without sacrificing the querying and inheritance power.
'''

#Workflow use cases
def SimpleWorkflow():
    
    #select code
    mycode = Code.query(name='Espresso-4.2')   #gets code object
    mycomputer = Computer.query(name='titan')
    
    #select structure - this is a structured object
    mystruc = Struc.find(natoms__gte = 6.0, atoms__contains = 'Li') #gets struc object based on attributes, probably will be hard to map using ORM   
    mystruc = Struc.query(attr__key = 'natoms', attr__key__gte = 6.0) # with current node library
    
    print mystruc.atoms
    mystruc.set_cell([[1,0,0],[0,1,0],[0,0,1]])  #should be able to inherit from multiple classes like ase
    struclist = Struc.filter(child__type__startswith = 'calculation', child__attr__key = 'energy', child__attr__fval__lte = 10.4)
    mystruc = struclist[0].copy()  # create a copy to be modified - this should set up a link with label 'copy'
    mystruc.junk = 55   # should be able to use attributes only for coding, not to be saved
    mystruc.attr.tag = 'something'  # set meta using attributes - to be saved
    mystruc.store()
    
    #create input file data object, without having to write plugins. This reduces user barrier and allows scripting using parameters.
    myinput = Inputfile.create() # a subclass of Data with certain methods like 'template'
    myinput.input_template = '''
        &control
    calculation = {{ CALCTYPE }},
    restart_mode = from_scratch
    nstep = NSTEP
    dt = 100.0
    tstress = .true.
    wf_collect = .true.
    forc_conv_thr = 5.0d-3,
    '''
    myinput.CALCTYPE = 'relax'
    myinput.attr.NSTEP = 5
    #both temporary and persistant attributes should be substituted using templates
    
    myjobparams = Jobparams.create() # a subclass of Data with a preset schema
    
    #set params for job execution
    mycalc = Relaxation.create()
    mycalc.attrs.add({'NPROC' : 32, 'NPOOL' : 1, 'CALCTYPE' : 'md', 'RUNTIME' : '1:00:00'})  # add or modify job attributes
    
    mycalc.NODES = 4   # only a temporary object property
    mycalc.attr.NPROC = 8 * mycalc.NODES  #example way of defining the attribute
    mycalc.store()  #State = initiated
    # params are validated based on expected schema at the store time
    
    #connect objects
    mycalc.set_input)
    myinput.set_destination(mycalc)
    
    mycalc.submit()
    # execution manager loads plugins and does its thing
    


def AdvancedWorkflow():
    
    struclist = Struc.filter(child__type__startswith = 'calculation', child__attr__key = 'energy', child__attr__fval__lte = 10.4)


def Observing():


def RestartWorkflow():



def QueryWorkflow():

    

def Queries():
    '''Enumerate the most important user queries.'''
    
    # find a structure
    
    mystruc = Struc.filter(attr__key = 'group', attr__ival = 230).filter(attr__key)
    mystruc = Struc.filterattr({'group': 230, })
    #filter charge density data that comes from calculations that use Li.UPF and LiCl
    #This should only look for objects of type 'node.data.charge'
    
    results = Charge_density.filter().filter
    
    #would be better to do
    results = Data.
    
