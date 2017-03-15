# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.cp import CpCalculation
from aiida.parsers.plugins.quantumespresso.raw_parser_cp import (
    QEOutputParsingError, parse_cp_traj_stanzas, parse_cp_raw_output)
from aiida.parsers.plugins.quantumespresso.constants import (bohr_to_ang,
                                                             timeau_to_sec, hartree_to_ev)
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser
from aiida.common.datastructures import calc_states
from aiida.orm.data.array.trajectory import TrajectoryData
import numpy



class CpParser(Parser):
    """
    This class is the implementation of the Parser class for Cp.
    """

    def __init__(self, calc):
        """
        Initialize the instance of CpParser
        
        :param calculation: calculation object.
        """
        # check for valid input
        if not isinstance(calc, CpCalculation):
            raise QEOutputParsingError("Input calc must be a CpCalculation")

        super(CpParser, self).__init__(calc)

    def parse_with_retrieved(self, retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        from aiida.common.exceptions import InvalidOperation
        import os, numpy
        from distutils.version import LooseVersion
        
        successful = True

        # check if I'm not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING))

        # get the input structure
        input_structure = self._calc.inp.structure

        # load the input dictionary
        # TODO: pass this input_dict to the parser. It might need it.            
        input_dict = self._calc.inp.parameters.get_dict()

        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            self.logger.error("No retrieved folder found")
            return False, ()

        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()
        # at least the stdout should exist
        if not self._calc._OUTPUT_FILE_NAME in list_of_files:
            successful = False
            new_nodes_tuple = ()
            self.logger.error("Standard output not found")
            return successful, new_nodes_tuple

        # if there is something more, I note it down, so to call the raw parser
        # with the right options
        # look for xml
        out_file = out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME)

        xml_file = None
        if self._calc._DATAFILE_XML_BASENAME in list_of_files:
            xml_file = out_folder.get_abs_path(self._calc._DATAFILE_XML_BASENAME)

        xml_counter_file = None
        if self._calc._FILE_XML_PRINT_COUNTER in list_of_files:
            xml_counter_file = out_folder.get_abs_path(
                self._calc._FILE_XML_PRINT_COUNTER)

        parsing_args = [out_file, xml_file, xml_counter_file]

        # call the raw parsing function
        out_dict, raw_successful = parse_cp_raw_output(*parsing_args)

        successful = True if raw_successful else False

        # parse the trajectory. Units in Angstrom, picoseconds and eV.
        # append everthing in the temporary dictionary raw_trajectory
        expected_configs = None
        raw_trajectory = {}
        evp_keys = ['electronic_kinetic_energy', 'cell_temperature', 'ionic_temperature',
                    'scf_total_energy', 'enthalpy', 'enthalpy_plus_kinetic',
                    'energy_constant_motion', 'volume', 'pressure']
        pos_vel_keys = ['cells', 'positions', 'times', 'velocities']
        # set a default null values

        # Now prepare the reordering, as filex in the xml are  ordered
        reordering = self._generate_sites_ordering(out_dict['species'],
                                                   out_dict['atoms'])

        # =============== POSITIONS trajectory ============================
        try:
            with open(out_folder.get_abs_path(
                    '{}.pos'.format(self._calc._PREFIX))) as posfile:
                pos_data = [l.split() for l in posfile]
                # POSITIONS stored in angstrom
            traj_data = parse_cp_traj_stanzas(num_elements=out_dict['number_of_atoms'],
                                              splitlines=pos_data,
                                              prepend_name='positions_traj',
                                              rescale=bohr_to_ang)

            # here initialize the dictionary. If the parsing of positions fails, though, I don't have anything
            # out of the CP dynamics. Therefore, the calculation status is set to FAILED.
            raw_trajectory['positions_ordered'] = self._get_reordered_array(traj_data['positions_traj_data'],
                                                                            reordering)
            raw_trajectory['times'] = numpy.array(traj_data['positions_traj_times'])
        except IOError:
            out_dict['warnings'].append("Unable to open the POS file... skipping.")
            successful = False
        except Exception as e:
            out_dict['warnings'].append("Error parsing POS file ({}). Skipping file."
                                        .format(e.message))
            successful = False

        # =============== CELL trajectory ============================
        try:
            with open(os.path.join(out_folder.get_abs_path('.'),
                                   '{}.cel'.format(self._calc._PREFIX))) as celfile:
                cel_data = [l.split() for l in celfile]
            traj_data = parse_cp_traj_stanzas(num_elements=3,
                                              splitlines=cel_data,
                                              prepend_name='cell_traj',
                                              rescale=bohr_to_ang)
            raw_trajectory['cells'] = numpy.array(traj_data['cell_traj_data'])
        except IOError:
            out_dict['warnings'].append("Unable to open the CEL file... skipping.")
        except Exception as e:
            out_dict['warnings'].append("Error parsing CEL file ({}). Skipping file."
                                        .format(e.message))

        # =============== VELOCITIES trajectory ============================
        try:
            with open(os.path.join(out_folder.get_abs_path('.'),
                                   '{}.vel'.format(self._calc._PREFIX))) as velfile:
                vel_data = [l.split() for l in velfile]
            traj_data = parse_cp_traj_stanzas(num_elements=out_dict['number_of_atoms'],
                                              splitlines=vel_data,
                                              prepend_name='velocities_traj',
                                              rescale=bohr_to_ang / timeau_to_sec * 10 ** 12)  # velocities in ang/ps,
            raw_trajectory['velocities_ordered'] = self._get_reordered_array(traj_data['velocities_traj_data'],
                                                                             reordering)
        except IOError:
            out_dict['warnings'].append("Unable to open the VEL file... skipping.")
        except Exception as e:
            out_dict['warnings'].append("Error parsing VEL file ({}). Skipping file."
                                        .format(e.message))

        # =============== EVP trajectory ============================
        try:
            matrix = numpy.genfromtxt(os.path.join(out_folder.get_abs_path('.'),
                                                   '{}.evp'.format(self._calc._PREFIX)))
            # there might be a different format if the matrix has one row only
            try:
                matrix.shape[1]
            except IndexError:
                matrix = numpy.array(numpy.matrix(matrix))
            
            if LooseVersion(out_dict['creator_version']) > LooseVersion("5.1"):
                # Between version 5.1 and 5.1.1, someone decided to change
                # the .evp output format, without any way to know that this 
                # happened... SVN commit 11158.
                # I here use the version number to parse, plus some
                # heuristics to check that I'm doing the right thing
                #print "New version"
                raw_trajectory['steps'] = numpy.array(matrix[:,0],dtype=int)
                raw_trajectory['evp_times']                 = matrix[:,1]                    # TPS, ps
                raw_trajectory['electronic_kinetic_energy'] = matrix[:,2] * hartree_to_ev    # EKINC, eV
                raw_trajectory['cell_temperature']          = matrix[:,3]                    # TEMPH, K
                raw_trajectory['ionic_temperature']         = matrix[:,4]                    # TEMPP, K
                raw_trajectory['scf_total_energy']          = matrix[:,5] * hartree_to_ev    # ETOT, eV
                raw_trajectory['enthalpy']                  = matrix[:,6] * hartree_to_ev    # ENTHAL, eV
                raw_trajectory['enthalpy_plus_kinetic']     = matrix[:,7] * hartree_to_ev    # ECONS, eV
                raw_trajectory['energy_constant_motion']    = matrix[:,8] * hartree_to_ev    # ECONT, eV
                raw_trajectory['volume']                    = matrix[:,9] * (bohr_to_ang**3) # volume, angstrom^3
                raw_trajectory['pressure']                  = matrix[:,10]                    # out_press, GPa
            else:
                #print "Old version"    
                raw_trajectory['steps'] = numpy.array(matrix[:,0],dtype=int)
                raw_trajectory['electronic_kinetic_energy'] = matrix[:,1] * hartree_to_ev    # EKINC, eV
                raw_trajectory['cell_temperature']          = matrix[:,2]                    # TEMPH, K
                raw_trajectory['ionic_temperature']         = matrix[:,3]                    # TEMPP, K
                raw_trajectory['scf_total_energy']          = matrix[:,4] * hartree_to_ev    # ETOT, eV
                raw_trajectory['enthalpy']                  = matrix[:,5] * hartree_to_ev    # ENTHAL, eV
                raw_trajectory['enthalpy_plus_kinetic']     = matrix[:,6] * hartree_to_ev    # ECONS, eV
                raw_trajectory['energy_constant_motion']    = matrix[:,7] * hartree_to_ev    # ECONT, eV
                raw_trajectory['volume']                    = matrix[:,8] * (bohr_to_ang**3) # volume, angstrom^3
                raw_trajectory['pressure']                  = matrix[:,9]                    # out_press, GPa
                raw_trajectory['evp_times']                  = matrix[:,10]                    # TPS, ps

            # Huristics to understand if it's correct.
            # A better heuristics could also try to fix possible issues
            # (in new versions of QE, it's possible to recompile it with
            # the __OLD_FORMAT flag to get back the old version format...)
            # but I won't do it, as there may be also other columns swapped.
            # Better to stop and ask the user to check what's going on.
            max_time_difference = abs(
                numpy.array(raw_trajectory['times']) - 
                numpy.array(raw_trajectory['evp_times'])).max()
            if max_time_difference > 1.e-4: # It is typically ~1.e-7 due to roundoff errors
                # If there is a large discrepancy, I set successful = False,
                # it means there is something very weird going on...
                out_dict['warnings'].append("Error parsing EVP file ({}). Skipping file."
                                            .format(e.message))
                successful = False

                # In this case, remove all what has been parsed to avoid users
                # using the wrong data
                for k in evp_keys:
                    try:
                        del raw_trajectory[k]
                    except KeyError:
                        # If for some reason a key is not there, ignore
                        pass
            # Delete evp_times in any case, it's a duplicate of 'times'
            del raw_trajectory['evp_times']
            
        except Exception as e:
            out_dict['warnings'].append("Error parsing EVP file ({}). Skipping file.".format(e.message))
        except IOError:
            out_dict['warnings'].append("Unable to open the EVP file... skipping.")

        # get the symbols from the input        
        # TODO: I should have kinds in TrajectoryData
        raw_trajectory['symbols'] = numpy.array([str(i.kind_name) for i in input_structure.sites])

        traj = TrajectoryData()
        traj.set_trajectory(stepids=raw_trajectory['steps'],
                            cells=raw_trajectory['cells'],
                            symbols=raw_trajectory['symbols'],
                            positions=raw_trajectory['positions_ordered'],
                            times=raw_trajectory['times'],
                            velocities=raw_trajectory['velocities_ordered'],
        )

        for this_name in evp_keys:
            try:
                traj.set_array(this_name,raw_trajectory[this_name])
            except KeyError:
                # Some columns may have not been parsed, skip
                pass
        new_nodes_list = [(self.get_linkname_trajectory(),traj)]
        
        # Remove big dictionaries that would be redundant
        # For atoms and cell, there is a small possibility that nothing is parsed
        # but then probably nothing moved.
        try:
            del out_dict['atoms']
        except KeyError:
            pass
        try:
            del out_dict['cell']
        except KeyError:
            pass
        try:
            del out_dict['ions_positions_stau']
        except KeyError:
            pass
        try:
            del out_dict['ions_positions_svel']
        except KeyError:
            pass
        try:
            del out_dict['ions_positions_taui']
        except KeyError:
            pass
        # This should not be needed
        try:
            del out_dict['atoms_index_list']
        except KeyError:
            pass
        # This should be already in the input
        try:
            del out_dict['atoms_if_pos_list']
        except KeyError:
            pass
        # 
        try:
            del out_dict['ions_positions_force']
        except KeyError:
            pass

        # convert the dictionary into an AiiDA object
        output_params = ParameterData(dict=out_dict)
        # save it into db
        new_nodes_list.append((self.get_linkname_outparams(), output_params))

        return successful, new_nodes_list

    def get_linkname_trajectory(self):
        """
        Returns the name of the link to the output_structure (None if not present)
        """
        return 'output_trajectory'

    def _generate_sites_ordering(self, raw_species, raw_atoms):
        """
        take the positions of xml and from file.pos of the LAST step and compare them 
        """
        # Examples in the comments are for species [Ba, O, Ti]
        # and atoms [Ba, Ti, O, O, O]

        # Dictionary to associate the species name to the idx
        # Example: {'Ba': 1, 'O': 2, 'Ti': 3}
        species_dict = {name: idx for idx, name in zip(raw_species['index'],
                                                       raw_species['type'])}
        # List of the indices of the specie associated to each atom,
        # in the order specified in input
        # Example: (1,3,2,2,2)
        atoms_species_idx = [species_dict[a[0]] for a in raw_atoms]
        # I also attach the current position; important to convert to a list
        # Otherwise the iterator can be looped on only once!
        # Example: ((0,1),(1,3),(2,2),(3,2),(4,2))
        ref_atom_list = list(enumerate(atoms_species_idx))
        new_order_tmp = []
        # I reorder the atoms, first by specie, then in their order
        # This is the order used in output by CP!!
        # Example: ((0,1),(2,2),(3,2),(4,2),(1,3))
        for specie_idx in sorted(raw_species['index']):
            for elem in ref_atom_list:
                if elem[1] == specie_idx:
                    new_order_tmp.append(elem)
        # This is the new order that is printed in CP:
        # e.g. reordering[2] is the index of the atom, in the input
        # list of atoms, that is printed in position 2 (0-based, so the
        # third atom) in the CP output files.
        # Example: [0,2,3,4,1]
        reordering = [_[0] for _ in new_order_tmp]
        # I now need the inverse reordering, to put back in place 
        # from the output ordering to the input one!
        # Example: [0,4,1,2,3]
        # Because in the final list (Ba, O, O, O, Ti)
        # the first atom Ba in the input is atom 0 in the CP output (the first),
        # the second atom Ti in the input is atom 4 (the fifth) in the CP output,
        # and so on
        sorted_indexed_reordering = sorted([(_[1], _[0]) for _ in
                                            enumerate(reordering)])
        reordering_inverse = [_[1] for _ in sorted_indexed_reordering]
        return reordering_inverse

    def _get_reordered_list(self, origlist, reordering):
        """
        Given a list to reorder, a list of integer positions with the new
        order, return the reordered list.
        """
        return [origlist[e] for e in reordering]

    def _get_reordered_array(self, input, reordering):
        return numpy.array([self._get_reordered_list(i, reordering) for i in input])
