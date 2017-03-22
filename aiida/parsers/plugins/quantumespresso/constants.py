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
Physical or mathematical constants. 
Since every code has its own conversion units, this module defines what
QE understands as for an eV or other quantities.
Whenever possible, we try to use the constants defined in
:py:mod:aiida.common.constants:, but if some constants are slightly different
among different codes (e.g., different standard definition), we define 
the constants in this file.
"""


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

# From the definition of Quantum ESPRESSO, conversion from atomic mass
# units to Rydberg units:
#  REAL(DP), PARAMETER :: AMU_SI           = 1.660538782E-27_DP  ! Kg
#  REAL(DP), PARAMETER :: ELECTRONMASS_SI  = 9.10938215E-31_DP   ! Kg
#  REAL(DP), PARAMETER :: AMU_AU           = AMU_SI / ELECTRONMASS_SI
#  REAL(DP), PARAMETER :: AMU_RY           = AMU_AU / 2.0_DP
amu_Ry = 911.4442421323

