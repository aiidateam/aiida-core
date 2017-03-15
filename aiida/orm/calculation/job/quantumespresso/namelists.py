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
Plugin to create a Quantum Espresso input file for a generic post-processing
(or similar) code that only requires a few namelists (plus possibly some text
afterwards).
"""
import os

from aiida.orm.calculation.job import JobCalculation
from aiida.common.exceptions import InputValidationError
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.utils import classproperty
from aiida.orm.calculation.job.quantumespresso import (
    _lowercase_dict, _uppercase_dict, get_input_data_text)
from aiida.orm.data.parameter import ParameterData 
from aiida.orm.data.remote import RemoteData 
from aiida.orm.data.folder import FolderData 
from aiida.orm.data.singlefile import SinglefileData
from aiida.common.datastructures import CodeInfo
    

class NamelistsCalculation(JobCalculation):   
    """
    Generic plugin to manage simple post-processing tools of the
    Quantum ESPRESSO distribution (http://www.quantum-espresso.org/)
    that accept as input a Fortran-style namelist.
    """
    def _init_internal_params(self):
        super(NamelistsCalculation, self)._init_internal_params()
                
        # Default name of the subfolder inside 'parent_folder'
        # from which you want to copy the files, in case
        # the parent_folder is of type FolderData
        self._INPUT_SUBFOLDER = "./out/"
        # Default name of the subfolder inside 'parent_folder'
        # from which you want to copy the files, in case
        # the parent_folder is of type RemoteData,
        # unless the user specified a SETTINGS->parent_calc_out_subfolder
        # value
        self._default_parent_output_folder = './out/'
        # Default name of the subfolder that you want to create
        # in the output and in which you want to place the files
        # taken from parent_folder/INPUT_SUBFOLDER, in case
        # the parent_folder is of type RemoteData or FolderData
        self._OUTPUT_SUBFOLDER = './out/'
        self._PREFIX = 'aiida'
        self._INPUT_FILE_NAME = 'aiida.in'
        self._OUTPUT_FILE_NAME = 'aiida.out'
        self._internal_retrieve_list = []
        self._default_namelists = ['INPUTPP']
        self._blocked_keywords = [] # a list of tuples with key and value fixed
        self._parent_folder_type = (RemoteData, FolderData, SinglefileData)
        self._default_parser = None
        self._retrieve_singlefile_list = []

        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'aiida.in'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'

    @classproperty
    def _use_methods(cls):
        """
        Additional use_* methods for the namelists class.
        """
        retdict = JobCalculation._use_methods
        retdict.update({
            "settings": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'settings',
               'docstring': "Use an additional node for special settings",
               },
            "parameters": {
               'valid_types': ParameterData,
               'additional_parameter': None,
               'linkname': 'parameters',
               'docstring': ("Use a node that specifies the input parameters "
                             "for the namelists"),
               },
            "parent_folder": {
               'valid_types': (RemoteData, FolderData, SinglefileData),
               'additional_parameter': None,
               'linkname': 'parent_calc_folder',
               'docstring': ("Use a remote folder as parent folder (for "
                             "restarts and similar"),
               },
            })
        return retdict

    def _get_following_text(self, inputdict, settings):
        """
        By default, no text follows the namelists section.
        This function should consume the content of inputdict (if it requires
        a different node) or the keys inside settings, using the 'pop' method,
        so that inputdict and settings should remain empty at the end of 
        _prepare_for_submission, if all flags/nodes were recognized
        """
        return ""
    
    def _prepare_for_submission(self,tempfolder, inputdict):        
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.
        
        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """
        local_copy_list = []
        remote_copy_list = []

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this calculation")
        
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")
        
        # Settings can be undefined, and defaults to an empty dictionary
        settings = inputdict.pop(self.get_linkname('settings'),None)
        if settings is None:
            settings_dict = {}
        else:
            if not isinstance(settings,  ParameterData):
                raise InputValidationError("settings, if specified, must be of "
                                           "type ParameterData")
            # Settings converted to uppercase
            settings_dict = _uppercase_dict(settings.get_dict(),
                                            dict_name='settings')

        parent_calc_folder = inputdict.pop(self.get_linkname('parent_folder'),None)
        
        if parent_calc_folder is not None:
            if not isinstance(parent_calc_folder, self._parent_folder_type):
                if not isinstance(self._parent_folder_type, tuple):
                    possible_types = [self._parent_folder_type.__name__]
                else:
                    possible_types = [t.__name__ for t in self._parent_folder_type]
                raise InputValidationError("parent_calc_folder, if specified,"
                    "must be of type {}".format(
                        " or ".join(possible_types)))

        following_text = self._get_following_text(inputdict, settings)

        # Here, there should be no more parameters...
        if inputdict:
            raise InputValidationError("The following input data nodes are "
                "unrecognized: {}".format(inputdict.keys()))

        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################

        # I put the first-level keys as uppercase (i.e., namelist and card names)
        # and the second-level keys as lowercase
        # (deeper levels are unchanged)
        input_params = _uppercase_dict(parameters.get_dict(),
                                       dict_name='parameters')
        input_params = {k: _lowercase_dict(v, dict_name=k) 
                        for k, v in input_params.iteritems()}
        
        # set default values. NOTE: this is different from PW/CP
        for blocked in self._blocked_keywords:
            namelist = blocked[0].upper()
            key = blocked[1].lower()
            value = blocked[2]
            
            if namelist in input_params:
                if key in input_params[namelist]:
                    raise InputValidationError(
                        "You cannot specify explicitly the '{}' key in the '{}' "
                        "namelist.".format(key, namelist))
                    
            # set to a default
            if not input_params[namelist]:
                input_params[namelist] = {}
            input_params[namelist][key] = value
        
        # =================== NAMELISTS AND CARDS ========================
        try:
            namelists_toprint = settings_dict.pop('NAMELISTS')
            if not isinstance(namelists_toprint, list):
                raise InputValidationError(
                    "The 'NAMELISTS' value, if specified in the settings input "
                    "node, must be a list of strings")
        except KeyError: # list of namelists not specified; do automatic detection
            namelists_toprint = self._default_namelists
        
        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)

        with open(input_filename,'w') as infile:
            for namelist_name in namelists_toprint:
                infile.write("&{0}\n".format(namelist_name))
                # namelist content; set to {} if not present, so that we leave an 
                # empty namelist
                namelist = input_params.pop(namelist_name,{})
                for k, v in sorted(namelist.iteritems()):
                    infile.write(get_input_data_text(k,v))
                infile.write("/\n")

            # Write remaning text now, if any
            infile.write(following_text)

        # Check for specified namelists that are not expected
        if input_params:
            raise InputValidationError(
                "The following namelists are specified in input_params, but are "
                "not valid namelists for the current type of calculation: "
                "{}".format(",".join(input_params.keys())))
        
        # copy remote output dir, if specified
        if parent_calc_folder is not None:
            if isinstance(parent_calc_folder,RemoteData):
                parent_calc_out_subfolder = settings_dict.pop('PARENT_CALC_OUT_SUBFOLDER',
                                              self._INPUT_SUBFOLDER)
                remote_copy_list.append(
                         (parent_calc_folder.get_computer().uuid,
                          os.path.join(parent_calc_folder.get_remote_path(),
                                       parent_calc_out_subfolder),
                          self._OUTPUT_SUBFOLDER))
            elif isinstance(parent_calc_folder,FolderData):
                local_copy_list.append(
                    (parent_calc_folder.get_abs_path(self._INPUT_SUBFOLDER),
                        self._OUTPUT_SUBFOLDER)
                    )
            elif isinstance(parent_calc_folder,SinglefileData):
                filename =parent_calc_folder.get_file_abs_path() 
                local_copy_list.append(
                    (filename, os.path.basename(filename))
                 )
                
        calcinfo = CalcInfo()
        
        calcinfo.uuid = self.uuid
        # Empty command line by default
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list
        
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings_dict.pop('CMDLINE', [])
        codeinfo.stdin_name = self._INPUT_FILE_NAME
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]
        
        # Retrieve by default the output file and the xml file
        calcinfo.retrieve_list = []        
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        settings_retrieve_list = settings_dict.pop('ADDITIONAL_RETRIEVE_LIST', [])
        calcinfo.retrieve_list += settings_retrieve_list
        calcinfo.retrieve_list += self._internal_retrieve_list
        
        calcinfo.retrieve_singlefile_list = self._retrieve_singlefile_list

        codeinfo = CodeInfo()
        codeinfo.stdin_name = self._INPUT_FILE_NAME
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        if settings_dict:
            try:
                Parserclass = self.get_parserclass()
                parser = Parserclass(self)
                parser_opts = parser.get_parser_settings_key()
                settings_dict.pop(parser_opts)
            except (KeyError,AttributeError): # the key parser_opts isn't inside the dictionary, or it is set to None
                raise InputValidationError("The following keys have been found in "
                  "the settings input node, but were not understood: {}".format(
                  ",".join(settings_dict.keys())))
        
        return calcinfo


