# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import click
import logging
from aiida.orm import DataFactory
from aiida.orm.code import Code
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.work.run import submit, run


def get_pseudos(structure, family_name):
    """
    Set the pseudo to use for all atomic kinds, picking pseudos from the
    family with name family_name.

    :note: The structure must already be set.

    :param family_name: the name of the group containing the pseudos
    """
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


@click.command()
@click.option('--pseudo', type=str, required=True, help='The pseudopotential family')
@click.option('--code', type=str, required=True, help='The codename to use')
@click.option('-v', '--verbose', count=True)
def run_si_scf(code, pseudo, verbose):
    if verbose is not None:
        if verbose == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG
        FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
        logging.basicConfig(level=level, format=FORMAT)

    pw_calc = PwCalculation.process()
    inputs = pw_calc.get_inputs_template()

    inputs.code = Code.get_from_string(code)
    # calc.label = "PW test"
    # calc.description = "My first AiiDA calculation of Silicon with Quantum ESPRESSO"
    inputs._options.resources = {"num_machines": 1}
    inputs._options.max_wallclock_seconds = 30 * 60

    # The structure
    alat = 5.4
    the_cell = [[alat / 2., alat / 2., 0], [alat / 2., 0, alat / 2.],
                [0, alat / 2., alat / 2.]]
    StructureData = DataFactory("structure")
    structure = StructureData(cell=the_cell)
    structure.append_atom(position=(0., 0., 0.), symbols="Si")
    structure.append_atom(position=(alat / 4., alat / 4., alat / 4.), symbols="Si")
    inputs.structure = structure

    # Kpoints
    KpointsData = DataFactory("array.kpoints")
    kpoints = KpointsData()
    kpoints_mesh = 2
    kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
    inputs.kpoints = kpoints

    # Calculation parameters
    parameters_dict = {
        "CONTROL": {"calculation": "scf",
                    "tstress": True,
                    "tprnfor": True, },
        "SYSTEM": {"ecutwfc": 30.,
                   "ecutrho": 200., },
        "ELECTRONS": {"conv_thr": 1.e-6, }
    }
    ParameterData = DataFactory("parameter")
    inputs.parameters = ParameterData(dict=parameters_dict)

    # Pseudopotentials
    inputs.pseudo = get_pseudos(structure, pseudo)

    # calc.set_extra("element", "Si")
    # calc.submit()
    # submit(JobCalc, **inputs)
    run(pw_calc, **inputs)


if __name__ == "__main__":
    run_si_scf()
