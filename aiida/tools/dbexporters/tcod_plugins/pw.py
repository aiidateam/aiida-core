# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

class PwTcodtranslator(BaseTcodtranslator):
    """
    Quantum ESPRESSO's PW-specific output parameter translator to TCOD
    CIF dictionary tags.
    """
    _plugin_type_string = "quantumespresso.pw.PwCalculation"

    @classmethod
    def _get_pw_energy_value(cls,parameters,energy_type,**kwargs):
        """
        Returns the energy of defined type in eV.
        """
        if energy_type not in parameters.attrs():
            return None
        if energy_type + '_units' not in parameters.attrs():
            raise ValueError("energy units for {} are "
                             "unknown".format(energy_type))
        if parameters.get_attr(energy_type + '_units') != 'eV':
            raise ValueError("energy units for {} are {} "
                             "instead of eV -- unit "
                             "conversion is not possible "
                             "yet".format(energy_type,
                                          parameters.get_attr(energy_type + '_units')))
        return parameters.get_attr(energy_type)
        
    @classmethod
    def get_total_energy(cls,parameters,**kwargs):
        """
        Returns the total energy in eV.
        """
        return cls._get_pw_energy_value(parameters,'energy')

    @classmethod
    def get_one_electron_energy(cls,parameters,**kwargs):
        """
        Returns one electron energy in eV.
        """
        return cls._get_pw_energy_value(parameters,'energy_one_electron')

    @classmethod
    def get_exchange_correlation_energy(cls,parameters,**kwargs):
        """
        Returns one exchange correlation (XC) energy in eV.
        """
        return cls._get_pw_energy_value(parameters,'energy_xc')

    @classmethod
    def get_ewald_energy(cls,parameters,**kwargs):
        """
        Returns Ewald energy in eV.
        """
        return cls._get_pw_energy_value(parameters,'energy_ewald')

    @classmethod
    def get_hartree_energy(cls,parameters,**kwargs):
        """
        Returns Hartree energy in eV.
        """
        return cls._get_pw_energy_value(parameters,'energy_hartree')

    @classmethod
    def get_fermi_energy(cls,parameters,**kwargs):
        """
        Returns Fermi energy in eV.
        """
        return cls._get_pw_energy_value(parameters,'fermi_energy')

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
