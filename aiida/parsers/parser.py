# -*- coding: utf-8 -*-
"""
This module implements a generic output plugin, that is general enough
to allow the reading of the outputs of a calculation.
"""
from aiida.common.datastructures import calc_states

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class Parser(object):
    """
    Base class for a parser object.
    
    Receives a Calculation object. This should be in the PARSING state. 
    Raises ValueError otherwise 
    Looks for the attached parser_opts or input_settings nodes attached to the calculation.
    Get the child Folderdata, parse it and store the parsed data.
    """
    _linkname_outparams = 'output_parameters'

    def __init__(self,calc):
        """
        Init
        """
        self._calc = calc
        
        
    def parse_from_data(self,data):
        """
        Receives in input a datanode.
        To be implemented.
        Will be used by the user for eventual re-parsing of out-data,
        for example with another or updated version of the parser
        """
        raise NotImplementedError
            
    def parse_from_calc(self):
        """
        Parses the datafolder, stores results.
        Used by the Execmanager.
        """
        raise NotImplementedError

        
    @classmethod
    def get_linkname_outparams(self):
        """
        The name of the link used for the output parameters
        """
        return self._linkname_outparams
    

    def get_result_keys(self):
        """
        Return an iterator of list of strings of valid result keys,
        that can be then passed to the get_result() method.
        
        :note: the function returns an empty list if no output params node
          can be found (either because the parser did not create it, or because
          the calculation has not been parsed yet).
        
        :raise: UniquenessError if more than one output node with the name
          self._get_linkname_outparams() is found. 
        """
        from aiida.orm.data.parameter import ParameterData
                
        out_parameters = self._calc.get_outputs(type=ParameterData,also_labels=True)
        out_parameterdata = [ i[1] for i in out_parameters if i[0]==self.get_linkname_outparams() ]
        
        if not out_parameterdata:
            return iter([])
                
        if len(out_parameterdata) > 1:
            from aiida.common.exceptions import UniquenessError
            raise UniquenessError("Output ParameterData should be found once, "
                                  "found it instead {} times"
                                  .format(len(out_parameterdata)) )
        
        out_parameterdata = out_parameterdata[0]
        
        return out_parameterdata.keys

    def get_result(self,key_name):
        """
        Access the parameters of the output.
        The following method will should work for a generic parser,
        provided it has to query only one ParameterData object.
        """
        from aiida.orm.data.parameter import ParameterData
        
        out_parameters = self._calc.get_outputs(type=ParameterData,also_labels=True)
        out_parameterdata = [ i[1] for i in out_parameters if i[0]==self.get_linkname_outparams() ]
        
        if not out_parameterdata:
            from aiida.common.exceptions import NotExistent
            raise NotExistent("No output ParameterData found")
        
        if len(out_parameterdata) > 1:
            from aiida.common.exceptions import UniquenessError
            raise UniquenessError("Output ParameterData should be found once, "
                                  "found it instead {} times"
                                  .format(len(out_parameterdata)) )
        
        out_parameterdata = out_parameterdata[0]
        
        try:
            value = out_parameterdata.get_attr(key_name)
        except KeyError:
            from aiida.common.exceptions import ContentNotExistent
            raise ContentNotExistent("Key energy not found in results")
        
        #TODO: eventually, here insert further operations
        # (ex: key_name = energy_float_rydberg could return only the last element of a list,
        # and convert in the right units)
        
        return value

