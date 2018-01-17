# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import numpy as np
import matplotlib.pyplot as plt
from aiida.orm.code import Code
from aiida.orm.utils import DataFactory
from aiida.orm.data.base import *
from aiida.work import *


@workfunction
def create_diamond_fcc(element, alat):
    from numpy import array
    the_cell = array([[0., 0.5, 0.5],
                      [0.5, 0., 0.5],
                      [0.5, 0.5, 0.]]) * alat
    StructureData = DataFactory("structure")
    structure = StructureData(cell=the_cell)
    structure.append_atom(position=(0., 0., 0.), symbols=str(element))
    structure.append_atom(position=(0.25 * alat, 0.25 * alat, 0.25 * alat), symbols=str(element))
    return structure


@workfunction
def rescale(structure, scale):
    the_ase = structure.get_ase()
    new_ase = the_ase.copy()
    new_ase.set_cell(the_ase.get_cell() * float(scale), scale_atoms=True)
    new_structure = DataFactory('structure')(ase=new_ase)
    return new_structure


def get_pseudos(structure, family_name):
    from collections import defaultdict
    from aiida.orm.data.upf import get_pseudos_from_structure

    # A dict {kind_name: pseudo_object}
    kind_pseudo_dict = get_pseudos_from_structure(structure, family_name)

    # We have to group the species by pseudo, I use the pseudo PK
    # pseudo_dict will just map PK->pseudo_object
    pseudo_dict = {}
    # Will contain a list of all species of the pseudo with given PK
    pseudo_species = defaultdict(list)

    for kindname, pseudo in kind_pseudo_dict.iteritems():
        pseudo_dict[pseudo.pk] = pseudo
        pseudo_species[pseudo.pk].append(kindname)

    pseudos = {}
    for pseudo_pk in pseudo_dict:
        pseudo = pseudo_dict[pseudo_pk]
        kinds = pseudo_species[pseudo_pk]
        for kind in kinds:
            pseudos[kind] = pseudo

    return pseudos


def generate_scf_input_params(structure, codename, pseudo_family):
    # The inputs
    inputs = PwCalculation.process().get_inputs_template()

    # The structure
    inputs.structure = structure

    inputs.code = Code.get_from_string(codename.value)
    inputs._options.resources = {"num_machines": 1}
    inputs._options.max_wallclock_seconds = 30 * 60

    # Kpoints
    KpointsData = DataFactory("array.kpoints")
    kpoints = KpointsData()
    kpoints_mesh = 2
    kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
    inputs.kpoints = kpoints

    # Calculation parameters
    parameters_dict = {
        "CONTROL": {"calculation": "scf",
                    "tstress": True,  # Important that this stays to get stress
                    "tprnfor": True, },
        "SYSTEM": {"ecutwfc": 30.,
                   "ecutrho": 200., },
        "ELECTRONS": {"conv_thr": 1.e-6, }
    }
    ParameterData = DataFactory("parameter")
    inputs.parameters = ParameterData(dict=parameters_dict)

    # Pseudopotentials
    inputs.pseudo = get_pseudos(structure, str(pseudo_family))

    return inputs


from aiida.orm.data.base import Str
from aiida.orm.utils import CalculationFactory

PwCalculation = CalculationFactory('quantumespresso.pw')
PwProcess = PwCalculation.process()


@workfunction
def eos(structure, codename, pseudo_family):
    scales = (0.96, 0.98, 0.99, 1.0, 1.02, 1.04)
    # Plotting
    fig, ax = plt.subplots()
    ax.set_xlim([scales[0], scales[-1]])
    ax.set_xlabel(u"Cell length [Å]")
    ax.set_ylabel(u"Total energy [eV]")
    line, = ax.plot([], [])

    # Loop over calculating energies at given scales
    energies = []
    for i, s in enumerate(scales):
        rescaled = rescale(structure, Float(s))
        inputs = generate_scf_input_params(rescaled, codename, pseudo_family)
        outputs = run(PwProcess, **inputs)
        energy = outputs['output_parameters'].dict.energy
        energies.append(energy)

        # Plot
        line.set_xdata(scales[0:len(energies)])
        line.set_ydata(energies)
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()


structure = create_diamond_fcc(Str('C'), Float(3.65))
codename = Str('pw.x@localhost')
pseudo_family = Str('SSSP_eff_PBE_0.7')
eos(structure, codename, pseudo_family)
