# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

class CpTcodtranslator(BaseTcodtranslator):
    _plugin_type_string = "quantumespresso.cp.CpCalculation"

    @classmethod
    def get_number_of_electrons(cls,parameters,**kwargs):
        """
        Returns the number of electrons.
        """
        if 'number_of_electrons' not in parameters.attrs():
            return None
        return parameters.get_attr('number_of_electrons')

    @classmethod
    def get_computation_wallclock_time(cls,parameters,**kwargs):
        """
        Returns the computation wallclock time in seconds.
        """
        if 'wall_time_seconds' not in parameters.attrs():
            return None
        return parameters.get_attr('wall_time_seconds')
