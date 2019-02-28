# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module provides import functionality to all data types
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import io

from aiida.cmdline.utils import echo


def data_import_xyz(filename, **kwargs):
    """
    Imports an XYZ-file.
    """
    from os.path import abspath
    from aiida.orm import StructureData

    vacuum_addition = kwargs.pop('vacuum_addition')
    vacuum_factor = kwargs.pop('vacuum_factor')
    pbc = [bool(i) for i in kwargs.pop('pbc')]
    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing XYZ-structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)
    with io.open(filepath, encoding='utf8') as fobj:
        xyz_txt = fobj.read()
    new_structure = StructureData()
    # pylint: disable=protected-access
    try:
        new_structure._parse_xyz(xyz_txt)
        new_structure._adjust_default_cell(vacuum_addition=vacuum_addition, vacuum_factor=vacuum_factor, pbc=pbc)

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo('  Succesfully imported structure {}, '
                  '(PK = {})'.format(new_structure.get_formula(), new_structure.pk))

    except ValueError as err:
        echo.echo_critical(err)


def data_import_pwi(filename, **kwargs):
    """
    Imports a structure from a quantumespresso input file.
    """
    from os.path import abspath
    try:
        from qe_tools.parsers.pwinputparser import PwInputFile
    except ImportError:
        echo.echo_critical("You have not installed the package qe-tools. \n"
                           "You can install it with: pip install qe-tools")

    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)

    try:
        inputparser = PwInputFile(filepath)
        new_structure = inputparser.get_structuredata()

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo('  Succesfully imported structure {}, '
                  '(PK = {})'.format(new_structure.get_formula(), new_structure.pk))

    except ValueError as err:
        echo.echo_critical(err)


def data_import_ase(filename, **kwargs):
    """
    Imports a structure in a number of formats using the ASE routines.
    """
    from os.path import abspath
    from aiida.orm import StructureData

    try:
        import ase.io
    except ImportError:
        echo.echo_critical("You have not installed the package ase. \n" "You can install it with: pip install ase")

    store = kwargs.pop('store')
    view_in_ase = kwargs.pop('view')

    echo.echo('importing structure from: \n  {}'.format(abspath(filename)))
    filepath = abspath(filename)

    try:
        asecell = ase.io.read(filepath)
        new_structure = StructureData(ase=asecell)

        if store:
            new_structure.store()
        if view_in_ase:
            from ase.visualize import view
            view(new_structure.get_ase())
        echo.echo('  Succesfully imported structure {}, '
                  '(PK = {})'.format(new_structure.get_formula(), new_structure.pk))

    except ValueError as err:
        echo.echo_critical(err)
