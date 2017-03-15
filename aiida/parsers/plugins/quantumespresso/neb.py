# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.neb import NebCalculation
from aiida.parsers.plugins.quantumespresso.raw_parser_pw import (
                            parse_pw_xml_output,parse_pw_text_output,QEOutputParsingError)
from aiida.parsers.plugins.quantumespresso.raw_parser_neb import parse_raw_output_neb
from aiida.orm.data.parameter import ParameterData
from aiida.parsers.parser import Parser#, ParserParamManager
from aiida.common.datastructures import calc_states
from aiida.orm.data.array.bands import KpointsData
from aiida.parsers.plugins.quantumespresso import convert_qe2aiida_structure


class NebParser(Parser):
    """
    This class is the implementation of the Parser class for Neb.
    """

    _setting_key = 'parser_options'

    def __init__(self,calc):
        """
        Initialize the instance of NebParser
        """
        # check for valid input
        if not isinstance(calc,NebCalculation):
            raise QEOutputParsingError("Input calc must be a NebCalculation")
        
        super(NebParser, self).__init__(calc)
        
        
    def parse_with_retrieved(self, retrieved):
        """
        Parses the calculation-output datafolder, and stores
        results.

        :param retrieved: a dictionary of retrieved nodes, where the keys
            are the link names of retrieved nodes, and the values are the
            nodes.
        """
        from aiida.common.exceptions import InvalidOperation
        from aiida.orm.data.array.trajectory import TrajectoryData
        from aiida.orm.data.array import ArrayData
        import os 
        import numpy
        import copy
        
        successful = True
        
        # check if I'm not to overwrite anything
        #state = self._calc.get_state()
        #if state != calc_states.PARSING:
        #    raise InvalidOperation("Calculation not in {} state"
        #                           .format(calc_states.PARSING) )

        # look for eventual flags of the parser
        try:
            parser_opts = self._calc.inp.settings.get_dict()[self.get_parser_settings_key()]
        except (AttributeError,KeyError):
            parser_opts = {}
        
        # load the pw input dictionary            
        pw_input_dict = self._calc.inp.pw_parameters.get_dict()
       
        # load the pw input dictionary                
        neb_input_dict = self._calc.inp.neb_parameters.get_dict()
        
        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            self.logger.error("No retrieved folder found")
            successful = False
            return successful, ()
        
        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()
        # at least the stdout should exist
        if not self._calc._OUTPUT_FILE_NAME in list_of_files:
            self.logger.error("Standard output not found")
            successful = False
            return successful,()
        
        out_file = os.path.join( out_folder.get_abs_path('.'), 
                                 self._calc._OUTPUT_FILE_NAME )
                
        # First parse the Neb output
        neb_out_dict,iteration_data,raw_successful = parse_raw_output_neb(out_file,neb_input_dict)
        
        # if calculation was not considered failed already, use the new value
        successful = raw_successful if successful else successful
            
        # Retrieve the number of images
        try:
            num_images = neb_input_dict['num_of_images']
        except KeyError:
            try: 
                num_images = neb_out_dict['num_of_images']
            except KeyError:
                self.logger.error("Impossible to understand the number of images")
                successful = False
                return successful, ()
        
        # Now parse the information from the single pw calculations for the different images
        image_data = {}
        positions = []
        cells = []
        for i in range(num_images):
            # look for xml and parse
            xml_file = os.path.join(out_folder.get_abs_path('.'),
                                    self._calc._PREFIX +'_{}'.format(i+1),self._calc._PREFIX+'.save',
                                    self._calc._DATAFILE_XML_BASENAME)
            try:
                with open(xml_file,'r') as f:                
                    xml_lines = f.read() # Note: read() and not readlines()
            except IOError:
                self.logger.error("No xml file found for image {} at {}".format(i+1,xml_file))
                successful = False
                return successful, ()
            xml_data,structure_dict,bands_data = parse_pw_xml_output(xml_lines)
            
            # convert the dictionary obtained from parsing the xml to an AiiDA StructureData
            structure_data = convert_qe2aiida_structure(structure_dict)
            
            # look for pw output and parse it
            pw_out_file = os.path.join(out_folder.get_abs_path('.'),
                                    self._calc._PREFIX +'_{}'.format(i+1),'PW.out')
            try:
                with open(pw_out_file,'r') as f:
                    pw_out_lines = f.read() # Note: read() and not readlines()
            except IOError:
                self.logger.error("No pw output file found for image {}".format(i+1))
                successful = False
                return successful, ()
            
            pw_out_data,trajectory_data,critical_messages = parse_pw_text_output(pw_out_lines,xml_data,
                                                                                 structure_dict,pw_input_dict)
            
            # I add in the out_data all the last elements of trajectory_data values.
            # Safe for some large arrays, that I will likely never query.
            skip_keys = ['forces','atomic_magnetic_moments','atomic_charges',
                         'lattice_vectors_relax','atomic_positions_relax',
                         'atomic_species_name']
            tmp_trajectory_data = copy.copy(trajectory_data)
            for x in tmp_trajectory_data.iteritems():
                if x[0] in skip_keys:
                    continue
                pw_out_data[x[0]] = x[1][-1]
                if len(x[1])==1: # delete eventual keys that are not arrays 
                    trajectory_data.pop(x[0])
            # As the k points are an array that is rather large, and again it's not something I'm going to parse likely
            # since it's an info mainly contained in the input file, I move it to the trajectory data
            for key in ['k_points','k_points_weights']:
                try:
                    trajectory_data[key] = xml_data.pop(key)
                except KeyError:
                    pass
    
            key = 'pw_output_image_{}'.format(i+1)
            image_data[key] = dict(pw_out_data.items() + xml_data.items())
            
            positions.append([site.position for site in structure_data.sites])
            cells.append(structure_data.cell)
            
            # If a warning was already present in the NEB, add also PW warnings to the neb output data, 
            # avoiding repetitions.
            if neb_out_dict['warnings']:
                for warning in pw_out_data['warnings']:
                    if warning not in neb_out_dict['warnings']:
                        neb_out_dict['warnings'].append(warning) 
                
        # Symbols can be obtained simply from the last image 
        symbols = [ str(site.kind_name) for site in structure_data.sites]
        
        new_nodes_list = []
        
        # convert the dictionary into an AiiDA object
        output_params = ParameterData(dict=dict(neb_out_dict.items()+image_data.items()))
        
        # return it to the execmanager
        new_nodes_list.append((self.get_linkname_outparams(),output_params))
        
        # convert data on structure of images into a TrajectoryData
        traj = TrajectoryData()
        traj.set_trajectory(stepids = numpy.arange(1,num_images+1),
                            cells = numpy.array(cells),
                            symbols = numpy.array(symbols),
                            positions = numpy.array(positions),
                            )
        
        # return it to the execmanager
        new_nodes_list.append((self.get_linkname_outtrajectory(),traj))
        
        if parser_opts.get('all_iterations',False):
            if iteration_data:           
                from aiida.orm.data.array import ArrayData
            
                arraydata = ArrayData()
                for x in iteration_data.iteritems():
                    arraydata.set_array(x[0],numpy.array(x[1]))               
                new_nodes_list.append((self.get_linkname_iterationarray(),arraydata))
        
        # Load the original and interpolated energy profile along the minimum-energy path (mep)
        try:
            mep_file = os.path.join( out_folder.get_abs_path('.'), 
                                                self._calc._PREFIX + '.dat' )
            mep = numpy.loadtxt(mep_file)
        except Exception:
            self.logger.warning("Impossible to find the file with image energies "
                                "versus reaction coordinate.")
            mep = numpy.array([[]])
            
        try:
            interp_mep_file = os.path.join( out_folder.get_abs_path('.'), 
                                                self._calc._PREFIX + '.int' )
            interp_mep = numpy.loadtxt(interp_mep_file)
        except Exception:
            self.logger.warning("Impossible to find the file with the interpolation "
                                "of image energies versus reaction coordinate.")
            interp_mep = numpy.array([[]])
        # Create an ArrayData with the energy profiles
        mep_arraydata = ArrayData()
        mep_arraydata.set_array('mep', mep)
        mep_arraydata.set_array('interpolated_mep', interp_mep)
        new_nodes_list.append((self.get_linkname_meparray(),mep_arraydata))
        
        return successful,new_nodes_list
    
    def get_parser_settings_key(self):
        """
        Return the name of the key to be used in the calculation settings, that
        contains the dictionary with the parser_options 
        """
        return 'parser_options'
    
    def get_linkname_iterationarray(self):
        """
        Returns the name of the link to the ArrayData
        containing data from neb iterations
        """
        return 'iteration_array'
    
    def get_linkname_outtrajectory(self):
        """
        Returns the name of the link to the output_trajectory.
        """
        return 'output_trajectory'
    
    def get_linkname_meparray(self):
        """
        Returns the name of the link to the ArrayData
        with the information on the minimum energy path 
        (energy versus reaction coordinate, original and interpolated)
        """
        return 'output_mep'
