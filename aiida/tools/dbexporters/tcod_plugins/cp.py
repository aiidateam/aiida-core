# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

class CpTcodtranslator(BaseTcodtranslator):
    """
    Quantum ESPRESSO's CP-specific input and output parameter translator
    to TCOD CIF dictionary tags.
    """
    _plugin_type_string = "quantumespresso.cp.CpCalculation"

    @classmethod
    def get_software_package(cls,calc,**kwargs):
        """
        Returns the package or program name that was used to produce
        the structure. Only package or program name should be used,
        e.g. 'VASP', 'psi3', 'Abinit', etc.
        """
        return 'Quantum ESPRESSO'

    @classmethod
    def get_number_of_electrons(cls,calc,**kwargs):
        """
        Returns the number of electrons.
        """
        parameters = calc.out.output_parameters
        if 'number_of_electrons' not in parameters.attrs():
            return None
        return parameters.get_attr('number_of_electrons')

    @classmethod
    def get_computation_wallclock_time(cls,calc,**kwargs):
        """
        Returns the computation wallclock time in seconds.
        """
        parameters = calc.out.output_parameters
        if 'wall_time_seconds' not in parameters.attrs():
            return None
        return parameters.get_attr('wall_time_seconds')
