# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.4.1"

from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator

class PwTcodtranslator(BaseTcodtranslator):
    """
    Quantum ESPRESSO's PW-specific input and output parameter translator
    to TCOD CIF dictionary tags.
    """
    _plugin_type_string = "quantumespresso.pw.PwCalculation"

    @classmethod
    def get_software_package(cls,calc,**kwargs):
        """
        Returns the package or program name that was used to produce
        the structure. Only package or program name should be used,
        e.g. 'VASP', 'psi3', 'Abinit', etc.
        """
        return 'Quantum ESPRESSO'

    @classmethod
    def _get_pw_energy_value(cls,calc,energy_type,**kwargs):
        """
        Returns the energy of defined type in eV.
        """
        parameters = calc.out.output_parameters
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
    def _get_atom_site_residual_force_Cartesian(cls,calc,index,**kwargs):
        """
        Returns an array with residual force components along the Cartesian
        axes.
        """
        try:
            array = calc.out.output_array
            return [x[index] for x in array.get_array('forces').tolist()]
        except KeyError:
            return None
        
    @classmethod
    def get_total_energy(cls,calc,**kwargs):
        """
        Returns the total energy in eV.
        """
        return cls._get_pw_energy_value(calc,'energy')

    @classmethod
    def get_one_electron_energy(cls,calc,**kwargs):
        """
        Returns one electron energy in eV.
        """
        return cls._get_pw_energy_value(calc,'energy_one_electron')

    @classmethod
    def get_exchange_correlation_energy(cls,calc,**kwargs):
        """
        Returns exchange correlation (XC) energy in eV.
        """
        return cls._get_pw_energy_value(calc,'energy_xc')

    @classmethod
    def get_ewald_energy(cls,calc,**kwargs):
        """
        Returns Ewald energy in eV.
        """
        return cls._get_pw_energy_value(calc,'energy_ewald')

    @classmethod
    def get_hartree_energy(cls,calc,**kwargs):
        """
        Returns Hartree energy in eV.
        """
        return cls._get_pw_energy_value(calc,'energy_hartree')

    @classmethod
    def get_fermi_energy(cls,calc,**kwargs):
        """
        Returns Fermi energy in eV.
        """
        return cls._get_pw_energy_value(calc,'fermi_energy')

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

    @classmethod
    def get_atom_site_residual_force_Cartesian_x(cls,calc,**kwargs):
        """
        Returns a list of x components for Cartesian coordinates of
        residual force for atom. The list order MUST be the same as in
        the resulting structure.
        """
        return cls._get_atom_site_residual_force_Cartesian(calc,0)

    @classmethod
    def get_atom_site_residual_force_Cartesian_y(cls,calc,**kwargs):
        """
        Returns a list of y components for Cartesian coordinates of
        residual force for atom. The list order MUST be the same as in
        the resulting structure.
        """
        return cls._get_atom_site_residual_force_Cartesian(calc,1)

    @classmethod
    def get_atom_site_residual_force_Cartesian_z(cls,calc,**kwargs):
        """
        Returns a list of z components for Cartesian coordinates of
        residual force for atom. The list order MUST be the same as in
        the resulting structure.
        """
        return cls._get_atom_site_residual_force_Cartesian(calc,2)
