##!/software/python/python27

from ase import *
from newaidajob import *

class params:
    #Parameters that are code-independent, non-numeric
    CODE = 'Espresso-4.2.1-pw.x'
    PROJECT = 'Garnets'
    COMPUTER = 'palpc170'
    NPROC = 32
    NPOOL = 1
    CALCTYPE = 'md'
    RUNTIME = '1:00:00'
    QUEUE = 'all.q@@oldcluster'
    COMMENT = "MD run of Li7 LLZ (cubic config) with Al on oct site"
    QEXCL = True
    USEDB = True

    #Code-specific parameters
    RESTART_MODE = 'from_scratch'
    KPTS = 'gamma'
    ECUTWFC = 20
    ECUTRHO = 160
    TEMPERATURE = 400
    POTENTIALS = ['La.pbe-nsp-van.UPF', 'Li.pbe-n-van.UPF', 'Zr.pbe-nsp-van.UPF', 'O.pbe-rrkjus.UPF']
    POTENTIALS = ['Li.pbe-n-van.UPF']

    input_template = """
&control
    calculation = {{ CALCTYPE }},
    restart_mode = {{ RESTART_MODE }}
    nstep = 5
    dt = 100.0
    tstress = .true.
    wf_collect = .true.
    forc_conv_thr = 5.0d-3,      
 /
&system
    ibrav = 0,
    a = 1
    nat = {{ NATOMS }},
    ntyp = {{ NTYP }},
    nosym = .true.
    ecutwfc = {{ ECUTWFC }},
    ecutrho = {{ ECUTRHO }},
    occupations = 'fixed',
 !  smearing='mp', degauss=0.03
 /
&electrons
    diagonalization = 'david',
    mixing_mode = 'plain',
    mixing_beta = 0.1,
    conv_thr =  1.0d-7,
 /
 &ions
    ion_dynamics = 'verlet'
    pot_extrapolation = 'second_order',
    wfc_extrapolation = 'second_order',
    ion_temperature = 'rescaling'
    tempw = {{ TEMPERATURE }}
/
K_POINTS {{ KPTS }}
/
{% block PSEUDOS %}{% endblock %}
{% block CELL %}{% endblock %}
{% block ATOMS %}{% endblock %}
"""

#--------------------- CREATE STRUCTURE and SUBMIT ----------------------

C = Get_calc(params)    

#the structure is saved to db as soon as it is initiated
struc = read_pickle('garnet_prototype.pkl')
S = Get_structure(struc)
S = Link_calc_input_struc(C,S)
Submit(C)

# continue at a different temperature
#runparams2 = runparams
#inputparams2 = inputparams
#inputparams2.RESTART_MODE = 'restart'
#inputarams2.TEMPERATURE = 600
#
#C2 = MyCalc(runpmaram2, inputparam2)
#C2.struc = C.struc
#C2.submit()
