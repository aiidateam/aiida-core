# -*- coding: utf-8 -*-

from aiida.orm import JobCalculation
from aiida.orm.data.parameter import ParameterData 
from aiida.common.utils import classproperty
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo
import json

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class SumCalculation(JobCalculation):
    """
    A generic plugin for calculations based on the ASE calculators.
    
    Requirement: the node should be able to import ase
    """
    
    def _init_internal_params(self):
        super(SumCalculation, self)._init_internal_params()
        
        self._INPUT_FILE_NAME = 'in.json'
        self._OUTPUT_FILE_NAME = 'out.json'
        self._default_parser = 'sum'
        
    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the namelists class.
        """
        retdict = JobCalculation._use_methods
        retdict.update({
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': ("Use a node that specifies the input parameters "
                             "for the namelists"),
               },
            })
        return retdict
    
    def _prepare_for_submission(self,tempfolder, inputdict):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this "
                                       "calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type "
                                       "ParameterData")
        if inputdict:
            raise ValidationError("Cannot add other nodes beside parameters")
        
        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################
        
        input_json = parameters.get_dict() 
        
        # write all the input to a file
        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)
        with open(input_filename,'w') as infile:
            json.dump(input_json,infile)
        
        # ============================ calcinfo ================================
        
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.cmdline_params = [self._INPUT_FILE_NAME,self._OUTPUT_FILE_NAME]
        calcinfo.stdout_name = []
        calcinfo.retrieve_list = [self._OUTPUT_FILE_NAME]
        
        return calcinfo
        
