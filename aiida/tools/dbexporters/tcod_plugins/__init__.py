# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.4.1"

class BaseTcodtranslator(object):
    """
    Base translator from calculation-specific output parameters to TCOD CIF
    dictionary tags.
    """
    _plugin_type_string = None

    @classmethod
    def get_software_package(cls,parameters,**kwargs):
        """
        Returns the package or program name that was used to produce
        the structure. Only package or program name should be used,
        e.g. 'VASP', 'psi3', 'Abinit', etc.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_software_package_version(cls,parameters,**kwargs):
        """
        Returns software package version used to compute and produce
        the computed structure file. Only version designator should be
        used, e.g. '3.4.0', '2.1rc3'.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_total_energy(cls,parameters,**kwargs):
        """
        Returns the total energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_one_electron_energy(cls,parameters,**kwargs):
        """
        Returns one electron energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_exchange_correlation_energy(cls,parameters,**kwargs):
        """
        Returns exchange correlation (XC) energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_ewald_energy(cls,parameters,**kwargs):
        """
        Returns Ewald energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_hartree_energy(cls,parameters,**kwargs):
        """
        Returns Hartree energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_fermi_energy(cls,parameters,**kwargs):
        """
        Returns Fermi energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_number_of_electrons(cls,parameters,**kwargs):
        """
        Returns the number of electrons.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_computation_wallclock_time(cls,parameters,**kwargs):
        """
        Returns the computation wallclock time in seconds.
        """
        raise NotImplementedError("not implemented in base class")
