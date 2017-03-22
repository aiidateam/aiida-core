# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.matdyn import MatdynCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser
from aiida.common.datastructures import calc_states
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError
from aiida.common.exceptions import UniquenessError
from aiida.parsers.plugins.quantumespresso.constants import invcm_to_THz
from aiida.orm.data.array.bands import BandsData
from aiida.orm.data.array.kpoints import KpointsData

class MatdynParser(Parser):
    """
    This class is the implementation of the Parser class for Matdyn.
    """
    _outbands_name = 'output_phonon_bands'
    
    def __init__(self,calculation):
        """
        Initialize the instance of MatdynParser
        """
        # check for valid input
        if not isinstance(calculation,MatdynCalculation):
            raise QEOutputParsingError("Input calc must be a MatdynCalculation")
        
        self._calc = calculation
        
        super(MatdynParser, self).__init__(calculation)
            
    def parse_with_retrieved(self,retrieved):
        """
        Parses the datafolder, stores results.
        This parser for this simple code does simply store in the DB a node
        representing the file of phonon frequencies
        """
        from aiida.common.exceptions import InvalidOperation

        # suppose at the start that the job is successful
        successful = True
        new_nodes_list = []

        # check if I'm not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )
        
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
            self.logger.error("Standard output not found")
            return successful,()
        
        # check that the file has finished (i.e. JOB DONE is inside the file)
        filpath = out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME)
        with open(filpath,'r') as fil:
            lines = fil.read()
        if "JOB DONE" not in lines:
            successful = False
            self.logger.error("Computation did not finish properly")
        
        # check that the phonon frequencies file is present
        try:
            # define phonon frequencies file name
            phonon_file = out_folder.get_abs_path(self._calc._PHONON_FREQUENCIES_NAME)
        except OSError:
            successful = False
            self.logger.error("File with phonon frequencies not found")
            return successful,new_nodes_list
        
        # extract the kpoints from the input data and create the kpointsdata for bands
        kpointsdata = self._calc.inp.kpoints
        try:
            kpoints = kpointsdata.get_kpoints()
            kpointsdata_for_bands = kpointsdata.copy()
        except AttributeError:
            kpoints = kpointsdata.get_kpoints_mesh(print_list=True)
            kpointsdata_for_bands = KpointsData()
            kpointsdata_for_bands.set_kpoints(kpoints)
        # find the number of kpoints
        num_kpoints = kpoints.shape[0]
        
        # call the raw parsing function
        parsed_data = parse_raw_matdyn_phonon_file(phonon_file)
        
        # extract number of kpoints read from the file (and take out from output
        # dictionary)
        try:
            this_num_kpoints = parsed_data.pop('num_kpoints')
        except KeyError:
            successful = False
            self.logger.error("Wrong number of kpoints")
            # warning message already in parsed_data
            return successful,new_nodes_list
        
        # check that the number of kpoints from the file is the same as the one
        # in the input kpoints
        if num_kpoints != this_num_kpoints:
            successful = False
            self.logger.error("Number of kpoints different in input and in "
                               "phonon frequencies file")
        
        # extract phonon bands (and take out from output dictionary)
        phonon_bands = parsed_data.pop('phonon_bands')
        
        # save phonon branches into BandsData
        output_bands = BandsData()
        output_bands.set_kpointsdata(kpointsdata_for_bands)
        output_bands.set_bands(phonon_bands,units='THz')
        
        # convert the dictionary into an AiiDA object (here only warnings remain)
        output_params = ParameterData(dict=parsed_data)
        
        for message in parsed_data['warnings']:
            self.logger.error(message)
        
        # prepare the list of output nodes to be returned
        new_nodes_list = [ (self.get_linkname_outparams(),output_params),
                           (self.get_linkname_outbands(),output_bands) ]
            
        return successful,new_nodes_list

    def get_linkname_outbands(self):
        """
        Returns the name of the link to the output_bands
        """
        return self._outbands_name

def parse_raw_matdyn_phonon_file(phonon_file):
    """
    Parses the phonon frequencies file
    :param phonon_file: phonon frequencies file from the matdyn calculation
    
    :return dict parsed_data: keys:
         * warnings: parser warnings raised
         * num_kpoints: number of kpoints read from the file
         * phonon_bands: BandsData object with the bands for each kpoint
    """
    import numpy
    import re
    
    parsed_data = {}
    parsed_data['warnings'] = []

    # read file
    with open(phonon_file,'r') as f:
        lines = f.read()
    
    # extract numbere of bands and kpoints
    try:
        num_bands = int( lines.split("=")[1].split(',')[0] )
        num_kpoints = int( lines.split("=")[2].split('/')[0] )
        parsed_data['num_kpoints'] = num_kpoints
    except (ValueError,IndexError):
        parsed_data['warnings'].append("Number of bands or kpoints unreadable "
                                       "in phonon frequencies file")
        return parsed_data

    # initialize array of frequencies
    freq_matrix = numpy.zeros((num_kpoints,num_bands))

    split_data = lines.split()
    # discard the header of the file
    raw_data = split_data[split_data.index('/')+1:]
    
    # try to improve matdyn deficiencies
    corrected_data = []
    for b in raw_data:
        try:
            corrected_data.append(float(b))
        except ValueError:
            # case in which there are two frequencies attached like -1204.1234-1020.536
            if "-" in b:
                c = re.split('(-)',b)
                d = [ i for i in c if i is not '' ]
                for i in range(0,len(d),2): # d should have an even number of elements
                    corrected_data.append( float( d[i]+d[i+1] ) )
            else:
                # I don't know what to do
                parsed_data["warnings"].append("Bad formatting of frequencies")
                return parsed_data
#        if b=='1162.9773': break
    
    counter = 3
    for i in range(num_kpoints):
        for j in range(num_bands):
            try:
                freq_matrix[i,j] = corrected_data[counter]*invcm_to_THz # from cm-1 to THz
            except ValueError:
                parsed_data["warnings"].append("Error while parsing the "
                                               "frequencies") 
            except IndexError:
                parsed_data["warnings"].append("Error while parsing the "
                                               "frequencies, dimension exceeded")
                return parsed_data
            counter += 1
        counter += 3 # move past the kpoint coordinates
    
            
    parsed_data['phonon_bands'] = freq_matrix
   
    return parsed_data
