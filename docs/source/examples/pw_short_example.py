#!/usr/bin/env python
from aiida.common.utils import load_django
load_django()
from aiida.orm import Code
from aiida.orm import CalculationFactory, DataFactory

ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')

codename = 'your_pw.x'

pseudo_family = 'lda_pslib'

code = Code.get(codename)
computer = code.get_remote_computer()

# BaTiO3 cubic structure
alat = 4. # angstrom
cell = [[alat, 0., 0.,],
        [0., alat, 0.,],
        [0., 0., alat,],
       ]
s = StructureData(cell=cell)
s.append_atom(position=(0.,0.,0.),symbols='Ba')
s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols='Ti')
s.append_atom(position=(alat/2.,alat/2.,0.),symbols='O')
s.append_atom(position=(alat/2.,0.,alat/2.),symbols='O')
s.append_atom(position=(0.,alat/2.,alat/2.),symbols='O')
s.store()

parameters = ParameterData(dict={
            'CONTROL': {
                'calculation': 'scf',
                'restart_mode': 'from_scratch',
                'wf_collect': True,
                },
            'SYSTEM': {
                'ecutwfc': 30.,
                'ecutrho': 240.,
                },
            'ELECTRONS': {
                'conv_thr': 1.e-6,
                }}).store()

kpoints = ParameterData(dict={
                'type': 'automatic',
                'points': [4, 4, 4, 0, 0, 0],
                }).store()

QECalc = CalculationFactory('quantumespresso.pw')
calc = QECalc(computer=computer)
calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 16})
calc.store()

calc.use_structure(s)
calc.use_code(code)
calc.use_parameters(parameters)
calc.use_pseudos_from_family(pseudo_family)
calc.use_kpoints(kpoints)

calc.submit()
