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
Implement subclass for real-space interatomic force constants file from QE-Q2R
"""
from aiida.orm.data.singlefile import SinglefileData
from aiida.parsers.plugins.quantumespresso.constants import bohr_to_ang
import numpy

class ForceconstantsData(SinglefileData):
    """
    Class to handle interatomic force constants from Quantum Espresso - Q2R.
    """

    def set_file(self, filename):
    
        """
        Add a file to the singlefiledata, parse it and set the attributes found
        :param filename: absolute path to the file
        """
        with open(filename,'r') as f:
            lines = f.readlines()
        
        # parse the force constants file
        out_dict, fc, warnings = parse_q2r_force_constants_file(lines,
                                                    also_force_constants=False)
        
        # check the path and add filename attribute
        self.add_path(filename)
        
        # add all other attributes found in the parsed dictionary
        for key in out_dict.keys():
            self._set_attr(key, out_dict[key])
 
    @property
    def number_of_species(self):
        """
        The number of atom species.
        :return: a scalar
        """
        return self.get_attr('number_of_species')

    @property
    def number_of_atoms(self):
        """
        The number of atoms.
        :return: a scalar
        """
        return self.get_attr('number_of_atoms')
        
    @property
    def cell(self):
        """
        The crystal unit cell. Rows are the crystal vectors.
        :return: a 3x3 numpy.array
        """
        return numpy.array(self.get_attr('cell'))
        
    @property
    def atom_list(self):
        """
        List of atoms.
        :return: a list of length-5 tuple (element_name, element_mass_in_amu_ry,
         then 3 coordinates in cartesian & Angstroms)
        """
        return self.get_attr('atom_list')
        
    @property
    def has_done_electric_field(self):
        """
        Flag to indicate if dielectric tensor and effective charges were
        computed.
        :return: a boolean
        """
        return self.get_attr('has_done_electric_field')
        
    @property
    def dielectric_tensor(self):
        """
        The dielectric tensor matrix.
        :return: a 3x3 tuple
        """
        return self.get_attr('dielectric_tensor')
        
    @property
    def effective_charges_eu(self):
        """
        The effective charges for each atom.
        :return: a list of number_of_atoms elements, each being a 3x3 tuple
        """
        return self.get_attr('effective_charges_eu')
        
    @property
    def qpoints_mesh(self):
        """
        The number of q-points in each direction.
        :return: a length-3 tuple
        """
        return tuple(self.get_attr('qpoints_mesh'))
        

def parse_q2r_force_constants_file(lines,also_force_constants=False):
    """
    Parse the real-space interatomic force constants file from QE-Q2R.
    
    :param also_force_constants: True to parse the force constants as well
    
    :return parsed_data: dictionary with the following keywords:
    
    - number_of_species: number of atom species ('ntyp' in QE)
    - number_of_atoms: number of atoms ('nat' in QE)
    - cell: unit cell
    - atom_list: list with, for each atom in the cell, a length-5 
    tuple of the form (element_name, mass_in_amu_ry, then 3 coordinates in 
    cartesian & Angstroms)
    - has_done_electric_field: True if dielectric constants & effective
    charges were computed
    - dielectric_tensor: dielectric constant (3x3 matrix)
    - effective_charges_eu: effective charges (ntyp x 3 x 3 matrix)
    - qpoints_mesh: length-3 tuple with number of qpoints in each dimension
    of the reciprocal lattice
    - force_constants: the real-space force constants: array with 7 
    indices of the kind C(m1,m2,m3,j1,j2,na1,na2) with
        * (m1, m2, m3): the supercell dimentsions
        * (j1, j2): axis of the displacement of the two atoms (from 1 to 3)
        * (na1, na2): atom numbers in the cell.
    - warnings: a list of warnings
    
    :return force_constants: the real-space force constants: array with 7 
    indices, of the kind C(m1,m2,m3,j1,j2,na1,na2) with
        * (m1, m2, m3): the supercell dimensions
        * (j1, j2): axis of the displacement of the two atoms (from 1 to 3)
        * (na1, na2): atom numbers in the cell.
    """
    
    parsed_data = {}
    warnings = []
    
    try:
        # read first line
        current_line = 0
        first_line = lines[current_line].split()
        ntyp = int(first_line[0])
        nat = int(first_line[1])
        ibrav = int(first_line[2])
        celldm = [float(c) for c in first_line[3:]]
        if len(celldm) != 6:
            warnings.append('Wrong length for celldm')
        if ibrav != 0:
            warnings.append("ibrav ({}) is not 0; q-points path for phonon "
                            "dispersion might be wrong".format(ibrav))
        if any([item != 0 for item in celldm[1:]]):
            warnings.append("celldm[1:] are not all zero; only celldm[0] will "
                            "be used")
        
        parsed_data['number_of_species'] = ntyp
        parsed_data['number_of_atoms'] = nat
        #parsed_data['ibrav'] = ibrav
        #parsed_data['celldm'] = celldm
        current_line += 1
        
        # read cell data
        cell = tuple(tuple(float(c)*celldm[0]*bohr_to_ang for c in l.split())
                     for l in lines[current_line:current_line+3])
        parsed_data['cell'] = cell
        current_line += 3
    
        # read atom types and masses
        atom_type_list = []
        for ityp in range(ntyp):
            line = lines[current_line].split("'")
            if int(line[0]) == ityp+1:
                atom_type_list.append(tuple((line[1].strip(),float(line[2]))))
            current_line += 1
        
        # read each atom coordinates
        atom_list = []
        for iat in range(nat):
            line = [float(c) for c in lines[current_line].split()]
            ityp = int(line[1])
            if (ityp > 0 and ityp < ntyp+1):
                line[0] = atom_type_list[ityp-1][0] # string with element name
                line[1] = atom_type_list[ityp-1][1] # element mass in amu_ry
                # Convert atomic positions (in cartesian) from alat to Angstrom:
                line[2:] = [pos*celldm[0]*bohr_to_ang for pos in line[2:]]
            atom_list.append(tuple(line))
            current_line += 1
        
        parsed_data['atom_list'] = atom_list
    
        # read lrigid (flag for dielectric constant and effective charges
        has_done_electric_field = (lines[current_line].split()[0] == 'T')
        parsed_data['has_done_electric_field'] = has_done_electric_field
        current_line += 1
    
        if has_done_electric_field:
            # read dielectric tensor
            dielectric_tensor = tuple(tuple(float(c) for c in l.split())
                         for l in lines[current_line:current_line+3])
            current_line += 3
            effective_charges_eu = []
            for iat in range(nat):
                current_line += 1
                effective_charges_eu.append(tuple(tuple(float(c) for c in l.split())
                         for l in lines[current_line:current_line+3]))
                current_line += 3
                
            parsed_data['dielectric_tensor'] = dielectric_tensor
            parsed_data['effective_charges_eu'] = effective_charges_eu
            
        # read q-points mesh
        qpoints_mesh = tuple(int(c) for c in lines[current_line].split())
        current_line += 1
        parsed_data['qpoints_mesh'] = qpoints_mesh

        force_constants = ()
        if also_force_constants:
            # read force_constants
            force_constants = numpy.zeros(qpoints_mesh+(3,3,nat,nat),dtype=float)
            for j1 in range(3):
                for j2 in range(3):
                    for na1 in range(nat):
                        for na2 in range(nat):
                            
                            indices = tuple([int(c) for c in lines[current_line].split()])
                            current_line += 1
                            if (j1+1, j2+1, na1+1, na2+1) != indices:
                                raise ValueError("Wrong indices in force constants")
                            
                            for m3 in range(qpoints_mesh[2]):
                                for m2 in range(qpoints_mesh[1]):
                                    for m1 in range(qpoints_mesh[0]):
                            
                                        line = lines[current_line].split()
                                        indices = tuple(int(c) for c in line[:3])
                            
                                        if (m1+1, m2+1, m3+1) != indices:
                                            raise ValueError("Wrong supercell "
                                                    "indices in force constants")
                
                                        force_constants[m1,m2,m3,j1,j2,na1,na2] = float(line[3])
                                        current_line += 1

    except (IndexError, ValueError) as e:
        raise ValueError(e.message+"\nForce constants file could not be parsed "
                         "(incorrect file format)")
        
    return parsed_data, force_constants, warnings
    
        
