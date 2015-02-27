# -*- coding: utf-8 -*-
"""
Physical or mathematical constants. 
Since every code has its own conversion units, this module defines what
QE understands as for an eV or other quantities.
Whenever possible, we try to use the constants defined in
:py:mod:aiida.common.constants:, but if some constants are slightly different
among different codes (e.g., different standard definition), we define 
the constants in this file.
"""

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Nicolas Mounet"

from aiida.common.constants import (
    ang_to_m,
    bohr_si,
    bohr_to_ang,
    hartree_to_ev,
    invcm_to_THz,
    ry_si,
    ry_to_ev,
    timeau_to_sec,
    )
