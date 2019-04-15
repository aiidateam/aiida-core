# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

if not is_dbenv_loaded():
    load_dbenv()

import ase
from aiida.workflows2.run import async
from aiida.orm import DataFactory
from aiida.workflows2.db_types import Float, Str
from aiida.workflows2.wf import wf
from aiida.workflows2.run import async
from examples.workflows2.common import run_scf
from aiida.workflows2.defaults import registry

@wf
def create_diamond_fcc(element,alat):
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


@wf
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


@wf
def calc_energies(codename, pseudo_family):
    print("Calculating energies, my pk is '{}'".format(registry.current_pid))

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
