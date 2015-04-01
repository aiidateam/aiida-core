# -*- coding: utf-8 -*-
from aiida.parsers.parser import Parser
from aiida.orm.calculation.job.nwchem.nwcpymatgen import NwcpymatgenCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import calc_states

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class NwcpymatgenParser(Parser):
    """
    Parser for the output of NWChem, using pymatgen.
    """
    def __init__(self,calc):
        """
        Initialize the instance of NwcpymatgenParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(NwcpymatgenParser, self).__init__(calc)

    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,NwcpymatgenCalculation):
            raise ParsingError("Input calc must be a NwcpymatgenCalculation")

    def parse_with_retrieved(self,retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """       
        from aiida.common.exceptions import InvalidOperation
        import os

        output_path = None
        error_path  = None
        try:
            output_path, error_path = self._fetch_output_files(retrieved)
        except InvalidOperation:
            raise
        except IOError as e:
            self.logger.error(e.message)
            return False, ()

        if output_path is None and error_path is None:
            self.logger.error("No output files found")
            return False, ()

        return True, self._get_output_nodes(output_path, error_path)

    def _fetch_output_files(self, retrieved):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.
        
        :param retrieved: A dictionary of retrieved nodes, as obtained from the
          parser.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        # check in order not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )

        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            raise IOError("No retrieved folder found")        

        list_of_files = out_folder.get_folder_list()

        output_path = None
        error_path  = None

        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files:
            output_path = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_OUTPUT_FILE )
        if self._calc._DEFAULT_ERROR_FILE in list_of_files:
            error_path  = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_ERROR_FILE )

        return output_path, error_path

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from pymatgen.io.nwchemio import NwOutput

        ret_dict = []
        nwo = NwOutput(output_path)
        for out in nwo.data:
            out.pop('molecules') # TODO: implement extraction of
                                 # Structure- and TrajectoryData
            ret_dict.append(('output',ParameterData(dict=out)))
        ret_dict.append(('job_info',ParameterData(dict=nwo.job_info)))
        
        return ret_dict
