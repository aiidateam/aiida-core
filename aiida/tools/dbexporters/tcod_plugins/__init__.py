# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


class BaseTcodtranslator(object):
    """
    Base translator from calculation-specific input and output parameters
    to TCOD CIF dictionary tags.
    """
    _plugin_type_string = None

    @classmethod
    def get_software_package(cls,calc,**kwargs):
        """
        Returns the package or program name that was used to produce
        the structure. Only package or program name should be used,
        e.g. 'VASP', 'psi3', 'Abinit', etc.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_software_package_version(cls,calc,**kwargs):
        """
        Returns software package version used to compute and produce
        the computed structure file. Only version designator should be
        used, e.g. '3.4.0', '2.1rc3'.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_software_package_compilation_timestamp(cls,calc,**kwargs):
        """
        Returns the timestamp of package/program compilation in ISO 8601
        format.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_software_executable_path(cls,calc,**kwargs):
        """
        Returns the file-system path to the executable that was run for
        this computation.
        """
        try:
            code = calc.inp.code
            if not code.is_local():
                return code.get_attr('remote_exec_path')
        except Exception:
            return None
        return None

    @classmethod
    def get_total_energy(cls,calc,**kwargs):
        """
        Returns the total energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_one_electron_energy(cls,calc,**kwargs):
        """
        Returns one electron energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_exchange_correlation_energy(cls,calc,**kwargs):
        """
        Returns exchange correlation (XC) energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_ewald_energy(cls,calc,**kwargs):
        """
        Returns Ewald energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_hartree_energy(cls,calc,**kwargs):
        """
        Returns Hartree energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_fermi_energy(cls,calc,**kwargs):
        """
        Returns Fermi energy in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_number_of_electrons(cls,calc,**kwargs):
        """
        Returns the number of electrons.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_computation_wallclock_time(cls,calc,**kwargs):
        """
        Returns the computation wallclock time in seconds.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_atom_type_symbol(cls,calc,**kwargs):
        """
        Returns a list of atom types. Each atom site MUST occur only
        once in this list. List MUST be sorted.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_atom_type_valence_configuration(cls,calc,**kwargs):
        """
        Returns valence configuration of each atom type. The list order
        MUST be the same as of get_atom_type_symbol().
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_atom_type_basisset(cls,calc,**kwargs):
        """
        Returns a list of basisset names for each atom type. The list
        order MUST be the same as of get_atom_type_symbol().
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_atom_site_residual_force_Cartesian_x(cls,calc,**kwargs):
        """
        Returns a list of x components for Cartesian coordinates of
        residual force for atom. The list order MUST be the same as in
        the resulting structure.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_atom_site_residual_force_Cartesian_y(cls,calc,**kwargs):
        """
        Returns a list of y components for Cartesian coordinates of
        residual force for atom. The list order MUST be the same as in
        the resulting structure.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_atom_site_residual_force_Cartesian_z(cls,calc,**kwargs):
        """
        Returns a list of z components for Cartesian coordinates of
        residual force for atom. The list order MUST be the same as in
        the resulting structure.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_BZ_integration_grid_X(cls,calc,**kwargs):
        """
        Returns a number of points in the Brillouin zone along reciprocal
        lattice vector X.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_BZ_integration_grid_Y(cls,calc,**kwargs):
        """
        Returns a number of points in the Brillouin zone along reciprocal
        lattice vector Y.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_BZ_integration_grid_Z(cls,calc,**kwargs):
        """
        Returns a number of points in the Brillouin zone along reciprocal
        lattice vector Z.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_BZ_integration_grid_shift_X(cls,calc,**kwargs):
        """
        Returns the shift of the Brillouin zone points along reciprocal
        lattice vector X.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_BZ_integration_grid_shift_Y(cls,calc,**kwargs):
        """
        Returns the shift of the Brillouin zone points along reciprocal
        lattice vector Y.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_BZ_integration_grid_shift_Z(cls,calc,**kwargs):
        """
        Returns the shift of the Brillouin zone points along reciprocal
        lattice vector Z.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_integration_smearing_method(cls,calc,**kwargs):
        """
        Returns the smearing method name as string.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_integration_smearing_method_other(cls,calc,**kwargs):
        """
        Returns the smearing method name as string if the name is different
        from specified in cif_dft.dic.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_integration_Methfessel_Paxton_order(cls,calc,**kwargs):
        """
        Returns the order of Methfessel-Paxton approximation if used.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_kinetic_energy_cutoff_wavefunctions(cls,calc,**kwargs):
        """
        Returns kinetic energy cutoff for wavefunctions in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_kinetic_energy_cutoff_charge_density(cls,calc,**kwargs):
        """
        Returns kinetic energy cutoff for charge density in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_kinetic_energy_cutoff_EEX(cls,calc,**kwargs):
        """
        Returns kinetic energy cutoff for exact exchange (EEX)
        operator in eV.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_pseudopotential_atom_type(cls,calc,**kwargs):
        """
        Returns a list of atom types. Each atom type MUST occur only
        once in this list. List MUST be sorted.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_pseudopotential_type(cls,calc,**kwargs):
        """
        Returns a list of pseudopotential types. List MUST be sorted
        by atom types.
        """
        raise NotImplementedError("not implemented in base class")

    @classmethod
    def get_pseudopotential_type_other_name(cls,calc,**kwargs):
        """
        Returns a list of other pseudopotential type names. List MUST be
        sorted by atom types.
        """
        raise NotImplementedError("not implemented in base class")
