# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.parsers.plugins.quantumespresso.basic_raw_parser_pw import (
    parse_raw_output, QEOutputParsingError)
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser  # , ParserParamManager
from aiida.parsers.plugins.quantumespresso import convert_qe2aiida_structure
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import UniquenessError
from aiida.orm.data.array import ArrayData
from aiida.orm.data.array.kpoints import KpointsData

# TODO: I don't like the generic class always returning a name for the link to the output structure



class BasicpwParser(Parser):
    """
    This class is the implementation of the Parser class for PWscf.
    """

    _setting_key = 'parser_options'

    def __init__(self, calc):
        """
        Initialize the instance of PwParser
        """
        # check for valid input
        if not isinstance(calc, PwCalculation):
            raise QEOutputParsingError("Input calc must be a PwCalculation")

        super(BasicpwParser, self).__init__(calc)

    def parse_with_retrieved(self, retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        from aiida.common.exceptions import InvalidOperation
        import os
        import glob

        successful = True

        # check if I'm not to overwrite anything
        #state = self._calc.get_state()
        #if state != calc_states.PARSING:
        #    raise InvalidOperation("Calculation not in {} state"
        #                           .format(calc_states.PARSING) )

        # retrieve the input parameter
        calc_input = self._calc.inp.parameters

        # look for eventual flags of the parser
        try:
            parser_opts = self._calc.inp.settings.get_dict()[self.get_parser_settings_key()]
        except (AttributeError, KeyError):
            parser_opts = {}

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
            self.logger.error("Standard output not found")
            successful = False
            return successful, ()
        # if there is something more, I note it down, so to call the raw parser
        # with the right options
        # look for xml
        has_xml = False
        if self._calc._DATAFILE_XML_BASENAME in list_of_files:
            has_xml = True
        # look for bands
        has_bands = False
        if glob.glob(os.path.join(out_folder.get_abs_path('.'),
                                  'K*[0-9]')):
            # Note: assuming format of kpoints subfolder is K*[0-9]
            has_bands = True
            # TODO: maybe it can be more general than bands only?
        out_file = os.path.join(out_folder.get_abs_path('.'),
                                self._calc._OUTPUT_FILE_NAME)
        xml_file = os.path.join(out_folder.get_abs_path('.'),
                                self._calc._DATAFILE_XML_BASENAME)
        dir_with_bands = out_folder.get_abs_path('.')

        # call the raw parsing function
        parsing_args = [out_file, input_dict, parser_opts]
        if has_xml:
            parsing_args.append(xml_file)
        if has_bands:
            if not has_xml:
                self.logger.warning("Cannot parse bands if xml file not "
                                    "found")
            else:
                parsing_args.append(dir_with_bands)

        out_dict, trajectory_data, structure_data, raw_successful = parse_raw_output(*parsing_args)

        # if calculation was not considered failed already, use the new value
        successful = raw_successful if successful else successful

        new_nodes_list = []

        # I eventually save the new structure. structure_data is unnecessary after this
        in_struc = self._calc.get_inputs_dict()['structure']
        type_calc = input_dict['CONTROL']['calculation']
        struc = in_struc
        if type_calc in ['relax', 'vc-relax', 'md', 'vc-md']:
            if 'cell' in structure_data.keys():
                struc = convert_qe2aiida_structure(structure_data, input_structure=in_struc)
                new_nodes_list.append((self.get_linkname_outstructure(), struc))

        k_points_list = trajectory_data.pop('k_points', None)
        k_points_weights_list = trajectory_data.pop('k_points_weights', None)

        if k_points_list is not None:

            # build the kpoints object
            if out_dict['k_points_units'] not in ['2 pi / Angstrom']:
                raise QEOutputParsingError('Error in kpoints units (should be cartesian)')
            # converting bands into a BandsData object (including the kpoints)

            kpoints_from_output = KpointsData()
            kpoints_from_output.set_cell_from_structure(struc)
            kpoints_from_output.set_kpoints(k_points_list, cartesian=True,
                                            weights=k_points_weights_list)
            kpoints_from_input = self._calc.inp.kpoints
            try:
                kpoints_from_input.get_kpoints()
            except AttributeError:
                new_nodes_list += [(self.get_linkname_out_kpoints(), kpoints_from_output)]

        # convert the dictionary into an AiiDA object
        output_params = ParameterData(dict=out_dict)
        # return it to the execmanager
        new_nodes_list.append((self.get_linkname_outparams(), output_params))

        if trajectory_data:
            import numpy
            from aiida.orm.data.array.trajectory import TrajectoryData
            from aiida.orm.data.array import ArrayData

            try:
                positions = numpy.array(trajectory_data.pop('atomic_positions_relax'))
                try:
                    cells = numpy.array(trajectory_data.pop('lattice_vectors_relax'))
                    # if KeyError, the MD was at fixed cell
                except KeyError:
                    cells = numpy.array([in_struc.cell] * len(positions))

                symbols = numpy.array([str(i.kind_name) for i in in_struc.sites])
                stepids = numpy.arange(len(positions))  # a growing integer per step
                # I will insert time parsing when they fix their issues about time 
                # printing (logic is broken if restart is on)

                traj = TrajectoryData()
                traj.set_trajectory(stepids=stepids,
                                    cells=cells,
                                    symbols=symbols,
                                    positions=positions,
                )
                for x in trajectory_data.iteritems():
                    traj.set_array(x[0], numpy.array(x[1]))
                # return it to the execmanager
                new_nodes_list.append((self.get_linkname_outtrajectory(), traj))

            except KeyError:  # forces in scf calculation (when outputed)
                arraydata = ArrayData()
                for x in trajectory_data.iteritems():
                    arraydata.set_array(x[0], numpy.array(x[1]))
                # return it to the execmanager
                new_nodes_list.append((self.get_linkname_outarray(), arraydata))

        return successful, new_nodes_list

    def get_parser_settings_key(self):
        """
        Return the name of the key to be used in the calculation settings, that
        contains the dictionary with the parser_options 
        """
        return 'parser_options'

    def get_linkname_outstructure(self):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_structure'

    def get_linkname_outtrajectory(self):
        """
        Returns the name of the link to the output_trajectory.
        Node exists in case of calculation='md', 'vc-md', 'relax', 'vc-relax'
        """
        return 'output_trajectory'

    def get_linkname_outarray(self):
        """
        Returns the name of the link to the output_array
        Node may exist in case of calculation='scf'
        """
        return 'output_array'

    def get_linkname_out_kpoints(self):
        """
        Returns the name of the link to the output_kpoints
        Node exists if cell has changed and no bands are stored.
        """
        return 'output_kpoints'
