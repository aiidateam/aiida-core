# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.nodes.data.dict import Dict 
from aiida.common.lang import classproperty
from aiida.common.exceptions import InputValidationError
from aiida.common.exceptions import ValidationError
from aiida.common.datastructures import CalcInfo, CodeInfo
import json

class SumCalculation(JobCalculation):
    """
    A generic plugin for adding two numbers.
    """
    
    def _init_internal_params(self):
        super(SumCalculation, self)._init_internal_params()
        
        self._DEFAULT_INPUT_FILE = 'in.json'
        self._DEFAULT_OUTPUT_FILE = 'out.json'
        self._default_parser = 'sum'
        
    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the namelists class.
        """
        retdict = JobCalculation._use_methods
        retdict.update({
            "parameters": {
               'valid_types': Dict,
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
        :param inputdict: a dictionary with the input nodes in a format
                           {label1: node1, ...} (with the Code!)
        """
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this "
                                       "calculation")
        if not isinstance(parameters, Dict):
            raise InputValidationError("parameters is not of type "
                                       "Dict")
        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this "
                                       "calculation")
        if inputdict:
            raise ValidationError("Cannot add other nodes beside parameters")
        
        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################
        
        input_json = parameters.get_dict() 
        
        # write all the input to a file
        input_filename = tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE)
        with open(input_filename, 'w') as infile:
            json.dump(input_json, infile)
        
        # ============================ calcinfo ================================
        
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = [self._DEFAULT_OUTPUT_FILE]
        
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = [self._DEFAULT_INPUT_FILE,self._DEFAULT_OUTPUT_FILE]
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]
        
        return calcinfo

