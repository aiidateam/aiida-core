# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida import orm
from aiida.orm.utils import CalculationFactory


def generate_scf_input_params(structure, codename, pseudo_family):
    # The inputs
    pw_calculation_class = CalculationFactory("quantumespresso.pw")
    inputs = pw_calculation_class.process().get_builder()

    # The structure
    inputs.structure = structure

    inputs.code = orm.Code.get_from_string(codename.value)
    inputs.options.resources = {"num_machines": 1}
    inputs.options.max_wallclock_seconds = 30 * 60

    # Kpoints
    KpointsData = orm.DataFactory("array.kpoints")
    kpoints = KpointsData()
    kpoints_mesh = 2
    kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])
    inputs.kpoints = kpoints

    # Calculation parameters
    parameters_dict = {
        "CONTROL": {"calculation": "scf", "tstress": True, "tprnfor": True, },
        "SYSTEM": {"ecutwfc": 30., "ecutrho": 200., },
        "ELECTRONS": {"conv_thr": 1.e-6, }
    }
    orm.data.ParameterData = orm.DataFactory("parameter")
    inputs.parameters = orm.data.ParameterData(dict=parameters_dict)

    # Pseudopotentials
    inputs.pseudo = get_pseudos(structure, str(pseudo_family))

    return inputs


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

    for kindname, pseudo in kind_pseudo_dict.items():
        pseudo_dict[pseudo.pk] = pseudo
        pseudo_species[pseudo.pk].append(kindname)

    pseudos = {}
    for pseudo_pk in pseudo_dict:
        pseudo = pseudo_dict[pseudo_pk]
        kinds = pseudo_species[pseudo_pk]
        for kind in kinds:
            pseudos[kind] = pseudo

    return pseudos
