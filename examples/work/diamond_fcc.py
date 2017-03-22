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

import ase
from aiida.work.run import async
from aiida.orm import DataFactory
from aiida.orm.data.base import Float, Str
from aiida.work.run import async
from aiida.work.defaults import registry
from aiida.work.util import ProcessStack
from aiida.work.workfunction import workfunction
from examples.work.common import run_scf


@workfunction
def create_diamond_fcc(element, alat):
    """
    Workfunction to create a diamond crystal structure with a given element.

    :param element: The element to create the structure with.
    :return: The structure.
    """
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
    """
    Workfunction to rescale a structure

    :param structure: An AiiDA structure to rescale
    :param scale: The scale factor
    :return: The rescaled structure
    """
    the_ase = structure.get_ase()
    new_ase = the_ase.copy()
    new_ase.set_cell(the_ase.get_cell() * float(scale), scale_atoms=True)
    new_structure = DataFactory('structure')(ase=new_ase)
    return new_structure


@workfunction
def calc_energies(codename, pseudo_family):
    print("Calculating energies, my pk is '{}'".format(
        ProcessStack.get_active_process_id()))

    futures = {}
    for element, scale in [("Si", 5.41)]:
        structure = create_diamond_fcc(Str(element), Float(1.))
        structure = rescale(structure, Float(scale))
        print("Running {} scf calculation.".format(element))
        futures[element] = async(run_scf, structure, codename, pseudo_family)

    print("Waiting for calculations to finish.")
    outs = {element: Float(future.result()['output_parameters'].dict.energy)
            for element, future in futures.iteritems()}
    print("Calculations finished.")
    return outs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Energy calculation example.')
    parser.add_argument('--pseudo', type=str, dest='pseudo', required=True,
                        help='The pseudopotential family')
    parser.add_argument('--code', type=str, dest='code', required=True,
                        help='The codename to use')

    args = parser.parse_args()
    print(calc_energies(Str(args.code), Str(args.pseudo)))
