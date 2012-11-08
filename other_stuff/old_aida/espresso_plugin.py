from newaidajob import *
import StringIO 

repo_patterns = ['*.in','*.out','*.pkl','*.py']

def Write_inputs(C):  
    # write qe input file. This is done on the server in calc repo dir
    # make substitutions in the template with defined attributes

    location_perm = calc_repo_path + str(C.id)
    location_temp = C.computer.scratch_location + str(C.id)
    cluster = C.computer.hostname
    
    in_file = "espresso." + C.type.title + ".in"
    out_file = "espresso." + C.type.title + ".out"
#    params = Load_params(C)
#    input_template = params['input_template']
    input_template = C.params.input_template

    input_pot_template = '''
{% block PSEUDOS %}
ATOMIC_SPECIES
{% for pot in potentials %}
  {{ pot.element.symbol }} {{ pot.element.mass }}  {{ pot.title }}
{% endfor %}
{% endblock %}'''

    input_struc_template = '''
{% block CELL %}
CELL_PARAMETERS (alat)
{% for vec in struc.cell %}
   {{vec.0}} {{vec.1}} {{vec.2}}
{% endfor %}
{% endblock %}   
{% block ATOMS %}
ATOMIC_POSITIONS (angstrom) 
{% for atom in struc.atoms %}
   {{ atom.symbol }} {{atom.position.0}} {{atom.position.1}} {{ atom.position.2}}
{% endfor %}
{% endblock %}'''

    S = C.input_structures.all()[0]   #fix this later using templates
    S = Get_structure(S.id)
    C.params.NATOMS = S.num_of_atoms
    C.params.NTYP = S.ntype
    
    #print C.params.__dict__
    in_text = Template(input_template).render(Context(C.params.__dict__))
    context = Context({'potentials':C.potentials.all()})
    pot_text = Template(input_pot_template).render(context)
#    print struc_text

    serial = json.loads(S.serial)
    struc_text = StringIO.StringIO()
    struc_text.write('CELL_PARAMETERS (alat) \n')
    for i in range(3):
        struc_text.write(' %s  %s  %s \n' % tuple(serial['cell'][i]))
    struc_text.write('\nATOMIC_POSITIONS (crystal) \n')
    for atom in serial['atoms']:
        struc_text.write(' %s  ' % atom['symbol'])
        struc_text.write('%s  %s  %s  \n' % tuple(atom['position']))        
    s_text = struc_text.getvalue()
    struc_text.close()

    all_text = in_text + pot_text + s_text
    #print all_text
    f = open(in_file, 'w')    
    f.write(all_text)
    f.close()

    #params = Load_params(C)
    #params['in_file'] = in_file
    #params['out_file'] = out_file
    C.params.in_file = in_file
    C.params.out_file = out_file
    C.params.binary = C.code.location

    command = '''mpirun -r ssh -n {{NPROC}} -npool {{NPOOL}} {{binary}} < {{in_file}} > {{out_file}}'''
    exec_command = Template(command).render(Context(C.params.__dict__))
    exec_file = 'run.exe'
    f = open(exec_file, 'w')    
    f.write(exec_command)
    f.close()
    run_command(localhost, 'chmod ug+rx %s' % (exec_file))

    for file in [in_file, exec_file]:
#        print 'scp -p %s %s:%s/' % (file, cluster, location_temp)
        run_command(localhost, 'scp -p %s %s:%s' % (file, cluster, location_temp))

    # serialize the entire input text with the calculation

    #    attrs = json.loads(C.attributes)
    attrs = {}
    attrs['inputfiles']={in_file: in_text, exec_file: exec_command}
    attrs['parameters']=C.params.__dict__
    C.attributes = json.dumps(attrs)
    #print C.attributes
    C.save()

    
    #===========================================================================
    # if calc.TYPE in ['scf','relax','vc-relax', 'md', 'vc-md']:
    #    # writes QE format CELL and ATOMIC_POSITIONS (crystal) assuming ibrav=0 and a=1 for Angstrom units
    #    f.write('CELL_PARAMETERS (alat) \n')
    #    for i in range(3):
    #        f.write(' %s  %s  %s \n' % tuple(struc.cell[i]))
    #    f.write('\n')
    #    f.write('ATOMIC_POSITIONS (crystal) \n')
    #    for iatom, atom in enumerate(struc):
    #        f.write(' %s  ' % atom.symbol)
    #       #f.write('%s  %s  %s  \n' % tuple(atom.position))
    #        f.write('%s  %s  %s  \n' % tuple(struc.get_scaled_positions()[iatom]))        
    #===========================================================================

    

def Repository_copy(C):
    # Copy important small files to repository.
    # This is run on the cluster
    location_perm = calc_repo_path + '/' + str(C.id)        
    #flatten list of lists of filenames
    repo_files = sum([glob.glob(fname) for fname in repo_patterns],[])
    for file in repo_files:
        run_command('scp -p %s %s:%s' % (file, server, location_perm))

