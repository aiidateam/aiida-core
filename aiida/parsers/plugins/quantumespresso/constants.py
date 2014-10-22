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

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

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
